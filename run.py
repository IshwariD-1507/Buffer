# ============================================================
# run.py  — Developer Testing Pipeline
# ============================================================

from graph.loader import load_city_graph
from graph.weights import apply_composite_weights
from graph.dijkstra import dijkstra
from graph.astar import astar

from features.emergency import (
    get_hospital_nodes,
    bfs_radial_sweep,
    rank_hospitals,
    get_best_hospital,
)

from features.reviews import add_review
from features.waypoints import dijkstra_with_waypoints

from map.render import plot_route, plot_emergency_route

import osmnx as ox


# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

CITY_NAME = "Pune, India"

START_POINT = (18.53, 73.86)
END_POINT   = (18.5208, 73.8554)

MODE = "Rush Hour"   # Normal / Rush Hour / Emergency


# ------------------------------------------------------------
# LOAD GRAPH
# ------------------------------------------------------------

print("\n[INIT] Loading graph...")
graph = load_city_graph(CITY_NAME)
print("[INIT] Graph loaded")

# Apply weights once
graph = apply_composite_weights(graph, mode=MODE)


# ------------------------------------------------------------
# NODE CONVERSION
# ------------------------------------------------------------

start_node = ox.distance.nearest_nodes(graph, START_POINT[1], START_POINT[0])
end_node   = ox.distance.nearest_nodes(graph, END_POINT[1], END_POINT[0])

print(f"[INIT] Start Node: {start_node}")
print(f"[INIT] End Node  : {end_node}")


# ============================================================
# 1. DIJKSTRA vs A*
# ============================================================

def test_shortest_path():
    print("\n=== TEST: Dijkstra vs A* ===")

    path_dij, dist_dij = dijkstra(graph, start_node, end_node, weight='weight')
    path_astar, dist_astar, explored = astar(graph, start_node, end_node, weight='weight')

    print(f"Dijkstra Distance : {dist_dij:.2f}")
    print(f"A* Distance       : {dist_astar:.2f}")
    print(f"A* Nodes Explored : {explored}")

    m = plot_route(graph, path_astar)
    m.save("route.html")
    print("[MAP] Saved → route.html")


# ============================================================
# 2. EMERGENCY MODE (T2)
# ============================================================

def test_emergency():
    print("\n=== TEST: Emergency Routing ===")

    hospital_nodes = get_hospital_nodes(graph, city_name=CITY_NAME)

    candidates = bfs_radial_sweep(
        graph,
        start_node,
        hospital_nodes,
        max_hops=50
    )

    pq = rank_hospitals(graph, start_node, candidates)
    best = get_best_hospital(pq)

    if best:
        plot_emergency_route(
            graph,
            best["path"],
            candidates,
            output_file="emergency_route.html"
        )
        print("[MAP] Saved → emergency_route.html")


# ============================================================
# 3. REVIEWS IMPACT
# ============================================================

def test_reviews():
    print("\n=== TEST: Reviews Impact ===")

    # Run once before review
    path1, dist1 = dijkstra(graph, start_node, end_node, weight='weight')

    # Add pothole on first edge
    if len(path1) > 1:
        edge = (path1[0], path1[1])
        print(f"[TEST] Adding pothole on edge {edge}")
        add_review(edge, score=0.0, review_type="pothole")

    # Run again
    path2, dist2 = dijkstra(graph, start_node, end_node, weight='weight')

    print(f"Before: {dist1:.2f}")
    print(f"After : {dist2:.2f}")


# ============================================================
# 4. WAYPOINT ROUTING
# ============================================================

def test_waypoints():
    print("\n=== TEST: Waypoints Routing ===")

    # Dummy: pick first few nodes as waypoints
    waypoint_nodes = list(graph.nodes)[:2]

    path, dist = dijkstra_with_waypoints(
        graph,
        start_node,
        end_node,
        waypoint_nodes,
        weight='weight'
    )

    print(f"Waypoint Distance: {dist:.2f}")

    m = plot_route(graph, path)
    m.save("waypoints_route.html")
    print("[MAP] Saved → waypoints_route.html")


# ============================================================
# MAIN SWITCH (choose what to test)
# ============================================================

if __name__ == "__main__":

    # Uncomment what you want to test

    test_shortest_path()
    # test_emergency()
    # test_reviews()
    # test_waypoints()