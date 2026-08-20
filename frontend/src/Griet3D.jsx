import { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  PerspectiveCamera,
} from "@react-three/drei";

const API = "http://127.0.0.1:8000";

const ROUTE_OFFSET = 0.10;


/* =========================================================
   TERRAIN
   ========================================================= */

function Terrain({ dem }) {

  const geometry = useMemo(() => {

    const aspect = dem.width / dem.height;

    const width = 12;
    const height = width / aspect;

    const geometry = new THREE.PlaneGeometry(
      width,
      height,
      dem.width - 1,
      dem.height - 1
    );

    const positions = geometry.attributes.position;

    for (let i = 0; i < positions.count; i++) {

      const x = i % dem.width;
      const y = Math.floor(i / dem.width);

      if (dem.valid[y][x]) {

        positions.setZ(
          i,
          dem.heights[y][x] * 2.5
        );

      } else {

        positions.setZ(i, 0);

      }
    }

    const oldIndices = geometry.index.array;
    const validIndices = [];

    for (
      let i = 0;
      i < oldIndices.length;
      i += 3
    ) {

      const a = oldIndices[i];
      const b = oldIndices[i + 1];
      const c = oldIndices[i + 2];

      const ax = a % dem.width;
      const ay = Math.floor(a / dem.width);

      const bx = b % dem.width;
      const by = Math.floor(b / dem.width);

      const cx = c % dem.width;
      const cy = Math.floor(c / dem.width);

      if (
        dem.valid[ay][ax] &&
        dem.valid[by][bx] &&
        dem.valid[cy][cx]
      ) {
        validIndices.push(a, b, c);
      }
    }

    geometry.setIndex(validIndices);
    geometry.computeVertexNormals();

    return geometry;

  }, [dem]);


  return (
    <mesh
      geometry={geometry}
      rotation={[-Math.PI / 2, 0, 0]}
    >
      <meshStandardMaterial
        color="#5f8f4f"
        side={THREE.DoubleSide}
        roughness={0.9}
      />
    </mesh>
  );
}


/* =========================================================
   FLOOD WATER
   ========================================================= */

function FloodWater({ dem, flood }) {

  const geometry = useMemo(() => {

    if (!flood) {
      return null;
    }

    const aspect = dem.width / dem.height;

    const width = 12;
    const height = width / aspect;

    const geometry = new THREE.PlaneGeometry(
      width,
      height,
      dem.width - 1,
      dem.height - 1
    );

    const positions = geometry.attributes.position;
    const oldIndices = geometry.index.array;

    // Put every water vertex at:
    // terrain height + actual flood depth
    for (let i = 0; i < positions.count; i++) {

      const x = i % dem.width;
      const y = Math.floor(i / dem.width);

      if (
        !dem.valid[y]?.[x] ||
        !flood.valid[y]?.[x]
      ) {
        positions.setZ(i, -100);
        continue;
      }

      const terrainHeight =
        dem.heights[y][x] * 2.5;

      const depth =
        Math.max(0, flood.depths[y][x]);

      positions.setZ(
        i,
        terrainHeight + depth * 2.5
      );
    }

    /*
     * Render a triangle when its average flood depth
     * is meaningful.
     *
     * 0.20 m gives a visible flooded region without
     * covering the entire terrain.
     */
    const WATER_THRESHOLD = 0.20;

    const newIndices = [];

    for (
      let i = 0;
      i < oldIndices.length;
      i += 3
    ) {

      const a = oldIndices[i];
      const b = oldIndices[i + 1];
      const c = oldIndices[i + 2];

      const ax = a % dem.width;
      const ay = Math.floor(a / dem.width);

      const bx = b % dem.width;
      const by = Math.floor(b / dem.width);

      const cx = c % dem.width;
      const cy = Math.floor(c / dem.width);

      if (
        !dem.valid[ay]?.[ax] ||
        !dem.valid[by]?.[bx] ||
        !dem.valid[cy]?.[cx] ||
        !flood.valid[ay]?.[ax] ||
        !flood.valid[by]?.[bx] ||
        !flood.valid[cy]?.[cx]
      ) {
        continue;
      }

      const depthA = Math.max(
        0,
        flood.depths[ay][ax]
      );

      const depthB = Math.max(
        0,
        flood.depths[by][bx]
      );

      const depthC = Math.max(
        0,
        flood.depths[cy][cx]
      );

      if (
        depthA >= WATER_THRESHOLD ||
        depthB >= WATER_THRESHOLD ||
        depthC >= WATER_THRESHOLD
      ) {
        newIndices.push(a, b, c);
      }
    }

    geometry.setIndex(newIndices);

    geometry.computeVertexNormals();

    return geometry;

  }, [dem, flood]);


  if (!geometry || geometry.index.count === 0) {
    return null;
  }


  return (
    <mesh
      geometry={geometry}
      rotation={[-Math.PI / 2, 0, 0]}
    >

      <meshStandardMaterial
        color="#1976d2"
        transparent
        opacity={0.68}
        roughness={0.15}
        metalness={0.05}
        side={THREE.DoubleSide}
      />

    </mesh>
  );
}


