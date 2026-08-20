import numpy as np
import rasterio
from pathlib import Path

DEM = "data/processed/final_dem.tif"
OUTDIR = Path("data/processed")

with rasterio.open(DEM) as src:
    dem = src.read(1).astype(np.float32)
    profile = src.profile
    nodata = src.nodata

# ---------------------------------------
# 1. Fill simple depressions
# ---------------------------------------
filled = dem.copy()

# Iteratively raise cells that are lower than all surrounding outlets.
# This is a simple terrain conditioning approach for our small prototype.
for _ in range(100):
    changed = False
    new = filled.copy()

    for r in range(1, filled.shape[0] - 1):
        for c in range(1, filled.shape[1] - 1):
            neighbors = filled[r-1:r+2, c-1:c+2].copy()
            neighbors[1, 1] = np.inf

            lowest_neighbor = np.min(neighbors)

            if filled[r, c] < lowest_neighbor:
                new[r, c] = lowest_neighbor
                changed = True

    filled = new

    if not changed:
        break

# ---------------------------------------
# 2. D8 flow direction
# ---------------------------------------
# Directions:
# 1  = E
# 2  = SE
# 4  = S
# 8  = SW
# 16 = W
# 32 = NW
# 64 = N
# 128 = NE

directions = [
    (0, 1, 1),
    (1, 1, 2),
    (1, 0, 4),
    (1, -1, 8),
    (0, -1, 16),
    (-1, -1, 32),
    (-1, 0, 64),
    (-1, 1, 128),
]

flow_dir = np.zeros_like(filled, dtype=np.int16)

for r in range(1, filled.shape[0] - 1):
    for c in range(1, filled.shape[1] - 1):

        best_drop = 0
        best_dir = 0

        for dr, dc, code in directions:
            nr = r + dr
            nc = c + dc

            drop = filled[r, c] - filled[nr, nc]

            if drop > best_drop:
                best_drop = drop
                best_dir = code

        flow_dir[r, c] = best_dir

# ---------------------------------------
# 3. Flow accumulation
# ---------------------------------------
rows, cols = filled.shape
accumulation = np.ones((rows, cols), dtype=np.float32)

# Process cells from high elevation to low elevation
order = np.argsort(filled.ravel())[::-1]

direction_lookup = {
    1:  (0, 1),
    2:  (1, 1),
    4:  (1, 0),
    8:  (1, -1),
    16: (0, -1),
    32: (-1, -1),
    64: (-1, 0),
    128: (-1, 1),
}

for idx in order:
    r = idx // cols
    c = idx % cols

    code = int(flow_dir[r, c])

    if code == 0:
        continue

    dr, dc = direction_lookup[code]
    nr = r + dr
    nc = c + dc

    if 0 <= nr < rows and 0 <= nc < cols:
        accumulation[nr, nc] += accumulation[r, c]

# ---------------------------------------
# 4. Save outputs
# ---------------------------------------
def save_raster(path, data, dtype):
    p = profile.copy()
    p.update(
        dtype=dtype,
        count=1,
        nodata=-9999,
        compress="deflate"
    )

    with rasterio.open(path, "w", **p) as dst:
        dst.write(data.astype(dtype), 1)

save_raster(
    OUTDIR / "final_hydrology_filled.tif",
    filled,
    "float32"
)

save_raster(
    OUTDIR / "final_flow_direction.tif",
    flow_dir,
    "int16"
)

save_raster(
    OUTDIR / "final_flow_accumulation.tif",
    accumulation,
    "float32"
)

print("HYDROLOGY CREATED")
print("Filled DEM: data/processed/final_hydrology_filled.tif")
print("Flow direction: data/processed/final_flow_direction.tif")
print("Flow accumulation: data/processed/final_flow_accumulation.tif")
print("MAX ACCUMULATION:", float(accumulation.max()))
print("FLOW CELLS:", int(np.sum(flow_dir > 0)))
