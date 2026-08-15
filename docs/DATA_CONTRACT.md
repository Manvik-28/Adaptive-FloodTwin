# Adaptive FloodTwin — Data Contract


This document defines how the different modules of Adaptive FloodTwin communicate with each other.


## 1. Rainfall Scenario


The frontend sends a rainfall scenario to the backend.


```json
{
  "rainfall_mm": 100,
  "duration_minutes": 60
}

Fields:

rainfall_mm — total rainfall amount in millimetres.
duration_minutes — rainfall duration in minutes.
2. Flood Simulation Result

The flood simulation receives the rainfall scenario and terrain/drainage data and produces flood information for multiple time steps.

{
  "scenario": {
    "rainfall_mm": 100,
    "duration_minutes": 60
  },
  "timesteps": [
    {
      "time_minutes": 0,
      "flood_depth": "GeoJSON/Grid"
    },
    {
      "time_minutes": 10,
      "flood_depth": "GeoJSON/Grid"
    },
    {
      "time_minutes": 20,
      "flood_depth": "GeoJSON/Grid"
    }
  ]
}

Fields:

scenario — rainfall conditions used for the simulation.
timesteps — flood state at different points in time.
time_minutes — time elapsed since the beginning of the rainfall event.
flood_depth — spatial representation of water depth.

Note: GeoJSON/Grid is currently a placeholder. The exact representation will be finalized when the simulation and frontend implementation are developed.

3. Evacuation Request

The frontend/backend provides the evacuation engine with a starting location and destination.

{
  "start": [longitude, latitude],
  "destination": "safe_zone"
}

Fields:

start — current location of the person.
destination — safe location or evacuation zone.
4. Evacuation Response

The evacuation engine returns the recommended route.

{
  "route": [
    [longitude, latitude],
    [longitude, latitude],
    [longitude, latitude]
  ],
  "estimated_time_minutes": 8,
  "risk": "low"
}

Fields:

route — ordered geographic points forming the recommended path.
estimated_time_minutes — estimated travel time.
risk — estimated risk level of the route.
5. Main System Data Flow

Frontend
|
| Rainfall Scenario
v
Backend
|
v
Flood Simulation
|
| Flood Result
v
Backend
|
+--------------------+
| |
v v
Frontend Evacuation Engine
|
| Evacuation Route
v
Backend
|
v
Frontend

6. Module Responsibilities
GIS / Data

Provides:

DEM
Campus boundary
Roads
Buildings
Drainage information
Other required spatial data
Flood Simulation

Receives:

DEM
Rainfall scenario
Drainage information
Other required terrain data

Produces:

Flood depth
Flood extent
Time-dependent flood states
Evacuation Engine

Receives:

Road network
Flood state
Starting location
Safe destination

Produces:

Recommended evacuation route
Estimated travel time
Route risk
Backend

Connects:

Frontend
Flood simulation
Evacuation engine
Frontend

Displays:

Campus map
Rainfall scenario
Flood extent
Flood depth
Flood progression
Risk information
Evacuation route
7. Important Integration Rule

Each module can be developed independently.

However, when connecting modules, the input and output structures defined in this document must be followed.

If the data structure needs to change, the team must update this document before changing the implementation.

8. Current MVP Data Flow

Rainfall
|
v
Runoff
|
v
Surface Flow
|
v
Water Accumulation
|
v
Flood Depth / Flood Extent
|
v
Risk Assessment
|
v
Evacuation Route
|
v
Web Visualization

9. MVP Principle

The first implementation should use simple, reliable data structures.

The exact spatial representation of flood depth and flood extent will be finalized after the GIS, simulation, backend, and frontend members test the data flow together.