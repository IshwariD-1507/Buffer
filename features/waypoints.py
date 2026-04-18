import osmnx as ox
import networkx as nx
import heapq

# Fetch petrol pumps and map to graph nodes
def get_fuel_nodes(graph, place="Pune, India"):
    tags = {"amenity": "fuel"}
    gdf = ox.features_from_place(place, tags=tags)

    fuel_nodes = []
    for _, row in gdf.iterrows():
        try:
            lat, lon = row.geometry.y, row.geometry.x
            node = ox.distance.nearest_nodes(graph, lon, lat)
            fuel_nodes.append(node)
        except:
            continue

    return fuel_nodes


# Bitmask Dijkstra (state-space graph)
def shortest_path_with_waypoints(graph, start, end, waypoints):
    k = len(waypoints)

    pq = [(0, start, 0)]  # (cost, node, mask)
    dist = {(start, 0): 0}

    while pq:
        cost, node, mask = heapq.heappop(pq)

        # if all waypoints visited → go to end
        if mask == (1 << k) - 1:
            try:
                return cost + nx.shortest_path_length(graph, node, end, weight='length')
            except:
                continue

        for neighbor in graph.neighbors(node):
            try:
                edge_weight = min(
                    graph[node][neighbor][k]['length']
                    for k in graph[node][neighbor]
                )
            except:
                continue

            new_mask = mask

            # mark waypoint visited
            for i in range(k):
                if neighbor == waypoints[i]:
                    new_mask |= (1 << i)

            new_cost = cost + edge_weight

            if (neighbor, new_mask) not in dist or dist[(neighbor, new_mask)] > new_cost:
                dist[(neighbor, new_mask)] = new_cost
                heapq.heappush(pq, (new_cost, neighbor, new_mask))

    return float("inf")
