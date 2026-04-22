import heapq

# ============================================================
# features/replacement.py  — T3
#
# DSA Concepts:
#   1. Distress Signal Handler — re-runs A* (from graph/astar.py)
#      from the current broken-down node to the hospital.
#
#   2. Bidirectional Dijkstra — finds the optimal rendezvous
#      (handoff) node where:
#        - the distressed ambulance drives FORWARD  from distress_node
#        - the replacement ambulance drives BACKWARD from hospital_node
#      Rendezvous = node v where forward_dist[v] + backward_dist[v] is minimum.
#
# MANUAL EDGE REVERSAL: Instead of graph.reverse() (a NetworkX builtin
# that hides the logic), we manually build a reversed adjacency structure
# so the DSA concept of graph reversal is fully visible.
#
# heapq is the priority queue — same as dijkstra.py in the repo.
# ============================================================


# ============================================================
# PART 1 — Distress Signal Handler
# ============================================================
def get_street_name(graph, node_id):
    """Extracts the street name connected to a specific node."""
    try:
        # Look at all the edges (roads) connected to this node
        for u, v, data in graph.edges(node_id, data=True):
            if 'name' in data:
                # Sometimes OSM returns a list of names if roads merge
                if isinstance(data['name'], list):
                    return data['name'][0]
                return data['name']
    except Exception:
        pass
    
    return "Unknown Street"

def handle_distress_signal(graph, current_node, destination_node, weight='weight'):
    """
    Called when an ambulance triggers a distress signal mid-route.

    Records where the distress happened and immediately re-runs A*
    (from graph/astar.py) from that node to the original destination
    so the system can dispatch a new route without waiting.

    Args:
        graph            : road network (NetworkX MultiDiGraph)
        current_node     : node ID where the distress signal was triggered
        destination_node : original destination node ID (e.g. a hospital node
                           from T2's get_best_hospital())
        weight           : edge attribute key — 'weight' from weights.py

    Returns:
        path     : new route list  — same structure as astar() in graph/astar.py
        dist     : total route cost (float)
        explored : number of nodes explored by A* (int) — for comparison output
                   (matches the 3-value return of astar() used in run.py:
                    path_astar, dist_astar, explored = astar(...))
    """
    # Import here to avoid circular imports at module load time
    from graph.astar import astar   # astar() returns (path, dist, explored) per run.py

    print(f"  [DISTRESS] Signal received at node: {current_node}")
    print(f"  [DISTRESS] Re-routing to destination {destination_node} via A*...")

    # Re-run A* from distress node — uses the same weight as the pipeline
    path, dist, explored = astar(graph, current_node, destination_node, weight=weight)

    print(f"  [DISTRESS] New route: {len(path)} nodes | Cost: {dist:.1f}")
    print(f"  [DISTRESS] A* explored {explored} nodes.")
    return path, dist, explored


# ============================================================
# PART 2 — Bidirectional Dijkstra helpers
# ============================================================

def _build_reversed_adjacency(graph, weight):
    """
    Manually build a reversed adjacency list from the graph.

    In the original graph: edge u → v with cost w
    In the reversed graph: edge v → u with cost w

    This is equivalent to graph.reverse() but done manually to show
    the DSA concept clearly — we explicitly flip every directed edge.

    Args:
        graph  : road network (NetworkX MultiDiGraph)
        weight : edge attribute key for cost

    Returns:
        rev_adj : dict of dicts — rev_adj[v][u] = min_cost of edge u→v in original
                  This lets us do Dijkstra "backwards" from the hospital.
    """
    rev_adj = {}            # rev_adj[destination_in_original][source_in_original] = cost

    # Initialise empty adjacency lists for every node
    for node in graph.nodes:
        rev_adj[node] = {}  # each node starts with no reversed neighbours

    # Walk every directed edge u → v in the original graph
    for u, v, data in graph.edges(data=True):
        # Get the cost for this specific edge
        if weight in data:
            w = data[weight]
        elif 'length' in data:
            w = data['length']
        else:
            w = 1

        # Flip direction: in reversed graph this becomes v → u
        # If multiple parallel edges exist between u and v, keep the minimum
        if u not in rev_adj[v]:
            rev_adj[v][u] = w          # first edge seen: store it
        else:
            if w < rev_adj[v][u]:
                rev_adj[v][u] = w      # manual minimum — no min() builtin

    return rev_adj


def _dijkstra_on_adj(adj, source, all_nodes):
    """
    Run Dijkstra on a plain adjacency dict (not a NetworkX graph).
    Used for the backward pass on the manually reversed graph.

    Variable names mirror graph/dijkstra.py exactly:
        pq, distances, parent, current_distance, current_node,
        neighbor, new_dist, path (not used here — caller reconstructs).

    Args:
        adj       : adjacency dict — adj[node][neighbor] = cost
        source    : starting node ID
        all_nodes : iterable of all node IDs (from graph.nodes)

    Returns:
        distances : {node: shortest_distance_from_source}
        parent    : {node: parent_node} for path reconstruction
    """
    pq = [(0, source)]                                          # (distance, node)
    distances = {node: float('inf') for node in all_nodes}     # init all to infinity
    distances[source] = 0
    parent = {node: None for node in all_nodes}

    while pq:
        current_distance, current_node = heapq.heappop(pq)     # pop smallest distance

        # Stale entry check — same as dijkstra.py's implicit skip pattern
        if current_distance > distances[current_node]:
            continue

        # Iterate over neighbours in the adjacency dict
        if current_node not in adj:
            continue                    # node has no outgoing edges in this direction

        for neighbor in adj[current_node]:
            w = adj[current_node][neighbor]     # direct lookup — already minimised
            new_dist = current_distance + w

            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = current_node
                heapq.heappush(pq, (new_dist, neighbor))

    return distances, parent


