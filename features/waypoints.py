import osmnx as ox
import heapq

# ============================================================
# features/waypoints.py  — Teammate 3
#
# DSA Concept: Bitmask DP + Dijkstra over augmented state-space
#
# CORE IDEA:
#   Normal Dijkstra tracks:  dist[node] = cheapest cost to reach node
#   Bitmask DP Dijkstra tracks:
#       dist[(node, mask)] = cheapest cost to reach node
#                            having visited exactly the waypoints
#                            whose bits are 1 in `mask`
#
#   state = (current_node, visited_mask)
#   For k waypoints: each node has 2^k possible masks
#   Goal: reach end node with full_mask = (1<<k)-1 (all k bits set)
# heapq is the priority queue data structure — same as dijkstra.py.
# ============================================================


def get_petrol_pump_nodes(graph, city_name="Pune, India"):
    """
    Fetch petrol pump locations from OpenStreetMap and snap each
    one to the nearest node in the road network graph.

    OSMnx/pandas calls are unavoidable for map data loading.
    Deduplication is done manually with a dict (no set() builtin).

    Args:
        graph     : road network (NetworkX MultiDiGraph) from loader.py
        city_name : place name string — same format as in loader.py

    Returns:
        pump_nodes : list of unique graph node IDs nearest to petrol pumps
    """
    print(f"  Fetching petrol pumps for '{city_name}'...")
    try:
        # ox.features_from_place returns a GeoDataFrame of fuel POIs
        pumps_gdf = ox.features_from_place(city_name, tags={"amenity": "fuel"})
    except Exception as e:
        print(f"  [WARN] Could not fetch petrol pumps: {e}")
        return []

    pump_nodes = []     # final list of nearest road-graph node IDs
    seen = {}           # manual dedup dict: {node_id: True}  — no set() used

    i = 0
    while i < len(pumps_gdf):
        try:
            row = pumps_gdf.iloc[i]        # access pump row by integer index
            geom = row.geometry

            # OSMnx returns Point for small POI, Polygon for large station
            if geom.geom_type == "Point":
                lat = geom.y               # latitude  is the y coordinate in OSMnx
                lon = geom.x               # longitude is the x coordinate in OSMnx
            else:
                lat = geom.centroid.y      # use polygon centroid for large stations
                lon = geom.centroid.x

            # Snap the pump coordinate to nearest road intersection
            # nearest_nodes signature: (graph, X=longitude, Y=latitude)
            nearest = ox.distance.nearest_nodes(graph, lon, lat)

            # Manual deduplication — two pumps may snap to the same intersection
            if nearest not in seen:
                seen[nearest] = True       # mark as seen
                pump_nodes.append(nearest) # add unique node to result
        except Exception:
            pass                           # skip pumps with bad geometry

        i = i + 1

    print(f"  Found {len(pump_nodes)} unique petrol pump nodes.")
    return pump_nodes


def _get_min_edge_weight(edge_data, weight):
    """
    Find the minimum weight among all parallel edges between two nodes.
    Done with a manual for-loop — no min() builtin — to show DSA logic clearly.

    Args:
        edge_data : nested dict from graph.get_edge_data(u, v)
                    e.g. {0: {'length': 50, 'weight': 65}, 1: {'length': 30, ...}}
        weight    : edge attribute key to use ('weight' after composite weights,
                    'length' as fallback — same fallback order as dijkstra.py)

    Returns:
        min_w : smallest weight value found (float)
    """
    min_w = float('inf')                   # worst starting value
    for key in edge_data:                  # iterate over parallel edge indices
        d = edge_data[key]
        if weight in d:
            w = d[weight]                  # use composite weight if available
        elif 'length' in d:
            w = d['length']                # fall back to raw road length
        else:
            w = 1                          # last resort default
        if w < min_w:
            min_w = w                      # manually track the running minimum
    return min_w


