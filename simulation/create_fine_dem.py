import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from pyproj import Transformer

INPUT = "data/dem/elevation_survey.csv"
OUTPUT = "data/dem/fine_dem.tif"

# Load survey
df = pd.read_csv(INPUT)
df.columns = df.columns.str.strip()

# Convert WGS84 -> UTM 44N
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32644",
    always_xy=True
)

x, y = transformer.transform(
    df["Longitude"].to_numpy(),
    df["Latitude"].to_numpy()
)

z = df["Ground_Elevation_m"].to_numpy(dtype=float)

# 10 m output resolution
resolution = 10.0

xmin = x.min()
xmax = x.max()
ymin = y.min()
ymax = y.max()

width = int(np.ceil((xmax - xmin) / resolution)) + 1
height = int(np.ceil((ymax - ymin) / resolution)) + 1

# Raster cell centers
grid_x = xmin + (np.arange(width) + 0.5) * resolution
grid_y = ymax - (np.arange(height) + 0.5) * resolution

gx, gy = np.meshgrid(grid_x, grid_y)

# IDW interpolation
points_x = x.reshape(1, 1, -1)
points_y = y.reshape(1, 1, -1)

dist2 = (gx[:, :, None] - points_x) ** 2 + \
        (gy[:, :, None] - points_y) ** 2

# 12 nearest survey points
k = min(12, len(z))
nearest = np.argpartition(dist2, k - 1, axis=2)[:, :, :k]

nearest_dist2 = np.take_along_axis(dist2, nearest, axis=2)

weights = 1.0 / np.maximum(nearest_dist2, 1e-12)

nearest_z = z[nearest]

fine_dem = np.sum(weights * nearest_z, axis=2) / np.sum(weights, axis=2)

# Force exact survey elevations onto nearest raster cells
for px, py, pz in zip(x, y, z):
    col = int((px - xmin) / resolution)
    row = int((ymax - py) / resolution)

    if 0 <= row < height and 0 <= col < width:
        fine_dem[row, col] = pz

transform = from_origin(
    xmin,
    ymax,
    resolution,
    resolution
)

# Write GeoTIFF
with rasterio.open(
    OUTPUT,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype="float32",
    crs="EPSG:32644",
    transform=transform,
    nodata=-9999.0,
    compress="deflate"
) as dst:
    dst.write(fine_dem.astype("float32"), 1)

print("Fine DEM created successfully")
print("OUTPUT:", OUTPUT)
print("CRS: EPSG:32644")
print("RESOLUTION:", resolution, "m")
print("SIZE:", width, "x", height)
print("ELEVATION MIN:", float(fine_dem.min()))
print("ELEVATION MAX:", float(fine_dem.max()))
