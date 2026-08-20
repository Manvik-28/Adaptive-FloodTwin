import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer


SURVEY_PATH = "data/dem/elevation_survey.csv"
DEM_PATH = "data/processed/final_dem.tif"


def duration_factor(duration_minutes: float) -> float:
    if duration_minutes <= 15:
        return 0.45
    elif duration_minutes <= 30:
        return 0.75
    return 1.0


def load_curve_number_grid(height, width, transform):
    df = pd.read_csv(SURVEY_PATH)

    df.columns = df.columns.str.strip()

    df["Surface_Type"] = (
        df["Surface_Type"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:32644",
        always_xy=True
    )

    sx, sy = transformer.transform(
        df["Longitude"].to_numpy(),
        df["Latitude"].to_numpy()
    )

    # Prototype assumptions
    CN_SOIL = 70.0
    CN_CONCRETE = 95.0

    cn_points = np.where(
        df["Surface_Type"].to_numpy() == "concrete",
        CN_CONCRETE,
        CN_SOIL
    ).astype(np.float32)

    rows, cols = np.indices((height, width))

    gx = (
        transform.c
        + (cols + 0.5) * transform.a
    )

    gy = (
        transform.f
        + (rows + 0.5) * transform.e
    )

    px = sx.reshape(1, 1, -1)
    py = sy.reshape(1, 1, -1)

    distance2 = (
        (gx[:, :, None] - px) ** 2
        +
        (gy[:, :, None] - py) ** 2
    )

    k = min(12, len(cn_points))

    nearest = np.argpartition(
        distance2,
        k - 1,
        axis=2
    )[:, :, :k]

    nearest_distance2 = np.take_along_axis(
        distance2,
        nearest,
        axis=2
    )

    nearest_cn = cn_points[nearest]

    weights = 1.0 / np.maximum(
        nearest_distance2,
        1e-12
    )

    cn_grid = (
        np.sum(weights * nearest_cn, axis=2)
        /
        np.sum(weights, axis=2)
    )

    return cn_grid


def calculate_runoff(
    rainfall_mm: float,
    duration_minutes: float,
    dem_path=DEM_PATH
):
    with rasterio.open(dem_path) as src:

        height = src.height
        width = src.width
        transform = src.transform

        cell_area = (
            abs(src.transform.a)
            *
            abs(src.transform.e)
        )

    cn_grid = load_curve_number_grid(
        height,
        width,
        transform
    )

    # Duration controls how much of the scenario rainfall
    # contributes during the event.
    effective_rainfall_mm = (
        rainfall_mm
        *
        duration_factor(duration_minutes)
    )

    P = effective_rainfall_mm

    # SCS Curve Number
    S = (
        25400.0 / cn_grid
    ) - 254.0

    initial_abstraction = 0.2 * S

    runoff_mm = np.where(
        P > initial_abstraction,
        (
            (P - initial_abstraction) ** 2
        )
        /
        (
            P + 0.8 * S
        ),
        0.0
    )

    infiltration_mm = np.maximum(
        P - runoff_mm,
        0.0
    )

    runoff_volume_m3 = (
        runoff_mm / 1000.0
    ) * cell_area

    return {
        "runoff_mm": runoff_mm.astype(np.float32),
        "infiltration_mm": infiltration_mm.astype(np.float32),
        "runoff_volume_m3": runoff_volume_m3.astype(np.float32),
        "curve_number": cn_grid.astype(np.float32),
        "effective_rainfall_mm": effective_rainfall_mm,
        "cell_area_m2": cell_area,
    }
