import osmnx as ox
import networkx as nx
import heapq


# 🔹 Fetch petrol pumps and map to graph nodes
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


# 🔹 Bitmask Dijkstra WITH PATH RECONSTRUCTION
def shortest_path_with_waypoints(graph, start, end, waypoints):

    if not waypoints:
        return nx.shortest_path(graph, start, end, weight='length')

    k = len(waypoints)

    pq = [(0, start, 0)]
    dist = {(start, 0): 0}
    parent = {}

    while pq:
        cost, node, mask = heapq.heappop(pq)

        # If all visited → go to end
        if mask == (1 << k) - 1:
            try:
                final_path = nx.shortest_path(graph, node, end, weight='length')

                # reconstruct previous path
                path = []
                cur = (node, mask)

                while cur in parent:
                    node_id, m = cur
                    path.append(node_id)
                    cur = parent[cur]

                path.append(start)
                path.reverse()

                return path + final_path[1:]

            except:
                continue

        for neighbor in graph.neighbors(node):
            try:
                edge_weight = min(
                    graph[node][neighbor][key]['length']
                    for key in graph[node][neighbor]
                )
            except:
                continue

            new_mask = mask

            for i in range(k):
                if neighbor == waypoints[i]:
                    new_mask |= (1 << i)

            new_cost = cost + edge_weight

            if (neighbor, new_mask) not in dist or dist[(neighbor, new_mask)] > new_cost:
                dist[(neighbor, new_mask)] = new_cost
                parent[(neighbor, new_mask)] = (node, mask)
                heapq.heappush(pq, (new_cost, neighbor, new_mask))

    return []
