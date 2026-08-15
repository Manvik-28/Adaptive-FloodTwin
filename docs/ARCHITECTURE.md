# System Architecture

## Overall Flow

GIS/Data
   ↓
Flood Simulation
   ↓
Backend API
   ↓
Frontend
   ↓
User

Flood Simulation
   ↓
Evacuation Engine
   ↓
Backend API
   ↓
Frontend

## Components

### GIS/Data
Provides:
- DEM
- Roads
- Buildings
- Drainage
- Campus boundary

### Simulation
Receives:
- DEM
- Rainfall scenario
- Drainage information

Produces:
- Flood depth
- Flood extent
- Time-step results

### Evacuation
Receives:
- Road network
- Flood state

Produces:
- Safer evacuation route

### Backend
Connects:
- Simulation
- Evacuation
- Frontend

### Frontend
Displays:
- Campus map
- Flood extent
- Flood depth
- Time progression
- Evacuation route