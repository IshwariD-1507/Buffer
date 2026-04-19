import osmnx as ox
import heapq

# ============================================================
# features/waypoints.py  — T3
# Waypoints with Bitmask DP + Dijkstra over augmented state
# state = (current_node, bitmask of visited waypoints)
# dist[node][mask] — run Dijkstra over this augmented state
# for k waypoints: 2^k states per node
# ============================================================

def get_petrol_pump_nodes(graph, city_name="Pune, India"):
    """
    Fetch all petrol pump locations from OSMnx and snap them
    to the nearest nodes in the road graph.

    Returns a list of node IDs (from graph) that are closest
    to actual petrol pump coordinates.
    """
    print(f"  Fetching petrol pumps for '{city_name}'...")
    try:
        pumps_gdf = ox.features_from_place(city_name, tags={"amenity": "fuel"})  # gets petrol pump POI data from OpenStreetMap
    except Exception as e:
        print(f"  [WARN] Could not fetch petrol pumps: {e}")
        return []

    pump_nodes = []  # will hold the list of nearest graph node IDs for each pump

    for _, row in pumps_gdf.iterrows():
        try:
            geom = row.geometry
            # For polygon shapes (like large petrol stations), use centroid
            if geom.geom_type == "Point":
                lat, lon = geom.y, geom.x   # extract lat/lon from Point geometry
            else:
                lat, lon = geom.centroid.y, geom.centroid.x  # extract lat/lon from centroid of polygon
            # Snap the pump coordinate to the nearest road network node
            nearest = ox.distance.nearest_nodes(graph, lon, lat)  # nearest_nodes(graph, X=lon, Y=lat)
            pump_nodes.append(nearest)   # add the nearest road node to our list
        except Exception:
            continue   # skip any pump that can't be snapped (e.g. bad geometry)

    # Remove duplicate nodes (two pumps might snap to the same intersection)
    unique_pump_nodes = []
    seen = set()
    for n in pump_nodes:
        if n not in seen:
            unique_pump_nodes.append(n)
            seen.add(n)

    print(f"  Found {len(unique_pump_nodes)} unique petrol pump nodes.")
    return unique_pump_nodes


def dijkstra_with_waypoints(graph, start, end, waypoint_nodes, weight='weight'):
    """
    Dijkstra over an augmented state-space using bitmask DP.

    State  : (current_node, visited_mask)
             visited_mask is a bitmask where bit i = 1 means waypoint i has been visited
    dist   : dict mapping (node, mask) -> best known cost to reach that state
    Goal   : reach `end` node with ALL waypoints visited (mask == full_mask)

    Args:
        graph         : road network (NetworkX MultiDiGraph)
        start         : starting node ID
        end           : destination node ID
        waypoint_nodes: list of node IDs that must be visited (petrol pumps)
        weight        : edge attribute to use as cost (default 'weight' from weights.py)

    Returns:
        path  : list of node IDs forming the shortest waypoint-covering route
        dist  : total cost of the path
    """
    k = len(waypoint_nodes)           # number of waypoints
    full_mask = (1 << k) - 1         # bitmask with all k bits set = all waypoints visited

    # Map each waypoint node to its bit index for fast lookup
    waypoint_index = {}               # {node_id: bit_position}
    for i in range(k):
        waypoint_index[waypoint_nodes[i]] = i

    # dist[(node, mask)] = minimum cost to reach `node` having visited waypoints in `mask`
    dist = {}

    # parent[(node, mask)] = (prev_node, prev_mask) for path reconstruction
    parent = {}

    # Priority queue entries: (cost, node, visited_mask)
    start_mask = 0
    # If the start node is itself a waypoint, mark it visited immediately
    if start in waypoint_index:
        start_mask = (1 << waypoint_index[start])

    pq = [(0, start, start_mask)]     # (cost, node, mask)
    dist[(start, start_mask)] = 0
    parent[(start, start_mask)] = None

    while pq:
        current_cost, current_node, current_mask = heapq.heappop(pq)  # pop lowest-cost state

        # Early exit: reached destination with all waypoints visited
        if current_node == end and current_mask == full_mask:
            break

        # Skip if we have already found a cheaper way to this state
        if dist.get((current_node, current_mask), float('inf')) < current_cost:
            continue

        # Explore all neighbours of current_node
        for neighbor in graph.neighbors(current_node):
            edge_data = graph.get_edge_data(current_node, neighbor)  # get all parallel edges between the two nodes

            # Pick minimum edge weight among parallel edges (same as dijkstra.py pattern)
            min_w = float('inf')
            for d in edge_data.values():
                w = d.get(weight, d.get('length', 1))  # fall back to 'length' if 'weight' not set yet
                if w < min_w:
                    min_w = w

            new_cost = current_cost + min_w  # total cost to reach neighbor via this edge

            # Compute new mask: if neighbor is a waypoint, set its bit
            new_mask = current_mask
            if neighbor in waypoint_index:
                new_mask = current_mask | (1 << waypoint_index[neighbor])  # bitwise OR sets the waypoint's bit

            state = (neighbor, new_mask)

            # Relaxation: only update if this path is strictly cheaper
            if new_cost < dist.get(state, float('inf')):
                dist[state] = new_cost
                parent[state] = (current_node, current_mask)  # remember where we came from
                heapq.heappush(pq, (new_cost, neighbor, new_mask))  # push improved state to queue

    # --------------------------------------------------------
    # Path reconstruction — trace back through parent map
    # --------------------------------------------------------
    # Find the best end state (end node with full mask visited)
    best_cost = dist.get((end, full_mask), float('inf'))

    if best_cost == float('inf'):
        print("  [WARN] Could not find a route that visits all waypoints.")
        print("         Falling back to direct Dijkstra (no waypoints).")
        return _fallback_dijkstra(graph, start, end, weight)

    path = []
    state = (end, full_mask)
    while state is not None:
        node, mask = state
        path.append(node)           # collect nodes in reverse order
        state = parent[state]

    path.reverse()  # reverse to get start -> end order
    return path, best_cost


def _fallback_dijkstra(graph, start, end, weight='weight'):
    """
    Plain Dijkstra fallback (mirrors graph/dijkstra.py exactly).
    Used when not all waypoints can be visited.
    """
    pq = [(0, start)]
    distances = {node: float('inf') for node in graph.nodes}
    distances[start] = 0
    parent = {node: None for node in graph.nodes}

    while pq:
        current_distance, current_node = heapq.heappop(pq)
        if current_node == end:
            break
        for neighbor in graph.neighbors(current_node):
            edge_data = graph.get_edge_data(current_node, neighbor)
            min_weight = min([d.get(weight, d.get('length', 1)) for d in edge_data.values()])
            new_dist = current_distance + min_weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = current_node
                heapq.heappush(pq, (new_dist, neighbor))

    path = []
    node = end
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path, distances[end]
