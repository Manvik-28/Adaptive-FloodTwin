"""
Pydantic models mirroring docs/DATA_CONTRACT.md.

Keep this file and DATA_CONTRACT.md in sync -- per the contract's own rule
("Important Integration Rule"), the doc must be updated first if a shape
needs to change, then the implementation.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
RouteStatus = Literal["Safe", "At Risk", "Blocked"]


class RainfallScenarioIn(BaseModel):
    """Section 1 of the data contract: what the frontend sends."""
    rainfall_mm: float = Field(..., gt=0)
    duration_minutes: int = Field(60, gt=0)


class ScenarioSummary(BaseModel):
    """One entry from GET /scenarios."""
    id: str
    label: str
    rainfall_mm: float
    duration_minutes: int


class Timestep(BaseModel):
    """One entry in a simulation result's timesteps list."""
    time_minutes: int
    max_depth_m: float
    mean_depth_m: Optional[float] = None
    flooded_area_fraction: Optional[float] = None
    risk_level: RiskLevel


class SimulationResult(BaseModel):
    """Section 2 of the data contract: flood simulation result."""
    scenario_id: Optional[str] = None
    rainfall_mm: float
    duration_minutes: int
    mode: Literal["physics-guided", "mock"] = "mock"
    notes: Optional[str] = None
    timesteps: List[Timestep]


class EvacuationRequest(BaseModel):
    """Section 3 of the data contract, extended with an optional timestep
    so the route can react to predicted future flood conditions."""
    start_point: List[float] = Field(..., min_length=2, max_length=2)
    destination: Optional[str] = "safe_zone"
    timestep: Optional[int] = 0
    scenario_id: Optional[str] = None


class EvacuationResponse(BaseModel):
    """Section 4 of the data contract."""
    start: List[float]
    destination: str
    route_coordinates: List[List[float]]
    estimated_time_minutes: float
    risk: str
    status: RouteStatus
    mode: Literal["graph", "mock"] = "mock"
