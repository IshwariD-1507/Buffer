import heapq
import random
import collections
import osmnx as ox

from graph.dijkstra import dijkstra


# -----------------------------------------------------------
# 1. Get hospital nodes from OSM
# -----------------------------------------------------------

def get_hospital_nodes(graph, city_name="Pune, India"):
    print(f"[T2] Fetching hospitals for '{city_name}'...")

    try:
        hospitals_gdf = ox.features_from_place(city_name, tags={"amenity": "hospital"})
    except Exception as e:
        print(f"[T2] WARNING: Could not fetch hospitals: {e}")
        return set()

    if hospitals_gdf.empty:
        print("[T2] WARNING: No hospitals found.")
        return set()

    # use centroid (works for both points and polygons)
    centroids = hospitals_gdf.geometry.centroid

    lats = centroids.y.tolist()
    lons = centroids.x.tolist()

    node_ids = ox.distance.nearest_nodes(graph, lons, lats)

    hospital_nodes = set(node_ids)

    print(f"[T2] Found {len(hospital_nodes)} hospital node(s).")
    return hospital_nodes


# -----------------------------------------------------------
# 2. BFS sweep to find nearby hospitals
# -----------------------------------------------------------

def bfs_radial_sweep(graph, start_node, hospital_nodes, max_hops=50):
    print(f"[T2] BFS sweep from node {start_node} (max_hops={max_hops})...")

    visited = set()
    queue = collections.deque()
    candidate_hospitals = []

    queue.append((start_node, 0))
    visited.add(start_node)

    while queue:
        current_node, hops = queue.popleft()

        if current_node in hospital_nodes:
            candidate_hospitals.append(current_node)
            print(f"    [BFS] Found hospital at {current_node} ({hops} hops)")

        if hops >= max_hops:
            continue

        # directed graph → use successors
        for neighbor in graph.successors(current_node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, hops + 1))

    print(f"[T2] BFS complete. {len(candidate_hospitals)} candidate(s).")
    return candidate_hospitals

def rank_hospitals(graph, ambulance_node, candidate_hospitals):
    if not candidate_hospitals:
        print("[T2] No hospitals to rank.")
        return []

    print(f"[T2] Ranking {len(candidate_hospitals)} hospital(s)...")

    # We no longer need to reverse the graph! 
    # We just run our new function EXACTLY ONCE from the ambulance's location.
    from graph.dijkstra import dijkstra_all
    distances, parents = dijkstra_all(graph, ambulance_node, weight='weight')

    pq = []

    for hosp_node in candidate_hospitals:
        try:
            # Look up the distance instantly (no recalculation needed)
            travel_dist = distances.get(hosp_node, float('inf'))
            
            if travel_dist == float('inf'):
                continue

            # Reconstruct the specific path from the ambulance to this hospital
            actual_path = []
            curr = hosp_node
            while curr is not None:
                actual_path.append(curr)
                curr = parents[curr]
            actual_path.reverse()

            # simulate bed availability
            random.seed(hosp_node)
            bed_score = random.randint(1, 100)

            # lower score = better
            final_score = (0.6 * travel_dist) - (0.4 * bed_score)

            heapq.heappush(
                pq,
                (final_score, travel_dist, bed_score, hosp_node, actual_path)
            )

            print(
                f"    [RANK] {hosp_node} | "
                f"Dist: {travel_dist:.1f} | "
                f"Beds: {bed_score} | "
                f"Score: {final_score:.2f}"
            )

        except Exception as e:
            print(f"    [RANK] Error for {hosp_node}: {e}")

    print(f"[T2] Ranking complete. {len(pq)} valid hospital(s).")
    return pq

# -----------------------------------------------------------
# 4. Pick best hospital
# -----------------------------------------------------------

def get_best_hospital(pq):
    if not pq:
        print("[T2] No hospital available.")
        return None

    final_score, travel_dist, bed_score, hosp_node, path = heapq.heappop(pq)

    print("\n[T2] ✅ BEST HOSPITAL")
    print(f"     Node       : {hosp_node}")
    print(f"     Distance   : {travel_dist:.1f} meters")
    print(f"     Beds       : {bed_score}/100")
    print(f"     Score      : {final_score:.2f}")

    return {
        "final_score": final_score,
        "travel_time": travel_dist,   # kept key same for compatibility
        "bed_score": bed_score,
        "hosp_node": hosp_node,
        "path": path,
    }