def dijkstra_with_waypoints(graph, start, end, waypoint_nodes, weight='weight'):
    """
    Dijkstra over an augmented (node, bitmask) state-space.

    ── STATE DEFINITION ──────────────────────────────────────────
    state = (node, mask)
      node : current road intersection node ID (same IDs as graph/dijkstra.py)
      mask : integer bitmask — bit i is 1 if waypoint_nodes[i] has been visited
             e.g. for 3 waypoints: mask=0b101 means pump 0 and pump 2 visited

    ── DISTANCE TABLE ────────────────────────────────────────────
    dist[(node, mask)] = best cost found so far to reach `node`
                         while having visited exactly the waypoints in `mask`.
    Sparse dict — not pre-initialised (N * 2^k entries would be too large).
    Check `if state not in dist` before reading.

    ── BITMASK UPDATE ────────────────────────────────────────────
    When we move to a neighbour that is waypoint i:
        new_mask = current_mask | (1 << i)
    Bitwise OR sets bit i without changing any other bits.

    ── GOAL ──────────────────────────────────────────────────────
    Reach (end, full_mask) where full_mask = (1 << k) - 1.

    ── RELAXATION (same pattern as dijkstra.py) ──────────────────
    new_dist = current_cost + edge_weight
    if new_dist < dist[(neighbor, new_mask)]:
        update dist and parent, push to heap

    Args:
        graph          : road network (NetworkX MultiDiGraph) — same as dijkstra.py
        start          : start node ID  — same type as start_node in run.py
        end            : end node ID    — same type as end_node in run.py
        waypoint_nodes : list of node IDs that MUST all be visited (petrol pumps)
        weight         : edge attribute key — 'weight' from apply_composite_weights()

    Returns:
        path : list of node IDs (same structure as dijkstra.py's path return)
        dist : total cost as float (same as distances[end] in dijkstra.py)
    """
    k = len(waypoint_nodes)               # how many waypoints we must visit
    full_mask = (1 << k) - 1             # bitmask with all k bits set = all visited
                                          # e.g. k=3 → 111 in binary = 7

    # Build lookup: waypoint node_id → its bit index in the mask
    # Manual loop, no enumerate() or dict comprehension dependency on order
    waypoint_index = {}                   # {node_id: bit_position}
    i = 0
    while i < k:
        waypoint_index[waypoint_nodes[i]] = i   # e.g. pump at node 12345 → bit 0
        i = i + 1

    # ── Sparse distance and parent tables ────────────────────────
    dist_table = {}    # {(node, mask): best_cost}      — sparse, checked with `in`
    parent     = {}    # {(node, mask): (prev_node, prev_mask) or None}

    # Compute starting mask: if start itself is a waypoint, mark it visited now
    start_mask = 0
    if start in waypoint_index:
        start_mask = (1 << waypoint_index[start])   # set the bit for start waypoint

    start_state = (start, start_mask)
    dist_table[start_state] = 0
    parent[start_state]     = None          # source has no parent

    # Priority queue: (cost, node, mask) — same structure as dijkstra.py's pq
    pq = [(0, start, start_mask)]

    while pq:
        current_cost, current_node, current_mask = heapq.heappop(pq)  # pop cheapest

        # ── Early exit ─────────────────────────────────────────
        if current_node == end and current_mask == full_mask:
            break   # reached goal with all waypoints visited

        # ── Stale entry check (same reason as dijkstra.py) ─────
        current_state = (current_node, current_mask)
        if dist_table[current_state] < current_cost:
            continue   # a cheaper path to this state was found later; skip

        # ── Neighbour exploration ───────────────────────────────
        for neighbor in graph.neighbors(current_node):    # same as dijkstra.py
            edge_data = graph.get_edge_data(current_node, neighbor)

            # Manual minimum — no min() builtin
            min_weight = _get_min_edge_weight(edge_data, weight)

            new_dist = current_cost + min_weight          # cost to reach neighbor

            # Update bitmask: if neighbor is a waypoint, set its bit
            new_mask = current_mask
            if neighbor in waypoint_index:
                new_mask = current_mask | (1 << waypoint_index[neighbor])  # set bit i

            neighbor_state = (neighbor, new_mask)

            # ── Relaxation ───────────────────────────────────
            if neighbor_state not in dist_table or new_dist < dist_table[neighbor_state]:
                dist_table[neighbor_state] = new_dist
                parent[neighbor_state]     = (current_node, current_mask)  # remember parent
                heapq.heappush(pq, (new_dist, neighbor, new_mask))         # push to heap

    # ── Check if goal state was reached ────────────────────────
    goal_state = (end, full_mask)
    if goal_state not in dist_table:
        print("  [WARN] Could not visit all waypoints — falling back to plain Dijkstra.")
        return _plain_dijkstra(graph, start, end, weight)

    best_cost = dist_table[goal_state]

    # ── Path reconstruction ─────────────────────────────────────
    # Same while-loop pattern as dijkstra.py:
    #   node = end; while node is not None: path.append(node); node = parent[node]
    # Here the "node" is a full state (node_id, mask).
    path = []
    state = goal_state
    while state is not None:
        node_id, mask = state
        path.append(node_id)       # collect node IDs in reverse order
        state = parent[state]      # step backwards through parent chain

    path.reverse()                 # reverse to get start → end order (same as dijkstra.py)
    return path, best_cost


def _plain_dijkstra(graph, start, end, weight='weight'):
    """
    Fallback plain Dijkstra — variable names match graph/dijkstra.py exactly:
    pq, distances, parent, current_distance, current_node,
    neighbor, edge_data, min_weight, new_dist, path, node.
    """
    pq = [(0, start)]                                         # (distance, node)
    distances = {node: float('inf') for node in graph.nodes} # all nodes start at infinity
    distances[start] = 0
    parent = {node: None for node in graph.nodes}

    while pq:
        current_distance, current_node = heapq.heappop(pq)   # pop smallest distance
        if current_node == end:
            break
        for neighbor in graph.neighbors(current_node):        # all connected nodes
            edge_data = graph.get_edge_data(current_node, neighbor)
            min_weight = _get_min_edge_weight(edge_data, weight)
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

    path.reverse()                                            # correct start → end order
    return path, distances[end]
