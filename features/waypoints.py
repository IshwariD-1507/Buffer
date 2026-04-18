import osmnx as ox
import networkx as nx

# Fetch petrol pumps and map to graph nodes
def get_fuel_nodes(graph, place="Pune, India"):
    tags = {"amenity": "fuel"}
    gdf = ox.features_from_place(place, tags=tags)

    fuel_nodes = []

    for _, row in gdf.iterrows():
        try:
            lat = row.geometry.y
            lon = row.geometry.x

            node = ox.distance.nearest_nodes(graph, lon, lat)
            fuel_nodes.append(node)

        except:
            continue

    return fuel_nodes


# Route via waypoints (safe version)
def route_with_waypoints(graph, start, end, waypoints):
    path = []
    current = start

    for wp in waypoints:
        segment = nx.shortest_path(graph, current, wp, weight='length')
        path.extend(segment[:-1])
        current = wp

    final_segment = nx.shortest_path(graph, current, end, weight='length')
    path.extend(final_segment)

    return path
