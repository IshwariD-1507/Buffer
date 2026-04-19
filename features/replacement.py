import heapq

# ============================================================
# features/replacement.py  — T3
# Ambulance distress signal handler + bidirectional Dijkstra
#
# When the ambulance sends a distress signal from its current
# node, we need to find the best RENDEZVOUS point where a
# replacement ambulance (coming from hospital) and the
# distressed ambulance's patient transfer can meet at the
# minimum combined travel cost.
#
# Uses bidirectional Dijkstra:
#   - Forward  : Dijkstra from distressed ambulance node
#   - Backward : Dijkstra from hospital node (on reversed graph)
#   - Rendezvous = node v where forward[v] + backward[v] is min
# ============================================================

# ============================================================
# PART 1 — Distress Signal Handler
# ============================================================

def handle_distress_signal(graph, current_node, destination_node, weight='weight'):
    """
    Called when an ambulance sends a distress signal mid-route.

    Records the node where the distress occurred, then re-runs
    A* (imported from graph/astar.py) from that exact node to
    the original destination so the system has a fresh route
    without relying on the broken ambulance completing its trip.

    Args:
        graph            : road network (NetworkX MultiDiGraph)
        current_node     : node ID where the distress was triggered
        destination_node : original destination (e.g. a hospital node)
        weight           : edge weight attribute

    Returns:
        path     : new route from current_node to destination_node
        dist     : total route cost
        explored : number of nodes explored by A* (for comparison output)
    """
    # Import here to avoid circular imports at module load time
    from graph.astar import astar  # astar() follows the same signature as dijkstra()

    print(f"  [DISTRESS] Signal received at node {current_node}.")
    print(f"  [DISTRESS] Re-routing to destination {destination_node} via A*...")

    # Re-run A* from distress node — same weight used by the rest of the pipeline
    path, dist, explored = astar(graph, current_node, destination_node, weight=weight)

    print(f"  [DISTRESS] New route: {len(path)} nodes, cost = {dist:.1f}")
    print(f"  [DISTRESS] A* explored {explored} nodes.")
    return path, dist, explored


# ============================================================
# PART 2 — Bidirectional Dijkstra for Rendezvous Node
# ============================================================

def _single_source_dijkstra(graph, source, weight='weight'):
    """
    Run Dijkstra from `source` and return the full distance dict.
    Identical logic to graph/dijkstra.py but returns all distances
    (not just the path to one destination).

    Args:
        graph  : road network
        source : starting node
        weight : edge weight attribute

    Returns:
        dist   : {node: shortest_distance_from_source}
        parent : {node: parent_node} for path reconstruction
    """
    dist = {node: float('inf') for node in graph.nodes}
    dist[source] = 0
    parent = {node: None for node in graph.nodes}
    pq = [(0, source)]   # (cost, node)

    while pq:
        current_cost, current_node = heapq.heappop(pq)  # pop cheapest unvisited node

        # Skip stale entries (we may have pushed the same node multiple times)
        if current_cost > dist[current_node]:
            continue

        for neighbor in graph.neighbors(current_node):
            edge_data = graph.get_edge_data(current_node, neighbor)  # get edge attributes
            min_w = float('inf')
            for d in edge_data.values():
                w = d.get(weight, d.get('length', 1))  # prefer composite weight, fall back to length
                if w < min_w:
                    min_w = w

            new_cost = current_cost + min_w
            if new_cost < dist[neighbor]:      # relaxation step
                dist[neighbor] = new_cost
                parent[neighbor] = current_node
                heapq.heappush(pq, (new_cost, neighbor))

    return dist, parent


def find_rendezvous_node(graph, distress_node, hospital_node, weight='weight'):
    """
    Bidirectional Dijkstra to find the optimal rendezvous (handoff) point.

    Algorithm:
      1. Run Dijkstra FORWARD  from distress_node  → forward_dist[v]
      2. Run Dijkstra BACKWARD from hospital_node  → backward_dist[v]
         (backward = Dijkstra on the reversed graph, same as T2's reverse Dijkstra)
      3. For every node v, compute combined_cost[v] = forward_dist[v] + backward_dist[v]
      4. Rendezvous = argmin(combined_cost)  — the node where the two ambulances
         can meet at the lowest total travel expense.

    Args:
        graph         : road network (NetworkX MultiDiGraph)
        distress_node : node where the original ambulance broke down
        hospital_node : node of the hospital sending the replacement ambulance
        weight        : edge weight attribute

    Returns:
        rendezvous_node    : the best handoff node ID
        path_to_rendezvous : route from distress_node to rendezvous_node
        path_from_hospital : route from hospital_node to rendezvous_node
        total_cost         : combined travel cost at rendezvous
    """
    print(f"  [BIDIR] Running forward Dijkstra from distress node {distress_node}...")
    forward_dist, forward_parent = _single_source_dijkstra(graph, distress_node, weight)

    # Reverse the graph so we can run "backward Dijkstra" from the hospital
    # graph.reverse() flips all directed edges — exactly as described in the spec
    reversed_graph = graph.reverse(copy=False)  # copy=False is memory-efficient; we won't modify it
    print(f"  [BIDIR] Running backward Dijkstra from hospital node {hospital_node}...")
    backward_dist, backward_parent = _single_source_dijkstra(reversed_graph, hospital_node, weight)

    # Find the rendezvous node: argmin over all nodes of forward[v] + backward[v]
    best_node = None
    best_combined = float('inf')

    for node in graph.nodes:
        f = forward_dist.get(node, float('inf'))
        b = backward_dist.get(node, float('inf'))
        combined = f + b
        if combined < best_combined:
            best_combined = combined
            best_node = node    # update best rendezvous candidate

    if best_node is None:
        print("  [BIDIR ERROR] No rendezvous node found.")
        return None, [], [], float('inf')

    print(f"  [BIDIR] Best rendezvous node: {best_node} | Combined cost: {best_combined:.1f}")

    # --------------------------------------------------------
    # Reconstruct path from distress_node → rendezvous_node
    # (using forward_parent)
    # --------------------------------------------------------
    path_to_rendezvous = _reconstruct_path(forward_parent, distress_node, best_node)

    # --------------------------------------------------------
    # Reconstruct path from hospital_node → rendezvous_node
    # (backward_parent gives us path on reversed graph,
    #  which equals hospital → rendezvous on the original graph)
    # --------------------------------------------------------
    path_from_hospital = _reconstruct_path(backward_parent, hospital_node, best_node)

    return best_node, path_to_rendezvous, path_from_hospital, best_combined


def _reconstruct_path(parent, source, target):
    """
    Trace back through a parent dictionary to rebuild the path
    from source to target.

    Args:
        parent : {node: parent_node} dict produced by Dijkstra
        source : start of the path
        target : end of the path

    Returns:
        path : list of node IDs from source to target
    """
    path = []
    node = target
    while node is not None:
        path.append(node)
        if node == source:
            break
        node = parent.get(node)   # walk backwards through parent links

    path.reverse()  # reverse to get source → target order

    # Safety check: if reconstruction failed (disconnected graph), return empty
    if not path or path[0] != source:
        return []

    return path
