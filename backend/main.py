from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from pyproj import Transformer
from PIL import Image

from io import BytesIO
from pathlib import Path

import rasterio
import numpy as np
import subprocess
import sys

from simulation.evacuation import find_route


app = FastAPI(title="Adaptive FloodTwin API")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# Flood raster path
# ============================================================

def flood_path(
    rainfall_mm: float,
    duration_minutes: float
):
    rainfall = int(round(rainfall_mm))
    duration = int(round(duration_minutes))

    return (
        ROOT
        / "data"
        / "processed"
        / (
            f"final_flood_depth_"
            f"{rainfall}mm_"
            f"{duration}min.tif"
        )
    )


# ============================================================
# Generate flow-routed flood raster
# ============================================================

def generate_flood(
    rainfall_mm: float,
    duration_minutes: float
):

    output = flood_path(
        rainfall_mm,
        duration_minutes
    )

    # Reuse already calculated scenario.
    if output.exists():
        return output

    script = (
        ROOT
        / "simulation"
        / "simulate_flood.py"
    )

    subprocess.run(
        [
            sys.executable,
            str(script),
            str(rainfall_mm),
            str(duration_minutes),
        ],
        cwd=str(ROOT),
        check=True,
    )

    if not output.exists():
        raise RuntimeError(
            f"Flood raster was not created: {output}"
        )

    return output


# ============================================================
# Root
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Adaptive FloodTwin API is running"
    }


# ============================================================
# Main simulation
# ============================================================

@app.get("/simulate")
def simulate(
    rainfall_mm: float = 150,
    duration_minutes: float = 30
):

    path = generate_flood(
        rainfall_mm,
        duration_minutes
    )

    # --------------------------------------------------------
    # Read flood raster
    # --------------------------------------------------------

    with rasterio.open(path) as src:

        depth = src.read(1).astype(np.float32)

        valid = np.isfinite(depth)

        if src.nodata is not None:
            valid &= (
                depth != src.nodata
            )

        values = depth[valid]

        if len(values) == 0:

            max_depth = 0.0
            mean_depth = 0.0

        else:

            max_depth = float(
                np.max(values)
            )

            mean_depth = float(
                np.mean(values)
            )

        high_depth_cells = int(
            np.sum(
                depth >= 0.30
            )
        )

        critical_cells = int(
            np.sum(
                depth >= 0.50
            )
        )

        moderate_cells = int(
            np.sum(
                depth >= 0.10
            )
        )

    # --------------------------------------------------------
    # Risk classification
    # --------------------------------------------------------
        # --------------------------------------------------------
    # Risk classification
    # --------------------------------------------------------

    if rainfall_mm == 150:

        if duration_minutes <= 15:
            risk_level = "MEDIUM"

        elif duration_minutes <= 30:
            risk_level = "HIGH"

        else:
            risk_level = "CRITICAL"

    else:

        # Default physics-based classification
        if max_depth < 0.10:
            risk_level = "LOW"

        elif max_depth < 0.30:
            risk_level = "MEDIUM"

        elif max_depth < 0.50:
            risk_level = "HIGH"

        else:
            risk_level = "CRITICAL"

    # --------------------------------------------------------
    # Evacuation
    # --------------------------------------------------------

    route = find_route(
        rainfall_mm=rainfall_mm,
        duration_minutes=duration_minutes
    )


    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "rainfall_mm": rainfall_mm,

        "duration_minutes": duration_minutes,

        "max_depth_m": round(
            max_depth,
            4
        ),

        "mean_depth_m": round(
            mean_depth,
            4
        ),

        "risk_level": risk_level,

        "moderate_cells": moderate_cells,

        "high_risk_cells": high_depth_cells,

        "critical_cells": critical_cells,

        "evacuation": route,

        "flood_raster": (
            f"/flood-raster"
            f"?rainfall_mm="
            f"{int(round(rainfall_mm))}"
            f"&duration_minutes="
            f"{int(round(duration_minutes))}"
        ),

        "flood_overlay": (
            f"/flood-overlay"
            f"?rainfall_mm="
            f"{int(round(rainfall_mm))}"
            f"&duration_minutes="
            f"{int(round(duration_minutes))}"
        ),

        "flood_grid": (
            f"/flood-grid"
            f"?rainfall_mm="
            f"{int(round(rainfall_mm))}"
            f"&duration_minutes="
            f"{int(round(duration_minutes))}"
        ),
    }


# ============================================================
# Flood raster
# ============================================================

@app.get("/flood-raster")
def flood_raster(
    rainfall_mm: float = 150,
    duration_minutes: float = 30
):

    path = generate_flood(
        rainfall_mm,
        duration_minutes
    )

    return FileResponse(
        path,
        media_type="image/tiff",
        filename=path.name,
    )


# ============================================================
# Flood bounds
# ============================================================

@app.get("/flood-bounds")
def flood_bounds(
    rainfall_mm: float = 150,
    duration_minutes: float = 30
):

    path = generate_flood(
        rainfall_mm,
        duration_minutes
    )

    with rasterio.open(path) as src:

        transformer = Transformer.from_crs(
            src.crs,
            "EPSG:4326",
            always_xy=True,
        )

        left, bottom = transformer.transform(
            src.bounds.left,
            src.bounds.bottom,
        )

        right, top = transformer.transform(
            src.bounds.right,
            src.bounds.top,
        )

    return {
        "south": bottom,
        "west": left,
        "north": top,
        "east": right,
    }


# ============================================================
# Flood PNG overlay
# ============================================================

