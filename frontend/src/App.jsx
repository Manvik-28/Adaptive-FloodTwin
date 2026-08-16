import { useEffect, useState } from "react";

import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Polygon,
  Polyline,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

function App() {
  const [rainfall, setRainfall] = useState(100);
  const [floodData, setFloodData] = useState(null);
  const [campusData, setCampusData] = useState(null);
  const [timeIndex, setTimeIndex] = useState(0);
  const [route, setRoute] = useState(null);

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
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/simulate?rainfall_mm=${rainfall}`
      );

      const data = await response.json();

      setFloodData(data);
      setTimeIndex(0);
      setRoute(null);
    } catch (error) {
      console.error("Simulation error:", error);

      // Temporary fallback so the frontend can still be demonstrated
      const fallback = {
        rainfall_mm: rainfall,
        duration_minutes: 60,
        timesteps: [
          {
            time_minutes: 0,
            max_depth_m: 0,
            risk_level: "SAFE",
          },
          {
            time_minutes: 15,
            max_depth_m: rainfall === 50 ? 0.05 : rainfall === 100 ? 0.12 : 0.2,
            risk_level: rainfall === 50 ? "LOW" : rainfall === 100 ? "MEDIUM" : "HIGH",
          },
          {
            time_minutes: 30,
            max_depth_m: rainfall === 50 ? 0.08 : rainfall === 100 ? 0.2 : 0.35,
            risk_level: rainfall === 50 ? "LOW" : rainfall === 100 ? "MEDIUM" : "HIGH",
          },
          {
            time_minutes: 45,
            max_depth_m: rainfall === 50 ? 0.1 : rainfall === 100 ? 0.28 : 0.45,
            risk_level: rainfall === 50 ? "LOW" : rainfall === 100 ? "HIGH" : "HIGH",
          },
          {
            time_minutes: 60,
            max_depth_m: rainfall === 50 ? 0.12 : rainfall === 100 ? 0.35 : 0.55,
            risk_level: rainfall === 50 ? "LOW" : rainfall === 100 ? "HIGH" : "CRITICAL",
          },
        ],
      };

      setFloodData(fallback);
      setTimeIndex(0);
      setRoute(null);
    }
  }

  // Existing evacuation API
  async function findEvacuationRoute() {
    try {
      const response = await fetch("http://127.0.0.1:8000/evacuate");

      const data = await response.json();

      setRoute(data);
    } catch (error) {
      console.error("Evacuation error:", error);

      // Temporary frontend fallback
      setRoute({
        start: "Building-A",
        destination: "Safe-Zone",
        route: ["Building-A", "Building-B", "Road-2", "Safe-Zone"],
        estimated_time_minutes: 8,
        risk: "low",
      });
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

  // Existing mock route coordinates
  const mockRouteCoordinates = [
    [17.4475, 78.3915],
    [17.4480, 78.3920],
    [17.4485, 78.3925],
    [17.4488, 78.3930],
  ];

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
          >
            Run Flood Simulation
          </button>

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


                <div className="result-card">

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

              <div className="risk">
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
          style={{
            height: "100%",
            width: "100%",
          }}
        >

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
                color: "blue",
              }}
            />

          )}


          {/* EVACUATION ROUTE */}
          {route && (

            <Polyline
              positions={mockRouteCoordinates}
              pathOptions={{
                color: "green",
                weight: 6,
              }}
            />

          )}

        </MapContainer>

      </div>

    </div>
  );
}

export default App;