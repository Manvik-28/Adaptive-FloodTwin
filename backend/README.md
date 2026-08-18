# Adaptive FloodTwin — Backend

FastAPI service that connects GIS/terrain data → the simulation pipeline →
the evacuation graph, per `docs/ARCHITECTURE.md` and `docs/DATA_CONTRACT.md`.

## Run it

From the **repo root** (not from inside `backend/`):

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Docs at `http://127.0.0.1:8000/docs`.

## Endpoint map

| Endpoint | Status | Notes |
|---|---|---|
| `GET /` | new | health/info + endpoint list |
| `GET /health` | new | liveness probe |
| `GET /campus-data` | new | roads/buildings/boundary/drainage as GeoJSON |
| `GET /scenarios` | new | precomputed rainfall scenarios from `data/sample/rainfall.json` |
| `GET /simulate` | **legacy, unchanged contract** | what `frontend/src/App.jsx` currently calls (`?rainfall_mm=`) |
| `GET /simulate/{scenario_id}` | new | precomputed + cached, per `3floodtwinbackend.pdf` §5 |
| `POST /evacuation-route` | new | body per `docs/DATA_CONTRACT.md` §3, flood-aware graph routing |
| `GET /evacuate` | **legacy, unchanged contract** | what `frontend/src/App.jsx` currently calls |

The legacy endpoints are untouched in shape (still return `rainfall_mm` /
`timesteps[].max_depth_m` / `risk_level` etc.) so the current frontend build
keeps working exactly as-is. They now run through the same service layer as
the new endpoints, so a "physics-guided" result is returned automatically
once the required terrain files are present — nobody has to change the
frontend for that upgrade to kick in.

## How each request degrades gracefully

Every service tries the real pipeline first and falls back to something
that still returns a valid response, so a missing file never 500s a live
demo:

- **`campus_service`**: real `.gpkg` layers → `gis/mock_campus.geojson` → empty `FeatureCollection`.
- **`simulation_service`**: DEM + flow-accumulation rasters + SCS-CN runoff (`mode: "physics-guided"`) → `simulation/mock_simulation.py` (`mode: "mock"`).
- **`evacuation_service`**: NetworkX graph over the real roads layer, risk-weighted by the current simulation (`mode: "graph"`) → `evacuation/mock_route.py` (`mode: "mock"`).

Every simulation/evacuation response includes `"mode"` so you always know
which path actually ran — say this out loud in the demo if it falls back,
per the gaps doc's "name your simplifications" advice.

## Known gaps found while wiring this up (flag to the relevant leads)

1. **`simulation/terrain.py` path mismatch.** It looks for
   `data/processed/flow_accumulation.tif`, `flow_direction.tif`, and
   `slope.tif`. What's actually committed is
   `flow_accumulation_correct.tif` and `flow_direction_correct.tif` — no
   `slope.tif` at all yet. `backend/services/simulation_service.py` loads
   rasters itself and tries both naming conventions so the API doesn't
   depend on this being fixed, but `terrain.py` itself (used if the
   simulation lead imports it directly) will currently raise
   `FileNotFoundError`. Worth a quick rename/alignment on the
   `simulation-development` branch.
2. **Coordinate order inconsistency.** `docs/DATA_CONTRACT.md` documents
   `start`/`route` as `[longitude, latitude]`. `evacuation/mock_route.py`'s
   `route_coordinates` are actually stored as `[latitude, longitude]`
   (e.g. `17.44755` first — that's Hyderabad's latitude). The new
   `/evacuation-route` endpoint and `evacuation_service.py` follow the
   documented `[lon, lat]` order; the legacy `/evacuate` mock fallback still
   returns the mock file's original `[lat, lon]` points unchanged, so it's
   safe but inconsistent between modes. Worth reconciling before the
   frontend renders both.
3. **No drainage points layer committed yet** (`data/campus/griet_drainage.gpkg`
   doesn't exist). `campus_service.get_campus_data()` already looks for it
   and returns `drainage_points: null` with a note when absent —
   `simulation_service` uses a literature-typical decay constant
   (`config.DEFAULT_DRAINAGE_DECAY_PER_STEP`) as a stand-in until surveyed
   drain capacities land.
4. **No land-cover/Curve-Number raster yet**, so the physics-guided runoff
   uses a single uniform placeholder CN (`config.DEFAULT_CURVE_NUMBER = 80`)
   for the whole campus instead of per-surface-type values from
   `5floodtwinwaterphysics.pdf`. One line to fix once that raster exists —
   see `simulation_service._run_physics_guided`.
5. **Fill-and-spill is "lite" for now.** The current physics-guided mode
   routes runoff by flow-accumulation weighting but doesn't yet do explicit
   depression-filling/D8 spill-over between cells (that needs
   `richdem`/`pysheds`, not wired in by any module yet). This is the
   deliberate MVP simplification the physics doc calls out, not a hidden
   shortcut — say so in the pitch if asked.

## Config

All tunables (paths, CN default, drainage decay, risk thresholds) live in
`backend/config.py` — change values there rather than hardcoding new ones
in the services.

## Precompute cache

`GET /simulate/{scenario_id}` writes its result to `backend/cache/` on
first call and serves that cached JSON afterwards (matches the
"precompute-for-demo" strategy in `3floodtwinbackend.pdf` §5 — nothing
should visibly compute live in front of judges). Pass `?refresh=true` to
force a recompute after terrain data changes. The `cache/` folder is
git-ignored content (only `.gitkeep` is committed) — run the endpoint once
per scenario before the actual demo so it's warm.

## Testing without the full geospatial stack

If `geopandas`/`rasterio`/`networkx` aren't installed yet on your machine,
the API still boots and every endpoint still returns valid data — it just
runs in `"mode": "mock"` throughout. That's intentional: you can develop
and test the API contract before your GIS/simulation teammates' data lands.