/* =========================================================
   DEM HEIGHT SAMPLING
   ========================================================= */

function sampleTerrainHeight(
  dem,
  lat,
  lon
) {

  const bounds = dem.bounds;

  const u =
    (lon - bounds.west) /
    (bounds.east - bounds.west);

  const v =
    (bounds.north - lat) /
    (bounds.north - bounds.south);

  const gridX =
    Math.max(
      0,
      Math.min(
        dem.width - 1,
        u * (dem.width - 1)
      )
    );

  const gridY =
    Math.max(
      0,
      Math.min(
        dem.height - 1,
        v * (dem.height - 1)
      )
    );

  const x0 = Math.floor(gridX);
  const y0 = Math.floor(gridY);

  const x1 = Math.min(
    x0 + 1,
    dem.width - 1
  );

  const y1 = Math.min(
    y0 + 1,
    dem.height - 1
  );

  const tx = gridX - x0;
  const ty = gridY - y0;

  const h00 =
    dem.heights[y0][x0];

  const h10 =
    dem.heights[y0][x1];

  const h01 =
    dem.heights[y1][x0];

  const h11 =
    dem.heights[y1][x1];

  const top =
    h00 * (1 - tx) +
    h10 * tx;

  const bottom =
    h01 * (1 - tx) +
    h11 * tx;

  const normalizedHeight =
    top * (1 - ty) +
    bottom * ty;

  return normalizedHeight * 2.5;
}


/* =========================================================
   EVACUATION ROUTE
   ========================================================= */

function EvacuationRoute({
  route,
  dem
}) {

  if (
    !route ||
    route.length < 2 ||
    !dem
  ) {
    return null;
  }


  const geometry = useMemo(() => {

    const aspect =
      dem.width / dem.height;

    const width = 12;
    const height =
      width / aspect;

    const points = [];

    for (const [lat, lon] of route) {

      const u =
        (lon - dem.bounds.west) /
        (dem.bounds.east - dem.bounds.west);

      const v =
        (dem.bounds.north - lat) /
        (dem.bounds.north - dem.bounds.south);

      const x =
        u * width -
        width / 2;

      const z =
        v * height -
        height / 2;

      const terrainY =
        sampleTerrainHeight(
          dem,
          lat,
          lon
        );

      points.push(
        new THREE.Vector3(
          x,
          terrainY + ROUTE_OFFSET,
          z
        )
      );
    }

    return new THREE.BufferGeometry()
      .setFromPoints(points);

  }, [route, dem]);


  return (
    <line geometry={geometry}>

      <lineBasicMaterial
        color="#00ff00"
        linewidth={3}
      />

    </line>
  );
}


/* =========================================================
   START / DESTINATION MARKERS
   ========================================================= */

function Marker({
  position,
  color
}) {

  return (
    <mesh position={position}>

      <sphereGeometry
        args={[0.14, 16, 16]}
      />

      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={1}
      />

    </mesh>
  );
}


/* =========================================================
   SCENE
   ========================================================= */

function Scene({
  dem,
  flood,
  evacuation
}) {

  const route =
    evacuation?.route_coordinates || [];


  const convertPoint = (point) => {

    const [lat, lon] = point;

    const u =
      (lon - dem.bounds.west) /
      (dem.bounds.east - dem.bounds.west);

    const v =
      (dem.bounds.north - lat) /
      (dem.bounds.north - dem.bounds.south);

    const x =
      u * 12 -
      6;

    const z =
      v * (12 / (dem.width / dem.height)) -
      (12 / (dem.width / dem.height)) / 2;

    const terrainY =
      sampleTerrainHeight(
        dem,
        lat,
        lon
      );

    return [
      x,
      terrainY + ROUTE_OFFSET,
      z
    ];
  };


  const startPosition =
    route.length > 0
      ? convertPoint(route[0])
      : [0, 0, 0];


  const destinationPosition =
    route.length > 0
      ? convertPoint(
          route[route.length - 1]
        )
      : [0, 0, 0];


  return (
    <>

      <PerspectiveCamera
        makeDefault
        position={[8, 7, 8]}
      />

      <ambientLight intensity={1.1} />

      <directionalLight
        position={[5, 10, 5]}
        intensity={2}
      />

      <directionalLight
        position={[-5, 6, -5]}
        intensity={0.8}
      />

      <Terrain dem={dem} />

      {flood && (
        <FloodWater
          dem={dem}
          flood={flood}
        />
      )}

      {route.length > 1 && (
        <>
          <EvacuationRoute
            route={route}
            dem={dem}
          />

          <Marker
            position={startPosition}
            color="#00ff00"
          />

          <Marker
            position={destinationPosition}
            color="#ff0000"
          />
        </>
      )}

      <OrbitControls
        enableDamping
        dampingFactor={0.08}
        minDistance={5}
        maxDistance={25}
      />

    </>
  );
}