def _dijkstra_on_graph(graph, source, weight):
    """
    Run Dijkstra directly on the NetworkX graph (forward pass).
    Returns full distance dict and parent dict for all nodes.

    Variable names match graph/dijkstra.py:
        pq, distances, parent, current_distance, current_node,
        neighbor, edge_data, min_weight, new_dist
    """
    pq = [(0, source)]                                              # (distance, node)
    distances = {node: float('inf') for node in graph.nodes}       # init all to infinity
    distances[source] = 0
    parent = {node: None for node in graph.nodes}

    while pq:
        current_distance, current_node = heapq.heappop(pq)         # pop smallest distance

        if current_distance > distances[current_node]:
            continue    # stale entry

        for neighbor in graph.neighbors(current_node):             # all connected nodes
            edge_data = graph.get_edge_data(current_node, neighbor)

            # Manual minimum — no min() builtin
            min_weight = float('inf')
            for key in edge_data:
                d = edge_data[key]
                if weight in d:
                    w = d[weight]
                elif 'length' in d:
                    w = d['length']
                else:
                    w = 1
                if w < min_weight:
                    min_weight = w

            new_dist = current_distance + min_weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = current_node
                heapq.heappush(pq, (new_dist, neighbor))

    return distances, parent


def _reconstruct_path(parent, source, target):
    """
    Trace parent links backwards from target to source to rebuild path.
    Same pattern as graph/dijkstra.py:
        node = end
        while node is not None:
            path.append(node); node = parent[node]
        path.reverse()
    """
    path = []
    node = target
    while node is not None:
        path.append(node)
        if node == source:
            break
        node = parent[node]     # step backwards through parent chain

    path.reverse()              # reverse to get source → target order

    # Safety: if reconstruction failed (disconnected graph), return empty list
    if len(path) == 0:
        return []
    if path[0] != source:
        return []
    return path


# ============================================================
# PART 2 — Main bidirectional Dijkstra function
# ============================================================

def find_rendezvous_node(graph, distress_node, hospital_node, weight='weight'):
    """
    Bidirectional Dijkstra to find the optimal rendezvous (handoff) node.

    ── ALGORITHM ────────────────────────────────────────────────
    STEP 1 — Forward Dijkstra:
        Run standard Dijkstra from distress_node on the original graph.
        Result: forward_dist[v] = cost for distressed ambulance to reach v.

    STEP 2 — Backward Dijkstra (manual edge reversal):
        Manually flip all edges in the graph (u→v becomes v→u).
        Run Dijkstra from hospital_node on this reversed graph.
        Result: backward_dist[v] = cost for replacement ambulance at
                hospital to reach v (since a path hospital→v on original
                is equivalent to v→hospital on the reversed graph).

    STEP 3 — Find rendezvous:
        For every node v:  combined[v] = forward_dist[v] + backward_dist[v]
        Rendezvous = node v where combined[v] is minimum.
        This is the point where both ambulances meet at the lowest total cost.

    ── WHY MANUAL REVERSAL? ─────────────────────────────────────
    graph.reverse() is a NetworkX call that hides the reversal logic.
    We manually flip edges with _build_reversed_adjacency() so the
    DSA concept is fully visible in the code.

    Args:
        graph         : road network (NetworkX MultiDiGraph)
        distress_node : node where the original ambulance broke down
        hospital_node : node of the hospital dispatching the replacement
        weight        : edge attribute key — 'weight' from weights.py

    Returns:
        rendezvous_node        : best handoff node ID
        path_to_rendezvous     : route from distress_node → rendezvous_node
        path_from_hospital     : route from hospital_node → rendezvous_node
        total_cost             : combined travel cost at rendezvous (float)
    """
    # ── Step 1: Forward Dijkstra (distress → all nodes) ──────
    print(f"  [BIDIR] Forward Dijkstra from distress node {distress_node}...")
    forward_dist, forward_parent = _dijkstra_on_graph(graph, distress_node, weight)

    # ── Step 2: Manual edge reversal + backward Dijkstra ─────
    print(f"  [BIDIR] Building reversed adjacency (manual edge flip)...")
    rev_adj = _build_reversed_adjacency(graph, weight)  # flip all edges manually

    print(f"  [BIDIR] Backward Dijkstra from hospital node {hospital_node}...")
    backward_dist, backward_parent = _dijkstra_on_adj(rev_adj, hospital_node, graph.nodes)

    # ── Step 3: Find rendezvous node ─────────────────────────
    # Manual loop over all nodes to find argmin(forward[v] + backward[v])
    best_node    = None
    best_combined = float('inf')

    for node in graph.nodes:
        f = forward_dist[node]          # cost: distress_node → node
        b = backward_dist[node]         # cost: hospital_node → node (via reversed)
        combined = f + b

        if combined < best_combined:    # manual minimum tracking
            best_combined = combined
            best_node     = node        # new best rendezvous candidate

    if best_node is None:
        print("  [BIDIR ERROR] No rendezvous node found.")
        return None, [], [], float('inf')

    print(f"  [BIDIR] Best rendezvous node: {best_node} | Combined cost: {best_combined:.1f}")

    # ── Path reconstruction ──────────────────────────────────
    # Path 1: distress_node → rendezvous (using forward_parent)
    path_to_rendezvous = _reconstruct_path(forward_parent, distress_node, best_node)

    # Path 2: hospital_node → rendezvous (using backward_parent on reversed graph)
    # backward_parent gives us the path on the reversed graph:
    # hospital_node → best_node on reversed = hospital_node → best_node on original
    path_from_hospital = _reconstruct_path(backward_parent, hospital_node, best_node)

    return best_node, path_to_rendezvous, path_from_hospital, best_combined
