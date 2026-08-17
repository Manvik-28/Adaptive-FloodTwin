import numpy as np

from terrain import load_terrain
from rainfall import rainfall_to_runoff


def calculate_runoff(rainfall_mm, runoff_coefficient=0.7):

    terrain = load_terrain()

    dem = terrain["dem"]
    flow_accumulation = terrain["flow_accumulation"]

    runoff_mm = rainfall_to_runoff(
        rainfall_mm,
        runoff_coefficient
    )

    # Convert rainfall/runoff depth from mm to metres
    runoff_m = runoff_mm / 1000.0

    # Ignore NoData cells
    valid = np.isfinite(dem)

    # Normalize flow accumulation
    accumulation = flow_accumulation.astype(float)

    accumulation[~valid] = np.nan

    max_accumulation = np.nanmax(accumulation)

    if max_accumulation > 0:
        accumulation_factor = accumulation / max_accumulation
    else:
        accumulation_factor = np.zeros_like(accumulation)

    # Initial spatial runoff contribution
    runoff_depth = runoff_m * (
        0.5 + 0.5 * accumulation_factor
    )

    runoff_depth[~valid] = np.nan

    return runoff_depth


if __name__ == "__main__":

    result = calculate_runoff(100)

    print("Runoff raster generated")
    print("Shape:", result.shape)
    print("Minimum runoff:", np.nanmin(result))
    print("Maximum runoff:", np.nanmax(result))