/* =========================================================
   MAIN COMPONENT
   ========================================================= */

export default function Griet3D({
  rainfall = 150,
  duration=30
}) {

  const [dem, setDem] =
    useState(null);

  const [flood, setFlood] =
    useState(null);

  const [evacuation, setEvacuation] =
    useState(null);

  const [loading, setLoading] =
    useState(true);


  /* -----------------------------
     Load DEM
  ----------------------------- */

  useEffect(() => {

    fetch(`${API}/dem`)
      .then((response) => {

        if (!response.ok) {
          throw new Error(
            `DEM request failed: ${response.status}`
          );
        }

        return response.json();

      })
      .then((data) => {

        setDem(data);

      })
      .catch((error) => {

        console.error(
          "DEM loading failed:",
          error
        );

      });

  }, []);


  /* -----------------------------
     Load flood + evacuation
  ----------------------------- */

  useEffect(() => {

  setLoading(true);

  Promise.all([

    fetch(
      `${API}/flood-grid?rainfall_mm=${rainfall}&duration_minutes=${duration}`
    ).then((response) => {

      if (!response.ok) {
        throw new Error(
          `Flood grid failed: ${response.status}`
        );
      }

      return response.json();

    }),

    fetch(
      `${API}/evacuate?rainfall_mm=${rainfall}&duration_minutes=${duration}`
    ).then((response) => {

      if (!response.ok) {
        throw new Error(
          `Evacuation failed: ${response.status}`
        );
      }

      return response.json();

    })

  ])
    .then(([floodData, evacuationData]) => {

      setFlood(floodData);
      setEvacuation(evacuationData);

    })
    .catch((error) => {

      console.error(
        "3D simulation loading failed:",
        error
      );

      setFlood(null);
      setEvacuation(null);

    })
    .finally(() => {

      setLoading(false);

    });

}, [rainfall, duration]);


  if (!dem) {

    return (
      <div
        style={{
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#111827",
          color: "white",
          fontFamily: "Arial, sans-serif",
        }}
      >
        Loading GRIET terrain...
      </div>
    );

  }


  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
      }}
    >

      <Canvas>

        <Scene
          dem={dem}
          flood={flood}
          evacuation={evacuation}
        />

      </Canvas>


      <div
        style={{
          position: "absolute",
          top: 15,
          left: 15,
          padding: "10px 14px",
          borderRadius: 8,
          background: "rgba(17, 24, 39, 0.85)",
          color: "white",
          fontFamily: "Arial, sans-serif",
          fontSize: 13,
          zIndex: 10,
        }}
      >

        <strong>
          3D Flood Twin
        </strong>

        <div style={{ marginTop: 4 }}>
          Rainfall: {rainfall} mm
        </div>

        <div style={{ marginTop: 2 }}>
          Duration: {duration} min
        </div>

        {flood && (
          <div style={{ marginTop: 2 }}>
            Max depth:{" "}
            {flood.max_depth_m.toFixed(3)} m
          </div>
        )}

      </div>


      <div
        style={{
          position: "absolute",
          bottom: 15,
          left: 15,
          padding: "8px 12px",
          borderRadius: 7,
          background: "rgba(17, 24, 39, 0.85)",
          color: "white",
          fontFamily: "Arial, sans-serif",
          fontSize: 12,
        }}
      >
        Green = evacuation route
      </div>


      {loading && (
        <div
          style={{
            position: "absolute",
            bottom: 15,
            right: 15,
            padding: "8px 12px",
            borderRadius: 7,
            background: "rgba(17, 24, 39, 0.85)",
            color: "white",
            fontFamily: "Arial, sans-serif",
            fontSize: 12,
          }}
        >
          Updating flood response...
        </div>
      )}

    </div>
  );
}