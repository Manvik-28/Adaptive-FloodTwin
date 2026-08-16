def find_route(start, destination):

    route = [
        start,
        "Building-B",
        "Road-2",
        "Safe-Zone"
    ]

    route_coordinates = [
        [17.44755, 78.39155],  # Building-A
        [17.44825, 78.39245],  # Building-B
        [17.44855, 78.39270],  # Road-2
        [17.44880, 78.39300],  # Safe-Zone
    ]

    return {
        "start": start,
        "destination": destination,
        "route": route,
        "route_coordinates": route_coordinates,
        "estimated_time_minutes": 8,
        "risk": "low"
    }


if __name__ == "__main__":

    result = find_route("Building-A", "Safe-Zone")

    print(result)