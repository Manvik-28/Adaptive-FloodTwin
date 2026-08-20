import math
import heapq
import os
import sys
import numpy as np
import geopandas as gpd
import rasterio
from pyproj import Transformer


ROADS_PATH = "data/campus/griet_roads.gpkg"
FLOOD_DIR = "data/processed"


def distance(a, b):
    """Distance between two latitude/longitude points in meters."""

    lat1, lon1 = a
    lat2, lon2 = b

    lat = math.radians((lat1 + lat2) / 2.0)

    dx = (
        (lon2 - lon1)
        * 111320.0
        * math.cos(lat)
    )

    dy = (
        (lat2 - lat1)
        * 111320.0
    )

    return math.sqrt(dx * dx + dy * dy)


def get_flood_raster_path(rainfall_mm, duration_minutes):
    rainfall_value = int(round(float(rainfall_mm)))
    duration_value = int(round(float(duration_minutes)))

    return os.path.join(
        FLOOD_DIR,
        f"final_flood_depth_{rainfall_value}mm_"
        f"{duration_value}min.tif"
    )


def load_roads():

    roads = gpd.read_file(ROADS_PATH)

    graph = {}

    for _, row in roads.iterrows():

        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            continue

        # Handle LineString
        if geometry.geom_type == "LineString":

            lines = [geometry]

        # Handle MultiLineString
        elif geometry.geom_type == "MultiLineString":

            lines = list(geometry.geoms)

        else:
            continue

        for line in lines:

            coords = list(line.coords)

            if len(coords) < 2:
                continue

            points = [
                (lat, lon)
                for lon, lat in coords
            ]

            for i in range(len(points) - 1):

                a = points[i]
                b = points[i + 1]

                d = distance(a, b)

                if d <= 0:
                    continue

                graph.setdefault(a, [])
                graph.setdefault(b, [])

                graph[a].append((b, d))
                graph[b].append((a, d))

    return graph


def nearest_node(graph, point):

    return min(
        graph.keys(),
        key=lambda node: distance(node, point)
    )


def get_local_flood_depth(
    lat,
    lon,
    flood_array,
    src,
    transformer,
    radius=1
):
    """
    Return the median flood depth in a local raster neighborhood.

    A 3x3 median (radius=1) suppresses isolated single-pixel
    spikes while preserving broader flooded regions.
    """

    try:

        x, y = transformer.transform(
            lon,
            lat
        )

        row, col = src.index(
            x,
            y
        )

        if (
            row < 0
            or row >= src.height
            or col < 0
            or col >= src.width
        ):
            return 0.0

        r0 = max(0, row - radius)
        r1 = min(src.height, row + radius + 1)

        c0 = max(0, col - radius)
        c1 = min(src.width, col + radius + 1)

        window = flood_array[
            r0:r1,
            c0:c1
        ].astype(float)

        if src.nodata is not None:

            window = window[
                window != src.nodata
            ]

        window = window[
            np.isfinite(window)
        ]

        if window.size == 0:
            return 0.0

        window = np.maximum(
            window,
            0.0
        )

        return float(
            np.median(window)
        )

    except Exception:

        return 0.0

def edge_flood_depth(
    a,
    b,
    flood_array,
    src,
    transformer
):
    """
    Sample several points along the road segment.

    Each point uses a local 3x3 median flood depth to avoid
    treating an isolated raster pixel as a completely flooded road.

    The maximum smoothed sample is used for routing.
    """

    samples = 7

    sampled_depths = []

    for i in range(samples + 1):

        t = i / samples

        lat = (
            a[0]
            + (b[0] - a[0]) * t
        )

        lon = (
            a[1]
            + (b[1] - a[1]) * t
        )

        depth = get_local_flood_depth(
            lat,
            lon,
            flood_array,
            src,
            transformer,
            radius=1
        )

        sampled_depths.append(
            depth
        )

    if not sampled_depths:
        return 0.0

    return max(
        sampled_depths
    )

