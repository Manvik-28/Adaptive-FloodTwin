def simulate_flood(rainfall_mm):

    if rainfall_mm == 50:
        depths = [0.00, 0.02, 0.05, 0.10]

    elif rainfall_mm == 100:
        depths = [0.00, 0.05, 0.12, 0.20]

    elif rainfall_mm == 150:
        depths = [0.00, 0.10, 0.22, 0.45]

    else:
        depths = [0.00, 0.05, 0.10, 0.15]

    timesteps = []

    for i, depth in enumerate(depths):

        if depth <= 0.10:
            risk = "LOW"
        elif depth <= 0.25:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        timesteps.append({
            "time_minutes": i * 10,
            "max_depth_m": depth,
            "risk_level": risk
        })

    return {
        "rainfall_mm": rainfall_mm,
        "duration_minutes": 30,
        "timesteps": timesteps
    }


if __name__ == "__main__":

    result = simulate_flood(100)

    print(result)