import rasterio
import numpy as np


DEM_PATH = "data/dem/hydrology_dem_filled.tif"
SLOPE_PATH = "data/processed/slope_hydro.tif"
FLOW_ACC_PATH = "data/processed/flow_accumulation_hydro.tif"
FLOW_DIR_PATH = "data/processed/flow_direction_hydro.tif"


def load_raster(path):

    with rasterio.open(path) as src:

        data = src.read(1).astype(np.float32)
        profile = src.profile
        nodata = src.nodata

    if nodata is not None:
        data[data == nodata] = np.nan

    return data, profile


def load_terrain():

    # -----------------------------
    # Load DEM
    # -----------------------------

    dem, dem_profile = load_raster(DEM_PATH)

    # -----------------------------
    # Load slope
    # -----------------------------

    slope, slope_profile = load_raster(
        SLOPE_PATH
    )

    # -----------------------------
    # Load flow accumulation
    # -----------------------------

    flow_accumulation, acc_profile = load_raster(
        FLOW_ACC_PATH
    )

    # -----------------------------
    # Load flow direction
    # -----------------------------

    flow_direction, dir_profile = load_raster(
        FLOW_DIR_PATH
    )

    # -----------------------------
    # Safety checks
    # -----------------------------

    if dem.shape != slope.shape:
        raise ValueError(
            f"DEM shape {dem.shape} != "
            f"slope shape {slope.shape}"
        )

    if dem.shape != flow_accumulation.shape:
        raise ValueError(
            f"DEM shape {dem.shape} != "
            f"flow accumulation shape {flow_accumulation.shape}"
        )

    if dem.shape != flow_direction.shape:
        raise ValueError(
            f"DEM shape {dem.shape} != "
            f"flow direction shape {flow_direction.shape}"
        )

    # -----------------------------
    # Print information
    # -----------------------------

    print("Terrain data loaded successfully")

    print("DEM shape:", dem.shape)
    print("DEM CRS:", dem_profile["crs"])

    print(
        "Elevation minimum:",
        np.nanmin(dem)
    )

    print(
        "Elevation maximum:",
        np.nanmax(dem)
    )

    print(
        "Slope shape:",
        slope.shape
    )

    print(
        "Slope minimum:",
        np.nanmin(slope)
    )

    print(
        "Slope maximum:",
        np.nanmax(slope)
    )

    print(
        "Flow accumulation shape:",
        flow_accumulation.shape
    )

    print(
        "Flow direction shape:",
        flow_direction.shape
    )

    # -----------------------------
    # Return terrain data
    # -----------------------------

    return {
        "dem": dem,
        "slope": slope,
        "flow_accumulation": flow_accumulation,
        "flow_direction": flow_direction,
        "profile": dem_profile
    }


if __name__ == "__main__":

    load_terrain()