"""
Adaptive FloodTwin - Backend API

Run from the repo root (per FloodTwin_Teammate_Setup_Guide):

    uvicorn backend.main:app --reload

Endpoint map:
  GET  /                      - health/info
  GET  /health                - liveness probe
  GET  /campus-data           - roads, buildings, boundary, drainage (GeoJSON)
  GET  /scenarios             - precomputed rainfall scenarios
  GET  /simulate               - legacy, kept for the current frontend build
  GET  /simulate/{scenario_id} - precomputed time-series for a named scenario
  POST /evacuation-route       - flood-aware evacuation routing (new contract)
  GET  /evacuate                - legacy, kept for the current frontend build

The legacy /simulate and /evacuate endpoints are exactly what
frontend/src/App.jsx currently calls (see fetch calls to
http://127.0.0.1:8000/simulate and /evacuate) - they're kept working
unchanged so nobody's demo breaks mid-integration. The new endpoints below
are the ones described in 3floodtwinbackend.pdf's "Suggested endpoints"
section; point the frontend at them once it's ready to use the richer
GeoJSON/graph-routing responses.
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.schemas import EvacuationRequest
from backend.services import campus_service, scenario_service, simulation_service, evacuation_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("floodtwin.main")

app = FastAPI(
    title="Adaptive FloodTwin",
    description="Physics-guided micro-scale flood prediction and evacuation API for the GRIET campus digital twin.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Adaptive FloodTwin API is running",
        "endpoints": [
            "/campus-data", "/scenarios", "/simulate", "/simulate/{scenario_id}",
            "/evacuation-route", "/evacuate", "/health",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Campus GIS data
# ---------------------------------------------------------------------------

@app.get("/campus-data")
def campus_data():
    return campus_service.get_campus_data()


# ---------------------------------------------------------------------------
# Rainfall scenarios
# ---------------------------------------------------------------------------

@app.get("/scenarios")
def scenarios():
    return {"scenarios": scenario_service.list_scenarios()}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

@app.get("/simulate")
def simulate(rainfall_mm: int = 100, duration_minutes: int = 60):
    """Legacy live-simulate endpoint - what the current frontend calls."""
    return simulation_service.run_simulation(rainfall_mm=rainfall_mm, duration_minutes=duration_minutes)


@app.get("/simulate/{scenario_id}")
def simulate_scenario(scenario_id: str, refresh: bool = False):
    """Precomputed, cached simulation for a named scenario (see
    3floodtwinbackend.pdf section 5, 'Precompute-for-demo strategy')."""
    params = scenario_service.get_scenario(scenario_id)
    if params is None:
        raise HTTPException(status_code=404, detail=f"Unknown scenario_id '{scenario_id}'")
    return simulation_service.get_precomputed(scenario_id, params, force_refresh=refresh)


# ---------------------------------------------------------------------------
# Evacuation
# ---------------------------------------------------------------------------

@app.post("/evacuation-route")
def evacuation_route(body: EvacuationRequest):
    return evacuation_service.find_route(
        start_point=body.start_point,
        destination=body.destination,
        timestep=body.timestep or 0,
        scenario_id=body.scenario_id,
    )


@app.get("/evacuate")
def evacuate(start: str = "Building-A", destination: str = "Safe-Zone"):
    """Legacy live-evacuate endpoint - what the current frontend calls."""
    return evacuation_service.find_route(start_point=None, destination=destination)
