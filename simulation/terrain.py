import rasterio
import numpy as np


DEM_PATH = "data/dem/coarse_dem.tif"
SLOPE_PATH = "data/processed/slope.tif"
FLOW_ACC_PATH = "data/processed/flow_accumulation.tif"
FLOW_DIR_PATH = "data/processed/flow_direction.tif"


def load_raster(path):
    with rasterio.open(path) as src:
        data = src.read(1).astype(np.float32)
        profile = src.profile
        nodata = src.nodata

    if nodata is not None:
        data[data == nodata] = np.nan

    return data, profile


def load_terrain():

    dem, dem_profile = load_raster(DEM_PATH)
    slope, _ = load_raster(SLOPE_PATH)
    flow_accumulation, _ = load_raster(FLOW_ACC_PATH)
    flow_direction, _ = load_raster(FLOW_DIR_PATH)

    print("Terrain data loaded successfully")

    print("DEM shape:", dem.shape)
    print("DEM CRS:", dem_profile["crs"])

    print("Elevation minimum:", np.nanmin(dem))
    print("Elevation maximum:", np.nanmax(dem))

    print("Slope shape:", slope.shape)
    print("Flow accumulation shape:", flow_accumulation.shape)
    print("Flow direction shape:", flow_direction.shape)

    return {
        "dem": dem,
        "slope": slope,
        "flow_accumulation": flow_accumulation,
        "flow_direction": flow_direction,
        "profile": dem_profile
    }


if __name__ == "__main__":
    load_terrain()