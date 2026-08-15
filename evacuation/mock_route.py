def find_route(start, destination):

    route = [
        start,
        "Building-B",
        "Road-2",
        "Safe-Zone"
    ]

    return {
        "start": start,
        "destination": destination,
        "route": route,
        "estimated_time_minutes": 8,
        "risk": "low"
    }


if __name__ == "__main__":

    result = find_route("Building-A", "Safe-Zone")

    print(result)