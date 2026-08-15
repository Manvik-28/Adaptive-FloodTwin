import { useState, useEffect } from "react";

import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Polygon,
  Polyline
} from "react-leaflet";

import "leaflet/dist/leaflet.css";


function App() {

  const [rainfall, setRainfall] = useState(100);

  const [floodData, setFloodData] = useState(null);

  const [campusData, setCampusData] = useState(null);

  const [timeIndex, setTimeIndex] = useState(0);

  const [route, setRoute] = useState(null);


  // Load campus GIS data

  useEffect(() => {

    fetch("/data/mock_campus.geojson")
      .then((response) => response.json())
      .then((data) => setCampusData(data))
      .catch((error) => {
        console.error("Error loading campus data:", error);
      });

  }, []);


  // Run flood simulation

  async function simulateFlood() {

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/simulate?rainfall_mm=${rainfall}`
      );

      const data = await response.json();

      setFloodData(data);

      // Start from the beginning of the simulation
      setTimeIndex(0);

      // Clear old route
      setRoute(null);

    } catch (error) {

      console.error("Simulation error:", error);

    }

  }


  // Request evacuation route

  async function findEvacuationRoute() {

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/evacuate"
      );

      const data = await response.json();

      setRoute(data);

    } catch (error) {

      console.error("Evacuation error:", error);

    }

  }


  // Current simulation timestep

  const currentStep =
    floodData
      ? floodData.timesteps[timeIndex]
      : null;


  const currentDepth =
    currentStep
      ? currentStep.max_depth_m
      : 0;


  const currentRisk =
    currentStep
      ? currentStep.risk_level
      : "SAFE";


  /*
   * Mock flood polygon.
   *
   * It grows according to the current simulated
   * water depth.
   */

  let floodPolygon = [];


  if (currentDepth > 0) {

    if (currentDepth <= 0.10) {

      floodPolygon = [
        [17.4476, 78.3917],
        [17.4480, 78.3922],
        [17.4477, 78.3925],
        [17.4473, 78.3921]
      ];

    }

    else if (currentDepth <= 0.25) {

      floodPolygon = [
        [17.4474, 78.3915],
        [17.4482, 78.3924],
        [17.4478, 78.3928],
        [17.4471, 78.3920]
      ];

    }

    else {

      floodPolygon = [
        [17.4472, 78.3912],
        [17.4484, 78.3923],
        [17.4480, 78.3930],
        [17.4470, 78.3924]
      ];

    }

  }


  /*
   * Mock evacuation route.
   */

  const mockRouteCoordinates = [

    [17.4475, 78.3915],

    [17.4480, 78.3920],

    [17.4485, 78.3925],

    [17.4488, 78.3930]

  ];


  return (

    <div
      style={{
        height: "100vh",
        width: "100%"
      }}
    >


      {/* CONTROL PANEL */}

      <div
        style={{
          position: "absolute",

          zIndex: 1000,

          background: "white",

          padding: "18px",

          margin: "15px",

          width: "280px",

          borderRadius: "10px",

          boxShadow: "0 2px 10px rgba(0,0,0,0.3)"
        }}
      >

        <h2>
          Adaptive FloodTwin
        </h2>


        <p>
          Campus Flood Simulation
        </p>


        {/* Rainfall */}

        <label>
          Rainfall scenario:
        </label>


        <br />


        <select

          value={rainfall}

          onChange={(e) =>
            setRainfall(Number(e.target.value))
          }

          style={{
            width: "100%",
            padding: "7px",
            marginTop: "5px"
          }}

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


        {/* Simulation button */}

        <button

          onClick={simulateFlood}

          style={{
            width: "100%",
            padding: "9px"
          }}

        >

          Simulate Flood

        </button>


        {/* RESULTS */}

        {floodData && (

          <div>

            <hr />


            <p>
              <b>Rainfall:</b>{" "}
              {floodData.rainfall_mm} mm
            </p>


            <p>
              <b>Time:</b>{" "}
              {currentStep.time_minutes} min
            </p>


            <p>
              <b>Water depth:</b>{" "}
              {currentDepth.toFixed(2)} m
            </p>


            <p>
              <b>Risk:</b>{" "}
              {currentRisk}
            </p>


            {/* TIME SLIDER */}

            <label>
              Simulation time:
            </label>


            <input

              type="range"

              min="0"

              max={floodData.timesteps.length - 1}

              value={timeIndex}

              onChange={(e) =>
                setTimeIndex(Number(e.target.value))
              }

              style={{
                width: "100%"
              }}

            />


            <div
              style={{
                display: "flex",
                justifyContent: "space-between"
              }}
            >

              <span>
                0 min
              </span>

              <span>
                {floodData.duration_minutes} min
              </span>

            </div>


            <br />


            {/* EVACUATION */}

            <button

              onClick={findEvacuationRoute}

              style={{
                width: "100%",
                padding: "9px"
              }}

            >

              Find Safe Evacuation Route

            </button>


            {route && (

              <div>

                <p>
                  <b>Route:</b>
                </p>

                <p>
                  {route.route.join(" → ")}
                </p>

                <p>
                  Estimated time:{" "}
                  {route.estimated_time_minutes} min
                </p>

                <p>
                  Route risk: {route.risk}
                </p>

              </div>

            )}

          </div>

        )}

      </div>


      {/* MAP */}

      <MapContainer

        center={[17.448, 78.392]}

        zoom={17}

        style={{
          height: "100%",
          width: "100%"
        }}

      >


        <TileLayer

          attribution="&copy; OpenStreetMap contributors"

          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

        />


        {/* CAMPUS */}

        {campusData && (

          <GeoJSON
            data={campusData}
          />

        )}


        {/* FLOOD */}

        {floodPolygon.length > 0 && (

          <Polygon

            positions={floodPolygon}

            pathOptions={{
              fillOpacity: 0.5,
              color: "blue"
            }}

          />

        )}


        {/* EVACUATION ROUTE */}

        {route && (

          <Polyline

            positions={mockRouteCoordinates}

            pathOptions={{
              color: "green",
              weight: 6
            }}

          />

        )}


      </MapContainer>

    </div>

  );

}


export default App;