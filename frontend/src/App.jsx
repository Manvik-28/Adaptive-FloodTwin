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
  const [route, setRoute] = useState(null);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationError, setSimulationError] = useState("");

  useEffect(() => {
    fetch("/data/griet_campus.geojson")
      .then((response) => response.json())
      .then((data) => setCampusData(data))
      .catch((error) => {
        console.error("Error loading campus data:", error);
      });
  }, []);

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

      setFloodData(data);
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

  const currentDepth = floodData?.max_depth_m ?? 0;
  const currentRisk = floodData?.risk_level ?? "SAFE";
  const riskClass = currentRisk.toLowerCase();

  // Temporary visualization only.
  // Real raster flood visualization will replace this next.
  let floodPolygon = [];

  if (currentDepth > 0) {
    if (currentDepth <= 0.1) {
      floodPolygon = [
        [17.5200, 78.3655],
        [17.5210, 78.3670],
        [17.5203, 78.3680],
        [17.5195, 78.3665],
      ];
    } else if (currentDepth <= 0.25) {
      floodPolygon = [
        [17.5197, 78.3650],
        [17.5215, 78.3672],
        [17.5205, 78.3685],
        [17.5192, 78.3662],
      ];
    } else {
      floodPolygon = [
        [17.5193, 78.3645],
        [17.5220, 78.3670],
        [17.5210, 78.3690],
        [17.5188, 78.3660],
      ];
    }
  }

  return (
    <div className="app">

      <header className="header">
        <div className="logo">
          <div className="logo-icon">🌊</div>

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

      <aside className="control-panel">

        <h2 className="panel-title">
          Flood Simulation
        </h2>

        <p className="panel-subtitle">
          Physics-guided campus flood monitoring
        </p>

        <div className="section">

          <div className="section-title">
            Rainfall Scenario
          </div>

          <select
            className="select"
            value={rainfall}
            onChange={(e) => setRainfall(Number(e.target.value))}
          >
            <option value={50}>50 mm — Light</option>
            <option value={100}>100 mm — Moderate</option>
            <option value={150}>150 mm — Heavy</option>
            <option value={200}>200 mm — Extreme</option>
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
                    Water Depth
                  </div>

                  <div className="result-value">
                    {currentDepth.toFixed(3)} m
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

            <div className="section">

              <div className="section-title">
                Simulation Result
              </div>

              <div className="result-card">

                <div className="result-label">
                  Mean Water Depth
                </div>

                <div className="result-value">
                  {floodData.mean_depth_m?.toFixed(3)} m
                </div>

              </div>

              <div className={`risk ${riskClass}`}>
                Risk: {currentRisk}
              </div>

            </div>

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

          {campusData && (
            <GeoJSON data={campusData} />
          )}

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

          {route && (
            <Polyline
              positions={route.route_coordinates}
              pathOptions={{
                color: "green",
                weight: 6,
              }}
            />
          )}

        </MapContainer>

        <div className="map-legend">

          <div className="legend-title">
            Map Legend
          </div>

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

          <div className="legend-line route"></div>
          Evacuation Route

        </div>

      </div>

    </div>
  );
}

export default App;