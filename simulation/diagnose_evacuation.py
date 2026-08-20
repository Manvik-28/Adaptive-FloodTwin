import rasterio
from pyproj import Transformer
from evacuation import (
    load_roads,
    nearest_node,
    get_flood_depth,
    edge_flood_depth,
)

FLOOD = "data/processed/final_flood_depth_150mm.tif"

graph = load_roads()

start = (17.5202, 78.3658)
destination = (17.5214, 78.3672)

start_node = nearest_node(graph, start)
destination_node = nearest_node(graph, destination)

with rasterio.open(FLOOD) as flood:

    transformer = Transformer.from_crs(
        "EPSG:4326",
        flood.crs,
        always_xy=True
    )

    flood_array = flood.read(1)

    start_depth = get_flood_depth(
        start_node[0],
        start_node[1],
        flood_array,
        flood,
        transformer
    )

    destination_depth = get_flood_depth(
        destination_node[0],
        destination_node[1],
        flood_array,
        flood,
        transformer
    )

    depths = []

    seen = set()

    for node in graph:
        for neighbour, road_distance in graph[node]:

            edge = tuple(sorted([node, neighbour]))

            if edge in seen:
                continue

            seen.add(edge)

            depth = edge_flood_depth(
                node,
                neighbour,
                flood_array,
                flood,
                transformer
            )

            depths.append(depth)

    print("GRAPH NODES:", len(graph))
    print("GRAPH EDGES:", len(seen))

    print("START NODE:", start_node)
    print("START FLOOD DEPTH:", start_depth, "m")

    print("DESTINATION NODE:", destination_node)
    print("DESTINATION FLOOD DEPTH:", destination_depth, "m")

    print("MIN ROAD DEPTH:", min(depths))
    print("MAX ROAD DEPTH:", max(depths))

    print(
        "ROADS <= 0.10m:",
        sum(d <= 0.10 for d in depths),
        "/",
        len(depths)
    )

    print(
        "ROADS 0.10-0.20m:",
        sum(0.10 < d <= 0.20 for d in depths)
    )

    print(
        "ROADS 0.20-0.30m:",
        sum(0.20 < d <= 0.30 for d in depths)
    )

    print(
        "ROADS > 0.30m:",
        sum(d > 0.30 for d in depths)
    )
