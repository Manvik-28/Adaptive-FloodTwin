import { useEffect, useState } from "react";

import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Polygon,
  Polyline,
  ZoomControl,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

function App() {
  const [rainfall, setRainfall] = useState(100);
  const [floodData, setFloodData] = useState(null);
  const [campusData, setCampusData] = useState(null);
  const [timeIndex, setTimeIndex] = useState(0);
  const [route, setRoute] = useState(null);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationError, setSimulationError] = useState("");

  // Load existing campus GIS data
  useEffect(() => {
    fetch("/data/mock_campus.geojson")
      .then((response) => response.json())
      .then((data) => setCampusData(data))
      .catch((error) => {
        console.error("Error loading campus data:", error);
      });
  }, []);

  // Existing flood simulation API
  async function simulateFlood() {
  setSimulationLoading(true);
  setSimulationError("");

  try {
    const response = await fetch(
      `http://127.0.0.1:8000/simulate?rainfall_mm=${rainfall}`
    );

    if (!response.ok) {
      throw new Error(`Simulation API failed: ${response.status}`);
    }

    const data = await response.json();

    if (!data.timesteps || data.timesteps.length === 0) {
      throw new Error("Simulation returned no timestep data.");
    }

    setFloodData(data);
    setTimeIndex(0);
    setRoute(null);

  } catch (error) {
    console.error("Simulation error:", error);

    setSimulationError(
      "Unable to run flood simulation. Please make sure the backend is running."
    );

  } finally {
    setSimulationLoading(false);
  }
}

  // Existing evacuation API
  async function findEvacuationRoute() {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/evacuate"
    );

    if (!response.ok) {
      throw new Error(`Evacuation API failed: ${response.status}`);
    }

    const data = await response.json();

    setRoute(data);
  } catch (error) {
    console.error("Evacuation error:", error);
  }
}

  const currentStep = floodData
    ? floodData.timesteps[timeIndex]
    : null;

  const currentDepth = currentStep
    ? currentStep.max_depth_m
    : 0;

  const currentRisk = currentStep
    ? currentStep.risk_level
    : "SAFE";
  const riskClass = currentRisk.toLowerCase();

  // Mock flood polygon
  let floodPolygon = [];

  if (currentDepth > 0) {
    if (currentDepth <= 0.1) {
      floodPolygon = [
        [17.4476, 78.3917],
        [17.4480, 78.3922],
        [17.4477, 78.3925],
        [17.4473, 78.3921],
      ];
    } else if (currentDepth <= 0.25) {
      floodPolygon = [
        [17.4474, 78.3915],
        [17.4482, 78.3924],
        [17.4478, 78.3928],
        [17.4471, 78.3920],
      ];
    } else {
      floodPolygon = [
        [17.4472, 78.3912],
        [17.4484, 78.3923],
        [17.4480, 78.3930],
        [17.4470, 78.3924],
      ];
    }
  }

  

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">

        <div className="logo">

          <div className="logo-icon">
            🌊
          </div>

          <div>
            <h1>Adaptive FloodTwin</h1>
            <span>GRIET Campus Flood Intelligence</span>
          </div>

        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          System Online
        </div>

      </header>


      {/* CONTROL PANEL */}
      <aside className="control-panel">

        <h2 className="panel-title">
          Flood Simulation
        </h2>

        <p className="panel-subtitle">
          Physics-guided campus flood monitoring
        </p>


        {/* RAINFALL */}
        <div className="section">

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

            <option value={50}>
              50 mm — Light
            </option>

            <option value={100}>
              100 mm — Moderate
            </option>

            <option value={150}>
              150 mm — Heavy
            </option>

          </select>

          <br />
          <br />

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

            <div className="section">

              <div className="section-title">
                Current Conditions
              </div>

              <div className="result-grid">

                <div className="result-card">

                  <div className="result-label">
                    Rainfall
                  </div>

                  <div className="result-value">
                    {floodData.rainfall_mm} mm
                  </div>

                </div>


                <div className="result-card">

                  <div className="result-label">
                    Time
                  </div>

                  <div className="result-value">
                    {currentStep.time_minutes} min
                  </div>

                </div>


                <div className="result-card">

                  <div className="result-label">
                    Water Depth
                  </div>

                  <div className="result-value">
                    {currentDepth.toFixed(2)} m
                  </div>

                </div>


              <div className={`result-card risk-card ${riskClass}`}>

                <div className="result-label">
                  Risk Level
                </div>

                <div className="result-value">
                  {currentRisk}
                </div>

              </div>  

              </div>

            </div>


            {/* TIMELINE */}
            <div className="section">

              <div className="section-title">
                Simulation Timeline
              </div>

              <input
                className="slider"
                type="range"
                min="0"
                max={floodData.timesteps.length - 1}
                value={timeIndex}
                onChange={(e) =>
                  setTimeIndex(Number(e.target.value))
                }
              />

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "12px",
                  color: "#6b7280",
                }}
              >

                <span>0 min</span>

                <span>
                  {floodData.duration_minutes} min
                </span>

              </div>

              <div className={`risk ${riskClass}`}>
                Risk: {currentRisk}
              </div>

            </div>


            {/* EVACUATION */}
            <div className="section">

              <div className="section-title">
                Evacuation
              </div>

              <button
                className="secondary-button"
                onClick={findEvacuationRoute}
              >
                Find Safe Evacuation Route
              </button>


              {route && (

                <div className="route-box">

                  <div className="route-title">
                    Safe Route Found
                  </div>

                  <div className="route-text">

                    <strong>From:</strong>{" "}
                    {route.start}

                    <br />

                    <strong>To:</strong>{" "}
                    {route.destination}

                    <br />

                    <strong>Path:</strong>{" "}
                    {route.route.join(" → ")}

                  </div>

                  <div className="route-risk">

                    Estimated time:{" "}
                    {route.estimated_time_minutes} min

                    <br />

                    Route risk:{" "}
                    {route.risk}

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
          center={[17.448, 78.392]}
          zoom={17}
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


          {/* CAMPUS */}
          {campusData && (
            <GeoJSON data={campusData} />
          )}


          {/* FLOOD AREA */}
          {floodPolygon.length > 0 && (

            <Polygon
              positions={floodPolygon}
              pathOptions={{
                fillOpacity: 0.5,
                color:
                  currentRisk === "LOW"
                    ? "#22c55e"
                    : currentRisk === "MEDIUM"
                    ? "#eab308"
                    : "#ef4444",
              }}
            />

          )}


          {/* EVACUATION ROUTE */}
          {route && (

            <Polyline
              positions={route.route_coordinates}
              pathOptions={{
                color: "green",
                weight: 6,
              }}
            />

          )}
          {/* MAP LEGEND */}
          <div className="map-legend">
            <div className="legend-title">Map Legend</div>

            <div className="legend-item">
              <span className="legend-color low"></span>
              Low Risk Flood Area
            </div>

            <div className="legend-item">
              <span className="legend-color medium"></span>
              Medium Risk Flood Area
            </div>

            <div className="legend-item">
              <span className="legend-color high"></span>
              High Risk Flood Area
            </div>

            <div className="legend-item">
              <span className="legend-line route"></span>
              Evacuation Route
            </div>
          </div>
        </MapContainer>

      </div>

    </div>
  );
}

export default App;