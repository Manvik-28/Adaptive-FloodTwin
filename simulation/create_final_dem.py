import rasterio
import numpy as np

INPUT = "data/dem/fine_dem.tif"
OUTPUT = "data/processed/final_dem.tif"

with rasterio.open(INPUT) as src:
    data = src.read(1)

    profile = src.profile.copy()
    profile.update(
        driver="GTiff",
        dtype="float32",
        compress="deflate",
        nodata=-9999.0
    )

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(data.astype("float32"), 1)

valid = data[data != -9999.0]

print("FINAL DEM CREATED")
print("OUTPUT:", OUTPUT)
print("CRS:", profile["crs"])
print("SIZE:", profile["width"], "x", profile["height"])
print("RESOLUTION:", profile["transform"].a, "m")
print("MIN:", float(valid.min()))
print("MAX:", float(valid.max()))
print("MEAN:", float(valid.mean()))
print("NODATA CELLS:", int(np.sum(data == -9999.0)))