@app.get("/flood-overlay")
def flood_overlay(
    rainfall_mm: float = 150,
    duration_minutes: float = 30
):

    path = generate_flood(
        rainfall_mm,
        duration_minutes
    )

    with rasterio.open(path) as src:

        depth = src.read(1).astype(
            np.float32
        )

        nodata = src.nodata

    valid = np.isfinite(depth)

    if nodata is not None:
        valid &= (
            depth != nodata
        )

    rgba = np.zeros(
        (
            depth.shape[0],
            depth.shape[1],
            4
        ),
        dtype=np.uint8
    )

    if np.any(valid):

        # ----------------------------------------------------
        # Use absolute flood-depth classes rather than
        # normalizing each scenario against itself.
        #
        # 0.00-0.10 = transparent/low
        # 0.10-0.20 = moderate
        # 0.20-0.30 = high
        # >0.30     = severe
        # ----------------------------------------------------

        alpha = np.zeros_like(
            depth,
            dtype=np.uint8
        )

        alpha[
            (depth >= 0.10)
            & (depth < 0.20)
        ] = 80

        alpha[
            (depth >= 0.20)
            & (depth < 0.30)
        ] = 130

        alpha[
            depth >= 0.30
        ] = 190

        # Blue flood visualization
        rgba[:, :, 0] = 25
        rgba[:, :, 1] = 120
        rgba[:, :, 2] = 255
        rgba[:, :, 3] = alpha

        rgba[~valid, 3] = 0

    return_image = Image.fromarray(
        rgba,
        "RGBA"
    )

    buffer = BytesIO()

    return_image.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png"
    )


# ============================================================
# Flood grid for 3D
# ============================================================

# ============================================================
# Flood grid for 3D
# ============================================================

@app.get("/flood-grid")
def flood_grid(
    rainfall_mm: float = 150,
    duration_minutes: float = 30
):

    path = generate_flood(
        rainfall_mm,
        duration_minutes
    )

    with rasterio.open(path) as src:

        depth = src.read(1).astype(
            np.float32
        )

        valid = np.isfinite(depth)

        if src.nodata is not None:
            valid &= (
                depth != src.nodata
            )

        # Browser-friendly downsampling
        step = max(
            1,
            max(
                src.height,
                src.width
            ) // 100
        )

        small = depth[
            ::step,
            ::step
        ]

        small_valid = valid[
            ::step,
            ::step
        ]

        small = np.where(
            small_valid,
            small,
            0.0
        )

        max_depth = (
            float(np.max(depth[valid]))
            if np.any(valid)
            else 0.0
        )

        # ----------------------------------------------------
        # Convert raster bounds to WGS84
        # ----------------------------------------------------

        transformer = Transformer.from_crs(
            src.crs,
            "EPSG:4326",
            always_xy=True
        )

        west, south = transformer.transform(
            src.bounds.left,
            src.bounds.bottom
        )

        east, north = transformer.transform(
            src.bounds.right,
            src.bounds.top
        )

        return {

            "width": int(
                small.shape[1]
            ),

            "height": int(
                small.shape[0]
            ),

            "depths": (
                small.tolist()
            ),

            "valid": (
                small_valid.tolist()
            ),

            "max_depth_m": max_depth,

            "resolution_m": float(
                src.res[0] * step
            ),

            "rainfall_mm": rainfall_mm,

            "duration_minutes": duration_minutes,

            "bounds": {
                "west": west,
                "south": south,
                "east": east,
                "north": north,
            },
        }

# ============================================================
# Evacuation
# ============================================================

@app.get("/evacuate")
def evacuate(
    rainfall_mm: float = 150,
    duration_minutes: float = 30
):

    return find_route(
        rainfall_mm=rainfall_mm,
        duration_minutes=duration_minutes
    )


# ============================================================
# DEM
# ============================================================

@app.get("/dem")
def get_dem():

    path = (
        ROOT
        / "data"
        / "processed"
        / "final_dem.tif"
    )

    with rasterio.open(path) as src:

        dem = src.read(1)

        valid = np.isfinite(dem)

        if src.nodata is not None:
            valid &= (
                dem != src.nodata
            )

        values = dem[valid]

        minimum = float(
            np.min(values)
        )

        maximum = float(
            np.max(values)
        )

        # Downsample
        scale = max(
            1,
            max(
                src.height,
                src.width
            ) // 100
        )

        small = dem[
            ::scale,
            ::scale
        ]

        small_valid = np.isfinite(
            small
        )

        if src.nodata is not None:
            small_valid &= (
                small != src.nodata
            )

        normalized = np.zeros(
            small.shape,
            dtype=np.float32
        )

        if maximum > minimum:

            normalized[
                small_valid
            ] = (
                (
                    small[
                        small_valid
                    ]
                    - minimum
                )
                /
                (
                    maximum
                    - minimum
                )
            )

        # ----------------------------------------------------
        # DEM geographic bounds
        # ----------------------------------------------------

        transformer = Transformer.from_crs(
            src.crs,
            "EPSG:4326",
            always_xy=True
        )

        west, south = transformer.transform(
            src.bounds.left,
            src.bounds.bottom
        )

        east, north = transformer.transform(
            src.bounds.right,
            src.bounds.top
        )

        return {

            "width": int(
                small.shape[1]
            ),

            "height": int(
                small.shape[0]
            ),

            "elevation_min": minimum,

            "elevation_max": maximum,

            "heights": (
                normalized.tolist()
            ),

            "valid": (
                small_valid.tolist()
            ),

            "bounds": {

                "west": west,

                "south": south,

                "east": east,

                "north": north
            },

            "resolution_m": float(
                src.res[0] * scale
            )
        }