def find_route(
    rainfall_mm=150.0,
    duration_minutes=30.0,
    start=(17.5202, 78.3658),
    destination=(17.5214, 78.3672)
):

    rainfall_mm = float(rainfall_mm)
    duration_minutes = float(duration_minutes)

    flood_path = get_flood_raster_path(
        rainfall_mm,
        duration_minutes
    )

    # ---------------------------------------------------------
    # Road network
    # ---------------------------------------------------------

    if not os.path.exists(ROADS_PATH):

        return {
            "rainfall_mm": rainfall_mm,
            "duration_minutes": duration_minutes,
            "start": "Main Gate",
            "destination": "Assembly Point",
            "route": [],
            "estimated_time_minutes": 0,
            "route_distance_m": 0,
            "risk": "BLOCKED",
            "max_flood_depth_m": 0,
            "route_coordinates": [],
            "message": f"Road network not found: {ROADS_PATH}"
        }

    graph = load_roads()

    if not graph:

        return {
            "rainfall_mm": rainfall_mm,
            "duration_minutes": duration_minutes,
            "start": "Main Gate",
            "destination": "Assembly Point",
            "route": [],
            "estimated_time_minutes": 0,
            "route_distance_m": 0,
            "risk": "BLOCKED",
            "max_flood_depth_m": 0,
            "route_coordinates": [],
            "message": "No road network was loaded."
        }

    # ---------------------------------------------------------
    # Matching duration-specific flood raster
    # ---------------------------------------------------------

    if not os.path.exists(flood_path):

        return {
            "rainfall_mm": rainfall_mm,
            "duration_minutes": duration_minutes,
            "start": "Main Gate",
            "destination": "Assembly Point",
            "route": [],
            "estimated_time_minutes": 0,
            "route_distance_m": 0,
            "risk": "BLOCKED",
            "max_flood_depth_m": 0,
            "route_coordinates": [],
            "message": (
                "Matching flood simulation does not exist: "
                f"{flood_path}"
            )
        }

    # ---------------------------------------------------------
    # Nearest road nodes
    # ---------------------------------------------------------

    start_node = nearest_node(
        graph,
        start
    )

    destination_node = nearest_node(
        graph,
        destination
    )

    # ---------------------------------------------------------
    # Open flood raster
    # ---------------------------------------------------------

    with rasterio.open(flood_path) as flood:

        transformer = Transformer.from_crs(
            "EPSG:4326",
            flood.crs,
            always_xy=True
        )

        flood_array = flood.read(1)

        # -----------------------------------------------------
        # Dijkstra
        # -----------------------------------------------------

        queue = [(0.0, start_node)]

        distances = {
            start_node: 0.0
        }

        previous = {}
        edge_depths = {}

        while queue:

            current_cost, current = heapq.heappop(queue)

            if current == destination_node:
                break

            if current_cost > distances.get(
                current,
                float("inf")
            ):
                continue

            for neighbour, road_distance in graph[current]:

                depth = edge_flood_depth(
                    current,
                    neighbour,
                    flood_array,
                    flood,
                    transformer
                )

                # -------------------------------------------------
                # Flood safety thresholds
                # -------------------------------------------------

                if depth > 0.30:
                    continue

                if depth > 0.20:
                    flood_penalty = 10.0

                elif depth > 0.10:
                    flood_penalty = 3.0

                else:
                    flood_penalty = 1.0

                new_cost = (
                    current_cost
                    + road_distance * flood_penalty
                )

                if new_cost < distances.get(
                    neighbour,
                    float("inf")
                ):

                    distances[neighbour] = new_cost

                    previous[neighbour] = current

                    edge_depths[
                        (current, neighbour)
                    ] = depth

                    heapq.heappush(
                        queue,
                        (new_cost, neighbour)
                    )

        # ---------------------------------------------------------
        # No route
        # ---------------------------------------------------------

        if destination_node not in distances:

            return {
                "rainfall_mm": rainfall_mm,
                "duration_minutes": duration_minutes,
                "start": "Main Gate",
                "destination": "Assembly Point",
                "route": [],
                "estimated_time_minutes": 0,
                "route_distance_m": 0,
                "risk": "BLOCKED",
                "max_flood_depth_m": 0,
                "route_coordinates": [],
                "message": "No safe evacuation route available."
            }

        # ---------------------------------------------------------
        # Reconstruct route
        # ---------------------------------------------------------

        path = []
        current = destination_node

        while current != start_node:

            path.append(current)

            current = previous[current]

        path.append(start_node)
        path.reverse()

        # ---------------------------------------------------------
        # Maximum route flood depth
        # ---------------------------------------------------------

        max_depth = 0.0

        for i in range(len(path) - 1):

            a = path[i]
            b = path[i + 1]

            depth = edge_depths.get(
                (a, b),
                edge_depths.get(
                    (b, a),
                    0.0
                )
            )

            max_depth = max(max_depth, depth)

        # ---------------------------------------------------------
        # Route risk
        # ---------------------------------------------------------

        if max_depth > 0.20:
            risk = "HIGH"

        elif max_depth > 0.10:
            risk = "MEDIUM"

        else:
            risk = "LOW"

        # ---------------------------------------------------------
        # Physical distance
        # ---------------------------------------------------------

        route_distance = 0.0

        for i in range(len(path) - 1):

            route_distance += distance(
                path[i],
                path[i + 1]
            )

        # ---------------------------------------------------------
        # Walking speed
        # ---------------------------------------------------------

        estimated_time = route_distance / 80.0

        return {
            "rainfall_mm": rainfall_mm,
            "duration_minutes": duration_minutes,
            "start": "Main Gate",
            "destination": "Assembly Point",

            "route": [
                f"Road Node {i + 1}"
                for i in range(len(path))
            ],

            "estimated_time_minutes": round(
                estimated_time,
                1
            ),

            "route_distance_m": round(
                route_distance,
                1
            ),

            "risk": risk,

            "max_flood_depth_m": round(
                max_depth,
                4
            ),

            "route_coordinates": path,

            "message": "Safe evacuation route found."
        }


if __name__ == "__main__":

    rainfall = (
        float(sys.argv[1])
        if len(sys.argv) > 1
        else 150.0
    )

    duration = (
        float(sys.argv[2])
        if len(sys.argv) > 2
        else 30.0
    )

    result = find_route(
        rainfall_mm=rainfall,
        duration_minutes=duration
    )

    print()
    print("FLOOD-AWARE EVACUATION")
    print("--------------------------------")

    print("Rainfall:", rainfall, "mm")
    print("Duration:", duration, "minutes")

    print("Start:", result["start"])
    print("Destination:", result["destination"])

    print("Risk:", result["risk"])

    print(
        "Max route flood depth:",
        result["max_flood_depth_m"],
        "m"
    )

    print(
        "Route distance:",
        result["route_distance_m"],
        "m"
    )

    print(
        "Estimated time:",
        result["estimated_time_minutes"],
        "minutes"
    )

    print("Message:", result["message"])

    print(
        "Route nodes:",
        len(result["route"])
    )