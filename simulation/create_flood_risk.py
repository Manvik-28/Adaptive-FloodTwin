import rasterio
import numpy as np

INPUT = "data/processed/final_flood_depth_150mm.tif"
OUTPUT = "data/processed/final_flood_risk_150mm.tif"

with rasterio.open(INPUT) as src:
    depth = src.read(1)
    profile = src.profile

# Risk classes:
# 0 = No/Low
# 1 = Moderate
# 2 = High
# 3 = Critical

risk = np.zeros(depth.shape, dtype=np.uint8)

risk[(depth >= 0.10) & (depth < 0.30)] = 1
risk[(depth >= 0.30) & (depth < 0.50)] = 2
risk[depth >= 0.50] = 3

profile.update(
    dtype="uint8",
    nodata=0,
    compress="deflate"
)

with rasterio.open(OUTPUT, "w", **profile) as dst:
    dst.write(risk, 1)

print("RISK MAP CREATED")
print("Output:", OUTPUT)
print("Low:", int(np.sum(risk == 0)))
print("Moderate:", int(np.sum(risk == 1)))
print("High:", int(np.sum(risk == 2)))
print("Critical:", int(np.sum(risk == 3)))
