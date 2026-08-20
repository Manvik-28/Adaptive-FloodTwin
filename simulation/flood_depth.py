import numpy as np
import rasterio

from terrain import load_terrain
from routing import route_water


def calculate_flood_depth(
    rainfall_mm,
    runoff_coefficient=0.7,
    drainage_capacity_mm=50.0
):
    """
    Estimate flood depth from rainfall.

    This is a prototype storage model.

    rainfall_mm:
        Total rainfall in mm.

    runoff_coefficient:
        Fraction of rainfall converted to runoff.

    drainage_capacity_mm:
        Prototype amount of water that can be removed
        by the drainage system during the event.
    """

    terrain = load_terrain()

    dem = terrain["dem"]
    flow_accumulation = terrain["flow_accumulation"]

    # --------------------------------------------------
    # 1. Route runoff
    # --------------------------------------------------

    routed_water = route_water(
        rainfall_mm,
        runoff_coefficient
    )

    # --------------------------------------------------
    # 2. Identify where water concentrates
    # --------------------------------------------------

    accumulation = flow_accumulation.astype(float)

    valid = np.isfinite(dem)

    accumulation[~valid] = np.nan
    routed_water[~valid] = np.nan

    # --------------------------------------------------
    # 3. Normalize flow accumulation
    #
    # This gives a concentration factor from 0 to 1.
    # We use the 99th percentile instead of the absolute
    # maximum so one extreme cell doesn't dominate.
    # --------------------------------------------------

    accumulation_limit = np.nanpercentile(
        accumulation,
        99
    )

    concentration = accumulation / accumulation_limit

    concentration = np.clip(
        concentration,
        0.0,
        1.0
    )

    # --------------------------------------------------
    # 4. Estimate locally stored water
    #
    # We don't treat all routed water as floodwater.
    # Only a fraction related to water concentration
    # contributes to local storage.
    # --------------------------------------------------

    rainfall_excess_mm = max(
        rainfall_mm - drainage_capacity_mm,
        0.0
    )

    rainfall_excess_m = rainfall_excess_mm / 1000.0

    # Base storage + concentration-dependent storage
    storage_depth = rainfall_excess_m * (
        0.2 + 0.8 * concentration
    )

    # --------------------------------------------------
    # 5. Use slope to reduce standing water on steep
    # terrain.
    # --------------------------------------------------

    slope = terrain["slope"]

    slope_factor = 1.0 / (
        1.0 + slope / 10.0
    )

    flood_depth = storage_depth * slope_factor

    flood_depth[~valid] = np.nan

    return flood_depth


def save_flood_depth(
    flood_depth,
    output_path="data/processed/flood_depth.tif"
):
    """
    Save flood depth as a GeoTIFF using the DEM
    spatial reference.
    """

    terrain = load_terrain()
    profile = terrain["profile"].copy()

    profile.update(
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="lzw"
    )

    output = np.where(
        np.isfinite(flood_depth),
        flood_depth,
        -9999.0
    ).astype(np.float32)

    with rasterio.open(
        output_path,
        "w",
        **profile
    ) as dst:

        dst.write(output, 1)

    print("Flood depth raster saved:")
    print(output_path)


if __name__ == "__main__":

    for rainfall in [50, 100, 150, 200]:

        result = calculate_flood_depth(
            rainfall_mm=rainfall
        )

        print(
            f"{rainfall} mm -> "
            f"max={np.nanmax(result):.4f} m, "
            f"mean={np.nanmean(result):.4f} m, "
            f">5cm={(result > 0.05).sum()}, "
            f">10cm={(result > 0.10).sum()}"
        )
    save_flood_depth(result)