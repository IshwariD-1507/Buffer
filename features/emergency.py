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
        return {}

    if hospitals_gdf.empty:
        print("[T2] WARNING: No hospitals found.")
        return {}

    # Extract names safely
    if "name" in hospitals_gdf.columns:
        names = hospitals_gdf["name"].fillna("Unknown Hospital").tolist()
    else:
        names = ["Unknown Hospital"] * len(hospitals_gdf)

    centroids = hospitals_gdf.geometry.centroid
    lats = centroids.y.tolist()
    lons = centroids.x.tolist()

    node_ids = ox.distance.nearest_nodes(graph, lons, lats)

    # Create a dictionary mapping Node ID -> Hospital Name
    hospital_data = {}
    for node_id, name in zip(node_ids, names):
        hospital_data[node_id] = name

    print(f"[T2] Found {len(hospital_data)} hospital node(s).")
    return hospital_data


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

def rank_hospitals(graph, ambulance_node, candidate_hospitals, hospital_data):
    if not candidate_hospitals:
        print("[T2] No hospitals to rank.")
        return []

    print(f"[T2] Ranking {len(candidate_hospitals)} hospital(s)...")

    from graph.dijkstra import dijkstra_all
    distances, parents = dijkstra_all(graph, ambulance_node, weight='weight')

    pq = []

    for hosp_node in candidate_hospitals:
        try:
            travel_dist = distances.get(hosp_node, float('inf'))
            if travel_dist == float('inf'): continue
            
            # Fetch the actual name from our dictionary!
            hosp_name = hospital_data.get(hosp_node, "Unknown Hospital")

            actual_path = []
            curr = hosp_node
            while curr is not None:
                actual_path.append(curr)
                curr = parents[curr]
            actual_path.reverse()

            random.seed(hosp_node)
            bed_score = random.randint(1, 100)
            final_score = (0.6 * travel_dist) - (0.4 * bed_score)

            # Store the name in the priority queue
            heapq.heappush(pq, (final_score, travel_dist, bed_score, hosp_node, hosp_name, actual_path))

            print(f"    [RANK] {hosp_name} | Dist: {travel_dist:.1f} | Beds: {bed_score} | Score: {final_score:.2f}")

        except Exception as e:
            print(f"    [RANK] Error for {hosp_node}: {e}")

    return pq

# -----------------------------------------------------------
# 4. Pick best hospital
# -----------------------------------------------------------

def get_best_hospital(pq):
    if not pq:
        return None

    # Unpack the new name variable
    final_score, travel_dist, bed_score, hosp_node, hosp_name, path = heapq.heappop(pq)

    print("\n[T2] ✅ BEST HOSPITAL")
    print(f"     Name       : {hosp_name}")
    print(f"     Distance   : {travel_dist:.1f} meters")
    print(f"     Beds       : {bed_score}/100")
    print(f"     Score      : {final_score:.2f}")

    return {
        "final_score": final_score,
        "travel_time": travel_dist,
        "bed_score": bed_score,
        "hosp_node": hosp_node,
        "hosp_name": hosp_name, # Added to dictionary
        "path": path,
    }