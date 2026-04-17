from graph.loader import load_city_graph
from graph.dijkstra import dijkstra
from graph.weights import apply_composite_weights
from graph.astar import astar
from map.render import plot_route

import osmnx as ox

# -----------------------
# Load graph ONCE
# -----------------------
graph = load_city_graph()
print("Graph loaded successfully!")

# -----------------------
# Coordinates (your example)
# -----------------------
start_point = (18.53, 73.86)
end_point = (18.5208, 73.8554)

# Convert to nearest nodes
start_node = ox.distance.nearest_nodes(graph, start_point[1], start_point[0])
end_node = ox.distance.nearest_nodes(graph, end_point[1], end_point[0])

# -----------------------
# Apply composite weights
# -----------------------
graph = apply_composite_weights(graph, mode="Rush Hour")

# -----------------------
# Run Dijkstra (with weight)
# -----------------------
path_dij, dist_dij = dijkstra(graph, start_node, end_node, weight='weight')

# -----------------------
# Run A* (IMPORTANT: 3 outputs)
# -----------------------
path_astar, dist_astar, explored = astar(graph, start_node, end_node, weight='weight')

# -----------------------
# Comparison
# -----------------------
print("\n===== COMPARISON =====")
print("Dijkstra Distance:", dist_dij)
print("A* Distance:", dist_astar)
print("A* Nodes Explored:", explored)
print("Dijkstra Path Length:", len(path_dij))

# -----------------------
# Plot A* route
# -----------------------
m = plot_route(graph, path_astar)

# Save map
m.save("route.html")
print("Map saved as route.html")
import heapq

from graph.loader import load_city_graph
from features.emergency import (
    get_hospital_nodes,
    bfs_radial_sweep,
    rank_hospitals,
    get_best_hospital,
)
from map.render_emergency import plot_emergency_route


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CITY_NAME = "Pune, India"
OUTPUT_FILE = "emergency_route.html"

# BFS sweep radius — number of intersection hops to search for hospitals
MAX_HOPS = 50

# ---------------------------------------------------------------------------
# Main T2 Execution Flow
# ---------------------------------------------------------------------------

def run_t2(ambulance_node=None):
    """
    Full T2 pipeline:
        1. Load city graph
        2. Resolve ambulance position
        3. Fetch hospital nodes from OSM
        4. BFS radial sweep to find nearby candidates
        5. Reverse Dijkstra + composite scoring to rank hospitals
        6. Select best hospital and render the route map

    Args:
        ambulance_node : Node ID for the ambulance's current position.
                         If None, defaults to the first node in the graph.
    """
    print("=" * 60)
    print("  T2 — Medical Emergency Mode")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Load the city graph
    # ------------------------------------------------------------------
    print("\n[STEP 1] Loading city graph...")
    graph = load_city_graph()
    print(f"         Graph loaded: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    # ------------------------------------------------------------------
    # Step 2: Resolve ambulance node
    # ------------------------------------------------------------------
    if ambulance_node is None:
        # Default: pick the first node in the graph as a fallback
        ambulance_node = list(graph.nodes)[0]
        print(f"\n[STEP 2] No ambulance node specified — using default: {ambulance_node}")
    else:
        print(f"\n[STEP 2] Ambulance current position node: {ambulance_node}")

    if ambulance_node not in graph.nodes:
        raise ValueError(f"Ambulance node {ambulance_node} is not present in the graph!")

    # ------------------------------------------------------------------
    # Step 3: Fetch hospital nodes from OSM
    # ------------------------------------------------------------------
    print(f"\n[STEP 3] Fetching hospital nodes for '{CITY_NAME}'...")
    hospital_nodes = get_hospital_nodes(graph, city_name=CITY_NAME)

    if not hospital_nodes:
        print("[ERROR] No hospital nodes found. Cannot continue T2 execution.")
        return

    # ------------------------------------------------------------------
    # Step 4: BFS radial sweep
    # ------------------------------------------------------------------
    print(f"\n[STEP 4] Running BFS radial sweep (max_hops={MAX_HOPS})...")
    candidate_hospitals = bfs_radial_sweep(
        graph, ambulance_node, hospital_nodes, max_hops=MAX_HOPS
    )

    if not candidate_hospitals:
        print("[ERROR] No candidate hospitals found within sweep radius.")
        print("        Try increasing MAX_HOPS or check the ambulance node location.")
        return

    # ------------------------------------------------------------------
    # Step 5: Rank hospitals with Reverse Dijkstra
    # ------------------------------------------------------------------
    print(f"\n[STEP 5] Ranking {len(candidate_hospitals)} candidate hospital(s)...")
    pq = rank_hospitals(graph, ambulance_node, candidate_hospitals)

    if not pq:
        print("[ERROR] Hospital ranking returned no valid results.")
        return

    # ------------------------------------------------------------------
    # Step 6: Select best hospital
    # ------------------------------------------------------------------
    print(f"\n[STEP 6] Selecting optimal hospital...")
    best = get_best_hospital(pq)

    if best is None:
        print("[ERROR] Could not determine best hospital.")
        return

    # ------------------------------------------------------------------
    # Step 7: Render the route map
    # ------------------------------------------------------------------
    print(f"\n[STEP 7] Rendering emergency route map...")
    plot_emergency_route(
        graph=graph,
        path=best["path"],
        candidate_hospitals=candidate_hospitals,
        output_file=OUTPUT_FILE,
    )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  T2 EXECUTION COMPLETE")
    print("=" * 60)
    print(f"  Ambulance Node   : {ambulance_node}")
    print(f"  Best Hospital    : {best['hosp_node']}")
    print(f"  Travel Distance  : {best['travel_time']:.1f} m")
    print(f"  Bed Score        : {best['bed_score']}/100")
    print(f"  Composite Score  : {best['final_score']:.2f}")
    print(f"  Route Length     : {len(best['path'])} nodes")
    print(f"  Output Map       : {OUTPUT_FILE}")
    print("=" * 60)

    return best


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # -----------------------------------------------------------------
    # Set your ambulance node ID here.
    # To find a valid node near a specific coordinate, use:
    #   import osmnx as ox
    #   graph = load_city_graph()
    #   node = ox.distance.nearest_nodes(graph, lon=73.8567, lat=18.5204)
    # -----------------------------------------------------------------
    AMBULANCE_NODE = None  # Replace with a real node ID, e.g. 1234567890

    run_t2(ambulance_node=AMBULANCE_NODE)