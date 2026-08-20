import rasterio
import numpy as np


FLOW_ACC_PATH = "data/processed/flow_accumulation_hydro.tif"
OUTPUT_PATH = "data/processed/drainage_candidate.tif"

# Start conservative.
# 100 accumulated cells means approximately:
# 100 × 30 m × 30 m ≈ 90,000 m² contributing area.
ACCUMULATION_THRESHOLD = 100


with rasterio.open(FLOW_ACC_PATH) as src:

    accumulation = src.read(1, masked=True)

    profile = src.profile.copy()

    data = accumulation.filled(0).astype(np.uint8)

    # Cells with sufficient upstream contribution
    drainage = (
        accumulation >= ACCUMULATION_THRESHOLD
    ).astype(np.uint8)

    profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw"
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(drainage, 1)


print("Drainage candidate raster created")
print("Threshold:", ACCUMULATION_THRESHOLD)
print("Drainage cells:", int(drainage.sum()))
print("Output:", OUTPUT_PATH)