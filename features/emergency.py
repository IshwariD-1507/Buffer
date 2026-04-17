import heapq
import random
import collections
import osmnx as ox

from graph.dijkstra import dijkstra


# ---------------------------------------------------------------------------
# 1. Fetch Hospital Nodes
# ---------------------------------------------------------------------------

def get_hospital_nodes(graph, city_name="Pune, India"):
    """
    Fetches all hospitals in the city from OpenStreetMap and maps them
    to the nearest node IDs in the existing NetworkX graph.

    Args:
        graph       : NetworkX MultiDiGraph (loaded city graph)
        city_name   : OSM place name string (default: "Pune, India")

    Returns:
        hospital_nodes (set) : Set of node IDs closest to real hospital locations
    """
    print(f"[T2] Fetching hospital locations for '{city_name}' from OSM...")

    try:
        # Pull hospital features as a GeoDataFrame
        hospitals_gdf = ox.features_from_place(city_name, tags={"amenity": "hospital"})
    except Exception as e:
        print(f"[T2] WARNING: Could not fetch hospitals from OSM: {e}")
        return set()

    if hospitals_gdf.empty:
        print("[T2] WARNING: No hospitals found in the specified area.")
        return set()

    # Use centroids to handle polygon geometries (buildings, campuses, etc.)
    centroids = hospitals_gdf.geometry.centroid

    lats = centroids.y.tolist()
    lons = centroids.x.tolist()

    # Map each centroid to the nearest graph node
    node_ids = ox.distance.nearest_nodes(graph, lons, lats)

    hospital_nodes = set(node_ids)
    print(f"[T2] Found {len(hospital_nodes)} unique hospital node(s) on the graph.")
    return hospital_nodes


# ---------------------------------------------------------------------------
# 2. Radial BFS Sweep
# ---------------------------------------------------------------------------

def bfs_radial_sweep(graph, start_node, hospital_nodes, max_hops=50):
    """
    Performs a BFS from the ambulance's current position to discover
    nearby hospitals within a maximum hop distance.

    Args:
        graph          : NetworkX MultiDiGraph
        start_node     : Node ID of the ambulance's current position
        hospital_nodes : Set of node IDs corresponding to hospitals
        max_hops       : Maximum intersection hops to explore (default: 50)

    Returns:
        candidate_hospitals (list) : List of hospital node IDs reachable within max_hops
    """
    print(f"[T2] Starting BFS radial sweep from node {start_node} (max_hops={max_hops})...")

    visited = set()
    queue = collections.deque()
    candidate_hospitals = []

    queue.append((start_node, 0))  # (node, hop_count)
    visited.add(start_node)

    while queue:
        current_node, hops = queue.popleft()

        # Check if this node is a hospital
        if current_node in hospital_nodes:
            candidate_hospitals.append(current_node)
            print(f"    [BFS] Hospital found at node {current_node} ({hops} hops away)")

        # Don't expand beyond max_hops
        if hops >= max_hops:
            continue

        for neighbor in graph.neighbors(current_node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, hops + 1))

    print(f"[T2] BFS complete. {len(candidate_hospitals)} candidate hospital(s) found.")
    return candidate_hospitals


# ---------------------------------------------------------------------------
# 3. Hospital Ranking via Reverse Dijkstra
# ---------------------------------------------------------------------------

def rank_hospitals(graph, ambulance_node, candidate_hospitals):
    """
    Ranks candidate hospitals using Reverse Dijkstra to solve the
    1-to-N routing problem efficiently. Also factors in simulated
    bed availability for a composite priority score.

    Composite scoring formula:
        final_score = (0.6 * travel_time) - (0.4 * bed_score)
        (Lower score = better hospital choice)

    Args:
        graph               : NetworkX MultiDiGraph
        ambulance_node      : Node ID of the ambulance's current position
        candidate_hospitals : List of hospital node IDs (from BFS sweep)

    Returns:
        pq (list) : Min-Heap priority queue of tuples:
                    (final_score, travel_time, bed_score, hosp_node, path)
    """
    if not candidate_hospitals:
        print("[T2] No candidate hospitals to rank.")
        return []

    print(f"[T2] Ranking {len(candidate_hospitals)} hospital(s) using Reverse Dijkstra...")

    # Reverse graph so we can run Dijkstra from each hospital toward the ambulance
    reversed_graph = graph.reverse(copy=True)

    pq = []  # Min-Heap

    for hosp_node in candidate_hospitals:
        try:
            # Dijkstra on reversed graph: hospital → ambulance
            path, travel_time = dijkstra(reversed_graph, hosp_node, ambulance_node)

            if path is None or travel_time == float('inf'):
                print(f"    [RANK] No path found to hospital {hosp_node}, skipping.")
                continue

            # Reverse the path to get actual ambulance → hospital direction
            actual_path = path[::-1]

            # Simulate bed availability (1=no beds, 100=fully available)
            bed_score = random.randint(1, 100)

            # Composite score: lower is better
            # Travel time dominates (60%) but bed availability matters (40%)
            final_score = (0.6 * travel_time) - (0.4 * bed_score)

            heapq.heappush(pq, (final_score, travel_time, bed_score, hosp_node, actual_path))

            print(f"    [RANK] Hospital {hosp_node} | "
                  f"Travel: {travel_time:.1f}m | "
                  f"Beds: {bed_score}/100 | "
                  f"Score: {final_score:.2f}")

        except Exception as e:
            print(f"    [RANK] Error processing hospital {hosp_node}: {e}")
            continue

    print(f"[T2] Ranking complete. {len(pq)} hospital(s) in priority queue.")
    return pq


# ---------------------------------------------------------------------------
# 4. Best Hospital Selector
# ---------------------------------------------------------------------------

def get_best_hospital(pq):
    """
    Pops the top entry from the ranked Min-Heap priority queue.

    Args:
        pq (list) : Min-Heap returned by rank_hospitals()

    Returns:
        dict with keys: final_score, travel_time, bed_score, hosp_node, path
        OR None if the queue is empty
    """
    if not pq:
        print("[T2] Priority queue is empty — no hospital available.")
        return None

    final_score, travel_time, bed_score, hosp_node, path = heapq.heappop(pq)

    print(f"\n[T2] ✅ BEST HOSPITAL SELECTED:")
    print(f"     Node        : {hosp_node}")
    print(f"     Travel Time : {travel_time:.1f} meters (road distance)")
    print(f"     Bed Score   : {bed_score}/100")
    print(f"     Final Score : {final_score:.2f}")

    return {
        "final_score": final_score,
        "travel_time": travel_time,
        "bed_score": bed_score,
        "hosp_node": hosp_node,
        "path": path,
    }