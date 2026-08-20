import numpy as np

from terrain import load_terrain
from runoff import calculate_runoff


# GRASS r.watershed direction encoding
# 1 = NE
# 2 = N
# 3 = NW
# 4 = W
# 5 = SW
# 6 = S
# 7 = SE
# 8 = E

DIRECTION_OFFSETS = {
    1: (-1, 1),    # NE
    2: (-1, 0),    # N
    3: (-1, -1),   # NW
    4: (0, -1),    # W
    5: (1, -1),    # SW
    6: (1, 0),     # S
    7: (1, 1),     # SE
    8: (0, 1),     # E
}


def route_water(rainfall_mm, runoff_coefficient=0.7):

    terrain = load_terrain()

    dem = terrain["dem"]
    flow_direction = terrain["flow_direction"]

    runoff_volume = calculate_runoff(
        rainfall_mm,
        runoff_coefficient
    )

    rows, cols = dem.shape

    accumulated_water = np.zeros(
        (rows, cols),
        dtype=np.float64
    )

    valid = np.isfinite(dem)

    # --------------------------------------------------
    # Add locally generated runoff
    # --------------------------------------------------

    accumulated_water[valid] = runoff_volume[valid]

    # --------------------------------------------------
    # Route water according to D8 directions
    # --------------------------------------------------

    # Process cells from high elevation to low elevation.
    # This ensures upstream cells are processed first.
    elevation_order = np.argsort(
        np.where(valid, dem, np.inf).ravel()
    )

    # We need highest elevation first
    elevation_order = elevation_order[::-1]

    for index in elevation_order:

        row, col = np.unravel_index(
            index,
            dem.shape
        )

        if not valid[row, col]:
            continue

        direction = int(flow_direction[row, col])

        # Negative directions indicate water leaving
        # the DEM region.
        if direction < 0:
            direction = abs(direction)

        if direction not in DIRECTION_OFFSETS:
            continue

        dr, dc = DIRECTION_OFFSETS[direction]

        next_row = row + dr
        next_col = col + dc

        # If water leaves the raster, ignore it.
        if (
            next_row < 0
            or next_row >= rows
            or next_col < 0
            or next_col >= cols
        ):
            continue

        if not valid[next_row, next_col]:
            continue

        # Send accumulated water downstream
        accumulated_water[next_row, next_col] += (
            accumulated_water[row, col]
        )

    accumulated_water[~valid] = np.nan

    return accumulated_water


if __name__ == "__main__":

    result = route_water(100)

    print("Water routing completed")

    print("Shape:", result.shape)

    print(
        "Minimum accumulated water:",
        np.nanmin(result),
        "m³"
    )

    print(
        "Maximum accumulated water:",
        np.nanmax(result),
        "m³"
    )

    print(
        "Mean accumulated water:",
        np.nanmean(result),
        "m³"
    )