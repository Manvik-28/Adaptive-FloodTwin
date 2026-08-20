import numpy as np
import rasterio


FLOW_DIRECTION_PATH = (
    "data/processed/final_flow_direction.tif"
)

FILLED_DEM_PATH = (
    "data/processed/final_hydrology_filled.tif"
)

DEM_PATH = (
    "data/processed/final_dem.tif"
)

DRAINAGE_PATH = (
    "data/processed/final_drainage_candidate.tif"
)


# ------------------------------------------------------------
# Prototype drainage assumption
#
# No measured hydraulic capacity is currently available.
#
# Therefore:
#
# 1 drainage candidate cell =
# 10 m3 removable during one event.
# ------------------------------------------------------------

DRAINAGE_CAPACITY_M3 = 10.0


# D8 direction codes
D8 = {
    1: (0, 1),
    2: (1, 1),
    4: (1, 0),
    8: (1, -1),
    16: (0, -1),
    32: (-1, -1),
    64: (-1, 0),
    128: (-1, 1),
}


def route_water(
    runoff_volume_m3,
    rainfall_mm,
    duration_minutes
):

    with rasterio.open(DEM_PATH) as src:

        dem = src.read(1).astype(np.float32)
        profile = src.profile.copy()

    with rasterio.open(FILLED_DEM_PATH) as src:

        filled_dem = src.read(1).astype(np.float32)

    with rasterio.open(FLOW_DIRECTION_PATH) as src:

        flow_direction = src.read(1).astype(np.int16)

    with rasterio.open(DRAINAGE_PATH) as src:

        drainage = src.read(1).astype(np.uint8)

    rows, cols = dem.shape

    # --------------------------------------------------------
    # Validate raster dimensions
    # --------------------------------------------------------

    if runoff_volume_m3.shape != dem.shape:
        raise ValueError(
            "Runoff raster shape does not match DEM: "
            f"{runoff_volume_m3.shape} vs {dem.shape}"
        )

    if (
        filled_dem.shape != dem.shape
        or flow_direction.shape != dem.shape
        or drainage.shape != dem.shape
    ):
        raise ValueError(
            "DEM, filled DEM, flow direction and drainage "
            "rasters must have identical dimensions."
        )

    # --------------------------------------------------------
    # Cell area
    # --------------------------------------------------------

    cell_area = (
        abs(profile["transform"].a)
        *
        abs(profile["transform"].e)
    )

    # --------------------------------------------------------
    # Depression storage
    #
    # This represents how much water can remain in a cell
    # before flowing onward.
    # --------------------------------------------------------

    depression_depth = np.maximum(
        filled_dem - dem,
        0.0
    )

    storage_capacity_m3 = (
        depression_depth
        * cell_area
    )

    # --------------------------------------------------------
    # Build D8 downstream graph
    # --------------------------------------------------------

    downstream = np.full(
        (rows, cols, 2),
        -1,
        dtype=np.int32
    )

    indegree = np.zeros(
        (rows, cols),
        dtype=np.int32
    )

    for r in range(rows):

        for c in range(cols):

            code = int(
                flow_direction[r, c]
            )

            if code not in D8:
                continue

            dr, dc = D8[code]

            nr = r + dr
            nc = c + dc

            if (
                nr < 0
                or nr >= rows
                or nc < 0
                or nc >= cols
            ):
                continue

            downstream[r, c] = (
                nr,
                nc
            )

            indegree[nr, nc] += 1

    # --------------------------------------------------------
    # Topological order
    # --------------------------------------------------------

    queue = []

    for r in range(rows):

        for c in range(cols):

            if indegree[r, c] == 0:

                queue.append(
                    (r, c)
                )

    order = []

    head = 0

    while head < len(queue):

        r, c = queue[head]
        head += 1

        order.append(
            (r, c)
        )

        nr, nc = downstream[r, c]

        if nr < 0:
            continue

        indegree[nr, nc] -= 1

        if indegree[nr, nc] == 0:

            queue.append(
                (nr, nc)
            )

    # --------------------------------------------------------
    # Safety fallback for unexpected cycles
    # --------------------------------------------------------

    if len(order) < rows * cols:

        known = set(order)

        for r in range(rows):

            for c in range(cols):

                if (r, c) not in known:

                    order.append(
                        (r, c)
                    )

    # --------------------------------------------------------
    # Water entering each cell
    # --------------------------------------------------------

    incoming_volume = np.zeros(
        (rows, cols),
        dtype=np.float64
    )

    # --------------------------------------------------------
    # Final water stored in each cell
    # --------------------------------------------------------

    ponded_volume = np.zeros(
        (rows, cols),
        dtype=np.float64
    )

    # --------------------------------------------------------
    # Drainage removal
    # --------------------------------------------------------

    drainage_removed = np.zeros(
        (rows, cols),
        dtype=np.float64
    )

    # --------------------------------------------------------
    # D8 routing
    # --------------------------------------------------------

    for r, c in order:

        total_volume = (
            float(
                runoff_volume_m3[r, c]
            )
            +
            float(
                incoming_volume[r, c]
            )
        )

        # ----------------------------------------------------
        # Drainage removes water before ponding.
        # ----------------------------------------------------

        if drainage[r, c] > 0:

            removed = min(
                total_volume,
                DRAINAGE_CAPACITY_M3
            )

            total_volume -= removed

            drainage_removed[r, c] = removed

        # ----------------------------------------------------
        # Local depression storage
        # ----------------------------------------------------

        stored = min(
            total_volume,
            storage_capacity_m3[r, c]
        )

        ponded_volume[r, c] = stored

        excess_volume = (
            total_volume - stored
        )

        # ----------------------------------------------------
        # Send excess downstream.
        # ----------------------------------------------------

        nr, nc = downstream[r, c]

        if nr >= 0:

            incoming_volume[nr, nc] += (
                excess_volume
            )

        # If there is no downstream cell,
        # water leaves the modeled boundary.

    # --------------------------------------------------------
    # Convert volume to depth
    # --------------------------------------------------------

    flood_depth_m = (
        ponded_volume / cell_area
    ).astype(np.float32)

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_runoff_m3 = float(
        runoff_volume_m3.sum()
    )

    total_ponded_m3 = float(
        ponded_volume.sum()
    )

    total_drainage_removed_m3 = float(
        drainage_removed.sum()
    )

    return {
        "flood_depth_m":
            flood_depth_m,

        "ponded_volume_m3":
            ponded_volume,

        "drainage_removed_m3":
            drainage_removed,

        "total_runoff_m3":
            total_runoff_m3,

        "total_ponded_m3":
            total_ponded_m3,

        "total_drainage_removed_m3":
            total_drainage_removed_m3,

        "depression_depth_m":
            depression_depth.astype(
                np.float32
            ),
    }