import sys
from pathlib import Path

import numpy as np
import rasterio

from runoff import calculate_runoff
from flow_routing import route_water


RAINFALL_MM = (
    float(sys.argv[1])
    if len(sys.argv) > 1
    else 150.0
)

DURATION_MINUTES = (
    float(sys.argv[2])
    if len(sys.argv) > 2
    else 30.0
)

OUTPUT_PATH = (
    Path("data/processed")
    /
    (
        f"final_flood_depth_"
        f"{int(RAINFALL_MM)}mm_"
        f"{int(DURATION_MINUTES)}min.tif"
    )
)

DEM_PATH = "data/processed/final_dem.tif"


# ============================================================
# 1. Rainfall -> runoff per cell
# ============================================================

runoff = calculate_runoff(
    rainfall_mm=RAINFALL_MM,
    duration_minutes=DURATION_MINUTES
)


# ============================================================
# 2. Runoff -> D8 flow routing -> storage -> drainage
# ============================================================

routing = route_water(
    runoff_volume_m3=runoff["runoff_volume_m3"],
    rainfall_mm=RAINFALL_MM,
    duration_minutes=DURATION_MINUTES
)

flood_depth = routing["flood_depth_m"]


# ============================================================
# 3. Save final flood depth raster
# ============================================================

with rasterio.open(DEM_PATH) as src:

    profile = src.profile.copy()

    profile.update(
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="deflate"
    )

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **profile
    ) as dst:

        dst.write(
            flood_depth.astype(np.float32),
            1
        )


# ============================================================
# 4. Statistics
# ============================================================

valid = flood_depth[
    np.isfinite(flood_depth)
]

print()
print("FLOW-ROUTED FLOOD SIMULATION")
print("================================")

print(
    "Rainfall:",
    RAINFALL_MM,
    "mm"
)

print(
    "Duration:",
    DURATION_MINUTES,
    "minutes"
)

print(
    "Effective rainfall:",
    runoff["effective_rainfall_mm"],
    "mm"
)

print(
    "Output:",
    OUTPUT_PATH
)

print()
print("RUNOFF")
print("--------------------------------")

print(
    "Runoff min/max:",
    float(runoff["runoff_mm"].min()),
    float(runoff["runoff_mm"].max()),
    "mm"
)

print(
    "Total runoff:",
    routing["total_runoff_m3"],
    "m3"
)

print()
print("DRAINAGE")
print("--------------------------------")

print(
    "Drainage capacity:",
    "10.0 m3 per drainage cell per event"
)

print(
    "Total drainage removed:",
    routing["total_drainage_removed_m3"],
    "m3"
)

print()
print("PONDING")
print("--------------------------------")

print(
    "Total stored water:",
    routing["total_ponded_m3"],
    "m3"
)
print(
    "Flood depth min/max:",
    float(valid.min()),
    float(valid.max()),
    "m"
)

print(
    "Mean flood depth:",
    float(valid.mean()),
    "m"
)

print(
    "Cells > 0.05 m:",
    int(np.sum(flood_depth > 0.05))
)

print(
    "Cells > 0.10 m:",
    int(np.sum(flood_depth > 0.10))
)

print(
    "Cells > 0.20 m:",
    int(np.sum(flood_depth > 0.20))
)

print(
    "Cells > 0.30 m:",
    int(np.sum(flood_depth > 0.30))
)

print(
    "Cells > 0.50 m:",
    int(np.sum(flood_depth > 0.50))
)

print()
print("DONE")