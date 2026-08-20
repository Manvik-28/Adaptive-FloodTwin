import numpy as np
import rasterio

from flood_depth import calculate_flood_depth
from terrain import load_terrain


def classify_flood_risk(depth):

    risk = np.zeros(depth.shape, dtype=np.uint8)

    valid = np.isfinite(depth)

    # Risk classification based on water depth
    risk[(depth >= 0.00) & (depth < 0.05)] = 0
    risk[(depth >= 0.05) & (depth < 0.10)] = 1
    risk[(depth >= 0.10) & (depth < 0.20)] = 2
    risk[(depth >= 0.20) & (depth < 0.50)] = 3
    risk[depth >= 0.50] = 4

    risk[~valid] = 255

    return risk


def save_flood_risk(
    risk,
    output_path="data/processed/flood_risk.tif"
):

    terrain = load_terrain()

    profile = terrain["profile"].copy()

    profile.update(
        dtype="uint8",
        count=1,
        nodata=255,
        compress="lzw"
    )

    with rasterio.open(
        output_path,
        "w",
        **profile
    ) as dst:

        dst.write(risk, 1)

    print("Flood risk raster saved:")
    print(output_path)


if __name__ == "__main__":

    rainfall = 200

    depth = calculate_flood_depth(
        rainfall_mm=rainfall
    )

    risk = classify_flood_risk(depth)

    print("Flood risk calculated")
    print("Rainfall:", rainfall, "mm")

    for level in range(5):

        print(
            f"Risk {level} cells:",
            np.sum(risk == level)
        )

    save_flood_risk(risk)