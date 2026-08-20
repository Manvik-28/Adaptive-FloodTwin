import rasterio
import numpy as np

ACC = "data/processed/final_flow_accumulation.tif"
OUT = "data/processed/final_drainage_candidate.tif"

with rasterio.open(ACC) as src:
    acc = src.read(1)
    profile = src.profile

# Candidate drainage cells.
# Start with 30 contributing cells for this 10 m prototype.
threshold = 30

drainage = (acc >= threshold).astype(np.uint8)

profile.update(
    dtype="uint8",
    nodata=0,
    compress="deflate"
)

with rasterio.open(OUT, "w", **profile) as dst:
    dst.write(drainage, 1)

print("DRAINAGE CANDIDATE CREATED")
print("OUTPUT:", OUT)
print("THRESHOLD:", threshold)
print("DRAINAGE CELLS:", int(drainage.sum()))
print("MAX ACCUMULATION:", float(acc.max()))
