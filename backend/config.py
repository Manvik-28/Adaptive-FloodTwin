"""
Central configuration for the Adaptive FloodTwin backend.

All paths are written relative to the repo root because the team runs the
API with:

    uvicorn backend.main:app --reload

...from the top-level Adaptive-FloodTwin/ folder (see
FloodTwin_Teammate_Setup_Guide). Do not hardcode absolute paths here.
"""

import os

# ---------------------------------------------------------------------------
# Repo-relative paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
GIS_DIR = os.path.join(BASE_DIR, "gis")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

# GIS / campus vector layers (committed by the GIS/data teammate)
CAMPUS_ROADS_GPKG = os.path.join(DATA_DIR, "campus", "griet_roads.gpkg")
CAMPUS_BUILDINGS_GPKG = os.path.join(DATA_DIR, "campus", "griet_buildings.gpkg")
CAMPUS_BOUNDARY_GPKG = os.path.join(DATA_DIR, "campus", "griet_campus.gpkg")

# Drainage points are referenced in the architecture doc but not committed
# yet -- kept here so wiring them in later is a one-line change.
CAMPUS_DRAINAGE_GPKG = os.path.join(DATA_DIR, "campus", "griet_drainage.gpkg")

# Fallback vector layer used only if the real GIS layers above can't be read
MOCK_CAMPUS_GEOJSON_CANDIDATES = [
    os.path.join(GIS_DIR, "mock_campus.geojson"),
    os.path.join(BASE_DIR, "frontend", "public", "data", "mock_campus.geojson"),
]

# DEM / terrain rasters. NOTE: simulation/terrain.py currently points at
# data/processed/flow_accumulation.tif and flow_direction.tif, but the files
# actually committed are named *_correct.tif, and slope.tif does not exist
# in the repo at all yet. The backend tries every known name below so it
# keeps working regardless of which naming convention lands first; the
# mismatch itself is flagged in backend/README.md for the simulation/GIS
# leads to reconcile.
DEM_PATH = os.path.join(DATA_DIR, "dem", "coarse_dem.tif")

FLOW_ACCUMULATION_CANDIDATES = [
    os.path.join(DATA_DIR, "processed", "flow_accumulation_correct.tif"),
    os.path.join(DATA_DIR, "processed", "flow_accumulation.tif"),
]

FLOW_DIRECTION_CANDIDATES = [
    os.path.join(DATA_DIR, "processed", "flow_direction_correct.tif"),
    os.path.join(DATA_DIR, "processed", "flow_direction.tif"),
]

SLOPE_CANDIDATES = [
    os.path.join(DATA_DIR, "processed", "slope.tif"),
]

# Rainfall scenarios (committed by the simulation/GIS teammates)
RAINFALL_SCENARIOS_PATH = os.path.join(DATA_DIR, "sample", "rainfall.json")

# ---------------------------------------------------------------------------
# Physics-guided simulation defaults
# ---------------------------------------------------------------------------

# Curve Number placeholder until the field-survey-derived land-cover /
# CN raster is available (see 5floodtwinwaterphysics: typical CN by surface
# type). 90 sits between "paved/rooftop" (~98) and "grass, fair" (~70-80) as
# a rough campus-wide mix; using a single value is a documented MVP
# simplification, not a silent guess. Tune once the real CN raster lands.
DEFAULT_CURVE_NUMBER = 90

# Timestep and storm shape defaults for the precompute pipeline
TIMESTEP_MINUTES = 10
RECESSION_MINUTES = 30

# Fraction of standing water assumed to leave the system per timestep in the
# absence of surveyed drain capacities (Manning's-equation inputs). This is
# an explicit literature-typical placeholder -- see backend/README.md.
# Tuned low (light outflow) so the demo curve can actually reach MEDIUM/HIGH
# for a heavy storm scenario instead of draining every timestep back to
# near-zero; revisit once real drain capacities are surveyed.
DEFAULT_DRAINAGE_DECAY_PER_STEP = 0.04

# ---------------------------------------------------------------------------
# Risk thresholds (see 6floodtwingapsandplan: "Define safe explicitly")
# ---------------------------------------------------------------------------

RISK_THRESHOLDS_M = {
    "LOW": 0.10,     # up to 10cm
    "MEDIUM": 0.25,  # 10-25cm
    # anything above 0.25m is HIGH
}

# A zone is considered unsafe/blocked for evacuation routing once predicted
# depth exceeds this value (~ankle-deep, enough to hide a pothole/open drain)
UNSAFE_DEPTH_THRESHOLD_M = 0.15

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
