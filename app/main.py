import streamlit as st
import osmnx as ox
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

from features.replacement import handle_distress_signal
from features.waypoints import get_petrol_pump_nodes, dijkstra_with_waypoints

from map.render import plot_route
from map.render import plot_emergency_route


# -----------------------------------------------------------
# Cache graph loading (prevents reloading every interaction)
# -----------------------------------------------------------
@st.cache_resource
def load_graph_cached(city_name):
    return load_city_graph(city_name)


# -----------------------------------------------------------
# Convert place → graph node safely
# -----------------------------------------------------------
def place_to_node(graph, place, city_context):
    try:
        full_query = f"{place}, {city_context}"
        lat, lon = ox.geocode(full_query)
        return ox.distance.nearest_nodes(graph, lon, lat)
    except Exception as e:
        st.error(f"Could not locate: {place} ({e})")
        return None


# -----------------------------------------------------------
# UI
# -----------------------------------------------------------
st.title("🚑 Smart Ambulance Routing System")

country = st.text_input("Enter Country")
city = st.text_input("Enter City")

start_place = st.text_input("Enter Start Location")
end_place = st.text_input("Enter Destination")

mode = st.selectbox(
    "Select Mode",
    ["Normal", "Emergency", "Waypoints", "Distress"]
)


# -----------------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------------
if st.button("Run"):

    # ---- Validation ----
    if not (country and city and start_place and end_place):
        st.warning("Please fill all fields.")
        st.stop()

    city_context = f"{city}, {country}"

    # ---- Load graph ----
    with st.spinner("Loading map..."):
        graph = load_graph_cached(city_context)

    # ---- Apply weights ----
    graph = apply_composite_weights(graph, mode="Rush Hour")

    # ---- Convert inputs to nodes ----
    start_node = place_to_node(graph, start_place, city_context)
    end_node = place_to_node(graph, end_place, city_context)

    if start_node is None or end_node is None:
        st.stop()

    # =======================================================
    # MODE 1 — NORMAL ROUTING
    # =======================================================
    if mode == "Normal":

        path, dist, explored = astar(graph, start_node, end_node, weight='weight')

        st.success(f"Distance: {dist:.2f}")
        st.info(f"A* explored {explored} nodes")

        m = plot_route(graph, path)
        st.components.v1.html(m._repr_html_(), height=500)


    # =======================================================
    # MODE 2 — EMERGENCY
    # =======================================================
    elif mode == "Emergency":

        hospitals = get_hospital_nodes(graph, city_context)

        candidates = bfs_radial_sweep(
            graph, start_node, hospitals, max_hops=50
        )

        pq = rank_hospitals(graph, start_node, candidates)
        best = get_best_hospital(pq)

        if best:
            st.success(f"Selected Hospital Node: {best['hosp_node']}")

            m = plot_emergency_route(
                graph,
                best["path"],
                candidates
            )
            st.components.v1.html(m._repr_html_(), height=500)


    # =======================================================
    # MODE 3 — WAYPOINTS (PETROL PUMPS)
    # =======================================================
    elif mode == "Waypoints":

        pumps = get_petrol_pump_nodes(graph, city_context)

        if len(pumps) == 0:
            st.warning("No petrol pumps found.")
            st.stop()

        num = st.slider("Number of stops", 1, min(5, len(pumps)), 2)

        selected = pumps[:num]   # simple selection (can be improved later)

        path, dist = dijkstra_with_waypoints(
            graph,
            start_node,
            end_node,
            selected,
            weight='weight'
        )

        st.success(f"Distance with stops: {dist:.2f}")

        m = plot_route(graph, path)
        st.components.v1.html(m._repr_html_(), height=500)


    # =======================================================
    # MODE 4 — DISTRESS HANDLING
    # =======================================================
    elif mode == "Distress":

        # simulate breakdown mid-route
        base_path, _, _ = astar(graph, start_node, end_node, weight='weight')

        if len(base_path) < 3:
            st.warning("Route too short for distress simulation.")
            st.stop()

        distress_node = base_path[len(base_path) // 2]

        new_path, dist, explored = handle_distress_signal(
            graph,
            distress_node,
            end_node
        )

        st.warning(f"Distress triggered at node {distress_node}")
        st.success(f"New route distance: {dist:.2f}")

        m = plot_route(graph, new_path)
        st.components.v1.html(m._repr_html_(), height=500)


# ============================================================

from features.waypoints   import get_petrol_pump_nodes, dijkstra_with_waypoints
from features.replacement import handle_distress_signal, find_rendezvous_node
from map.render_t3        import plot_waypoint_route, plot_replacement_route


def run_t3(graph, start_node, end_node):
    """
    Full T3 pipeline. Call this function from the bottom of run.py,
    passing the same graph, start_node, and end_node already used
    by the T1/T2 blocks above.

    PHASE A — Waypoints (features/waypoints.py)
      1. Fetch petrol pump nodes from OSMnx
      2. Run bitmask-DP Dijkstra to visit all pumps en route to hospital
      3. Render route with orange waypoint markers -> waypoint_route.html

    PHASE B — Ambulance Replacement (features/replacement.py)
      4. Simulate distress signal at the midpoint of the waypoint path
      5. Re-run A* from distress node to hospital (handle_distress_signal)
      6. Bidirectional Dijkstra -> find rendezvous handoff node
      7. Render two-segment replacement route -> replacement_route.html

    Args:
        graph      : NetworkX MultiDiGraph — already loaded + weighted in run.py
                     (load_city_graph() + apply_composite_weights() already called)
        start_node : ambulance start node — same start_node used throughout run.py
        end_node   : destination node     — use best["hosp_node"] from T2 block,
                     OR end_node from run.py if T2 hasn't run yet
    """

    print("\n" + "=" * 60)
    print(" T3 — Waypoints + Ambulance Replacement")
    print("=" * 60)

    # ── PHASE A: Waypoints ────────────────────────────────────────────────

    # Step 1: Fetch petrol pump waypoint nodes from OpenStreetMap
    print("\n[T3 STEP 1] Fetching petrol pump waypoints...")
    pump_nodes = get_petrol_pump_nodes(graph, city_name="Pune, India")

    # Limit to first 3 pumps for bitmask DP performance
    # 2^3 = 8 states per node — fast even on a full city graph
    # Increase to 4-5 if you want more pumps (2^5 = 32 states per node)
    pump_nodes = pump_nodes[:3]
    print(f"[T3] Using {len(pump_nodes)} petrol pump waypoints for bitmask DP.")

    # Step 2: Bitmask DP Dijkstra — visit all pumps en route to end_node
    # Returns (path, cost) — same return structure as dijkstra() in dijkstra.py
    print("\n[T3 STEP 2] Running bitmask-DP Dijkstra (waypoints)...")
    path_waypoints, dist_waypoints = dijkstra_with_waypoints(
        graph, start_node, end_node, pump_nodes, weight='weight'
    )
    print(f"[T3] Waypoint route: {len(path_waypoints)} nodes | Cost: {dist_waypoints:.1f}")

    # Step 3: Render waypoint route map
    print("\n[T3 STEP 3] Rendering waypoint route...")
    m_waypoints = plot_waypoint_route(graph, path_waypoints, pump_nodes)
    m_waypoints.save("waypoint_route.html")    # same .save() pattern as run.py
    print("[T3] Saved -> waypoint_route.html")

    # ── PHASE B: Ambulance Replacement ────────────────────────────────────

    # Step 4: Simulate distress at midpoint of waypoint path
    mid_index    = len(path_waypoints) // 2
    distress_node = path_waypoints[mid_index]
    print(f"\n[T3 STEP 4] Simulating distress signal at node {distress_node}")

    # Step 5: Re-run A* from distress node -> hospital
    # handle_distress_signal calls astar() which returns (path, g_score[end], explored)
    # matching: path_astar, dist_astar, explored = astar(graph, start_node, end_node, weight='weight')
    print("\n[T3 STEP 5] Re-routing via A* after distress...")
    path_distress, dist_distress, explored_distress = handle_distress_signal(
        graph, distress_node, end_node, weight='weight'
    )
    print(f"[T3] Re-route: {len(path_distress)} nodes | Cost: {dist_distress:.1f}")
    print(f"[T3] A* explored: {explored_distress} nodes")

    # Step 6: Bidirectional Dijkstra — find rendezvous node
    # find_rendezvous_node returns:
    #   (rendezvous_node, path_to_rv, path_from_hosp, combined_cost)
    print("\n[T3 STEP 6] Finding rendezvous node (bidirectional Dijkstra)...")
    rendezvous_node, path_to_rv, path_from_hosp, combined_cost = find_rendezvous_node(
        graph, distress_node, end_node, weight='weight'
    )

    if rendezvous_node is None:
        print("[T3] ERROR: Could not find rendezvous node.")
        return

    print(f"[T3] Rendezvous node  : {rendezvous_node}")
    print(f"[T3] Combined cost    : {combined_cost:.1f}")
    print(f"[T3] Seg 1 (old amb.) : {len(path_to_rv)} nodes   distress -> rendezvous")
    print(f"[T3] Seg 2 (hospital) : {len(path_from_hosp)} nodes   hospital -> rendezvous")

    # Step 7: Render replacement route map
    print("\n[T3 STEP 7] Rendering replacement route...")
    m_replacement = plot_replacement_route(
        graph, path_to_rv, path_from_hosp, rendezvous_node
    )
    m_replacement.save("replacement_route.html")
    print("[T3] Saved -> replacement_route.html")

    # ── Comparison Output ─────────────────────────────────────────────────
    # Shows DSA speedup: Dijkstra nodes explored vs A* nodes explored
    print("\n" + "=" * 60)
    print(" T3 RESULTS SUMMARY")
    print("=" * 60)
    print(f"  Waypoint route cost    : {dist_waypoints:.1f}")
    print(f"  Petrol pumps visited   : {len(pump_nodes)}")
    print(f"  Distress re-route cost : {dist_distress:.1f}  (A* from mid-route)")
    print(f"  A* explored            : {explored_distress} nodes")
    print(f"  Rendezvous node        : {rendezvous_node}")
    print(f"  Combined handoff cost  : {combined_cost:.1f}")
    print(f"  Files saved            : waypoint_route.html, replacement_route.html")
    print("=" * 60)


# ============================================================
