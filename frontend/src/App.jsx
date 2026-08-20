import Griet3D from "./Griet3D";
import { useState, useEffect } from "react";

import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Polyline,
  ImageOverlay,
  ZoomControl,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [show3D, setShow3D] = useState(false);

  const [rainfall, setRainfall] = useState(150);
  const [duration, setDuration] = useState(30);

  const [floodData, setFloodData] = useState(null);
  const [campusData, setCampusData] = useState(null);
  const [floodBounds, setFloodBounds] = useState(null);

  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationError, setSimulationError] = useState("");

  useEffect(() => {
    fetch("/data/griet_campus.geojson")
      .then((response) => response.json())
      .then((data) => setCampusData(data))
      .catch((error) => {
        console.error("Campus GeoJSON error:", error);
      });
  }, []);

  async function simulateFlood() {
    setSimulationLoading(true);
    setSimulationError("");

    try {
      const simulateResponse = await fetch(
        `${API}/simulate?rainfall_mm=${rainfall}&duration_minutes=${duration}`
      );

      if (!simulateResponse.ok) {
        throw new Error(
          `Simulation API failed: ${simulateResponse.status}`
        );
      }

      const data = await simulateResponse.json();

      // Keep selected duration visible even before the backend
      // starts using it in the physics model.
      data.duration_minutes = duration;

      setFloodData(data);

      const boundsResponse = await fetch(
        `${API}/flood-bounds?rainfall_mm=${rainfall}&duration_minutes=${duration}`
      );

      if (!boundsResponse.ok) {
        throw new Error(
          `Flood bounds API failed: ${boundsResponse.status}`
        );
      }

      const bounds = await boundsResponse.json();

      setFloodBounds([
        [bounds.south, bounds.west],
        [bounds.north, bounds.east],
      ]);
    } catch (error) {
      console.error("Simulation error:", error);

      setSimulationError(
        "Unable to run simulation. Make sure FastAPI is running."
      );
    } finally {
      setSimulationLoading(false);
    }
  }

  const currentDepth = floodData?.max_depth_m ?? 0;
  const meanDepth = floodData?.mean_depth_m ?? 0;
  const currentRisk = floodData?.risk_level ?? "SAFE";

  const highDepthCells = floodData?.high_risk_cells ?? 0;
  const criticalCells = floodData?.critical_cells ?? 0;

  const highDepthArea = highDepthCells * 100;
  const criticalArea = criticalCells * 100;

  const evacuation = floodData?.evacuation;

  const evacuationAvailable =
    evacuation?.route && evacuation.route.length > 0;

  const riskClass = currentRisk.toLowerCase();

  const routeRiskClass =
    evacuation?.risk?.toLowerCase() || "low";

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">

        <div className="logo">

          <div className="logo-icon">
            FT
          </div>

          <div>
            <h1>Adaptive FloodTwin</h1>
            <span>
              GRIET Campus Flood Intelligence
            </span>
          </div>

        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          System Online
        </div>

      </header>


      {/* CONTROL PANEL */}
      <aside className="control-panel">

        <div className="dashboard-heading">
          <h2 className="panel-title">
            Flood Simulation
          </h2>

          <p className="panel-subtitle">
            Physics-guided campus flood monitoring
          </p>
        </div>


        {/* SCENARIO */}
        <div className="section simulation-section">

          <div className="section-title">
            Rainfall Scenario
          </div>

          <select
            className="select"
            value={rainfall}
            onChange={(e) =>
              setRainfall(Number(e.target.value))
            }
          >
            <option value={100}>
              100 mm - Heavy
            </option>

            <option value={150}>
              150 mm - Very Heavy
            </option>

            <option value={250}>
              250 mm - Extreme
            </option>

            <option value={350}>
              350 mm - Severe
            </option>
          </select>


          <div className="section-title duration-title">
            Rain Duration
          </div>

          <select
            className="select"
            value={duration}
            onChange={(e) =>
              setDuration(Number(e.target.value))
            }
          >
            <option value={15}>
              15 min - Short Event
            </option>

            <option value={30}>
              30 min - Continuous Rain
            </option>

            <option value={60}>
              60 min - Prolonged Rain
            </option>
          </select>


          <button
            className="primary-button"
            onClick={simulateFlood}
            disabled={simulationLoading}
          >
            {simulationLoading
              ? "Running Simulation..."
              : "Run Flood Simulation"}
          </button>


          {simulationError && (
            <div className="simulation-error">
              {simulationError}
            </div>
          )}

        </div>


        {/* RESULTS */}
        {floodData && (
          <>

            {/* CURRENT CONDITIONS */}
            <div className="section">

              <div className="section-title">
                Current Conditions
              </div>

              <div className={`risk-status-card ${riskClass}`}>

                <div className="risk-status-label">
                  Overall Flood Risk
                </div>

                <div className="risk-status-value">
                  {currentRisk}
                </div>

                <div className="risk-status-depth">
                  Maximum depth: {currentDepth.toFixed(3)} m
                </div>

              </div>

            </div>


            {/* KEY METRICS */}
            <div className="section">

              <div className="section-title">
                Key Indicators
              </div>

              <div className="metric-grid">

                <div className="metric-card">

                  <div className="metric-label">
                    Rainfall
                  </div>

                  <div className="metric-value">
                    {floodData.rainfall_mm}
                    <span> mm</span>
                  </div>

                </div>


                <div className="metric-card">

                  <div className="metric-label">
                    Duration
                  </div>

                  <div className="metric-value">
                    {duration}
                    <span> min</span>
                  </div>

                </div>


                <div className="metric-card">

                  <div className="metric-label">
                    Max Depth
                  </div>

                  <div className="metric-value">
                    {currentDepth.toFixed(3)}
                    <span> m</span>
                  </div>

                </div>


                <div className="metric-card">

                  <div className="metric-label">
                    Mean Depth
                  </div>

                  <div className="metric-value">
                    {meanDepth.toFixed(3)}
                    <span> m</span>
                  </div>

                </div>

              </div>

            </div>


            {/* FLOOD IMPACT */}
            <div className="section">

              <div className="section-title">
                Flood Impact
              </div>

              <div className="impact-row">

                <div>
                  <span className="impact-label">
                    High-depth cells
                  </span>

                  <strong>
                    {highDepthCells}
                  </strong>
                </div>

                <div>
                  <span className="impact-label">
                    High-depth area
                  </span>

                  <strong>
                    {highDepthArea.toLocaleString()} m²
                  </strong>
                </div>

                <div>
                  <span className="impact-label">
                    Critical cells
                  </span>

                  <strong>
                    {criticalCells}
                  </strong>
                </div>

                <div>
                  <span className="impact-label">
                    Critical area
                  </span>

                  <strong>
                    {criticalArea.toLocaleString()} m²
                  </strong>
                </div>

              </div>

            </div>


            {/* EVACUATION */}
            <div className="section">

              <div className="section-title">
                Evacuation
              </div>

              <div
                className={`evacuation-status ${
                  evacuationAvailable
                    ? "available"
                    : "blocked"
                }`}
              >

                <div className="evacuation-status-label">
                  Evacuation Status
                </div>

                <div className="evacuation-status-value">
                  {evacuationAvailable
                    ? "AVAILABLE"
                    : "BLOCKED"}
                </div>

                <div className="evacuation-status-message">
                  {evacuation?.message ||
                    "No evacuation route available."}
                </div>

              </div>


              {evacuationAvailable ? (

                <div className="route-box">

                  <div className="route-title">
                    Safest Available Route
                  </div>

                  <div className="route-main">
                    {evacuation.start}
                    <span>to</span>
                    {evacuation.destination}
                  </div>

                  <div className="route-stats">

                    <div>
                      <span>Distance</span>
                      <strong>
                        {evacuation.route_distance_m} m
                      </strong>
                    </div>

                    <div>
                      <span>ETA</span>
                      <strong>
                        {evacuation.estimated_time_minutes} min
                      </strong>
                    </div>

                    <div>
                      <span>Flood Depth</span>
                      <strong>
                        {evacuation.max_flood_depth_m} m
                      </strong>
                    </div>

                  </div>

                  <div className={`route-risk-badge ${routeRiskClass}`}>
                    Route Risk: {evacuation.risk}
                  </div>

                </div>

              ) : (

                <div className="blocked-box">

                  <div className="blocked-title">
                    No Safe Evacuation Route
                  </div>

                  <div className="blocked-text">
                    Current flooding prevents a safe route
                    from the Main Gate to the Assembly Point.
                  </div>

                </div>

              )}

            </div>

          </>
        )}

      </aside>


      {/* MAP */}
      <div className="map-container">

        <MapContainer
          center={[17.5205, 78.366]}
          zoom={16}
          zoomControl={false}
          style={{
            height: "100%",
            width: "100%",
          }}
        >

          <ZoomControl position="bottomright" />

          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {floodBounds && floodData && (
            <ImageOverlay
              key={`flood-${floodData.rainfall_mm}-${floodData.duration_minutes}`}
              url={`${API}/flood-overlay?rainfall_mm=${floodData.rainfall_mm}&duration_minutes=${floodData.duration_minutes}`}
              bounds={floodBounds}
              opacity={0.65}
            />
          )}

          {campusData && (
            <GeoJSON data={campusData} />
          )}

          {evacuationAvailable &&
            evacuation.route_coordinates &&
            evacuation.route_coordinates.length > 1 && (
              <Polyline
                positions={evacuation.route_coordinates}
                pathOptions={{
                  color: "lime",
                  weight: 6,
                }}
              />
            )}

        </MapContainer>


        <button
          className="view-3d-button"
          onClick={() => setShow3D(true)}
        >
          View 3D Terrain
        </button>


        <div className="map-legend">

          <div className="legend-title">
            Map Legend
          </div>

          <div className="legend-item">
            <span className="legend-color low"></span>
            Low Risk
          </div>

          <div className="legend-item">
            <span className="legend-color medium"></span>
            Moderate Risk
          </div>

          <div className="legend-item">
            <span className="legend-color high"></span>
            High Risk
          </div>

          <div className="legend-line route"></div>
          Evacuation Route

        </div>

      </div>


      {/* 3D MODAL */}
      {show3D && (
        <div className="three-d-overlay">

          <div className="three-d-panel">

            <div className="three-d-header">

              <div>
                <h2>GRIET 3D Terrain</h2>

                <span>
                  Campus elevation visualization
                </span>
              </div>

              <button
                className="three-d-close"
                onClick={() => setShow3D(false)}
              >
                Close
              </button>

            </div>

            <div className="three-d-content">
              <Griet3D
                rainfall={floodData?.rainfall_mm ?? rainfall}
                duration={floodData?.duration_minutes ?? duration}
              />
            </div>

          </div>

        </div>
      )}

    </div>
  );
}

export default App;