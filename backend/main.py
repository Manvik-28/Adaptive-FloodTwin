from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simulation.mock_simulation import simulate_flood
from evacuation.mock_route import find_route


app = FastAPI(title="Adaptive FloodTwin")


# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Adaptive FloodTwin API is running"
    }


@app.get("/simulate")
def simulate(rainfall_mm: int = 100):

    result = simulate_flood(rainfall_mm)

    return result


@app.get("/evacuate")
def evacuate(
    start: str = "Building-A",
    destination: str = "Safe-Zone"
):

    result = find_route(start, destination)

    return result