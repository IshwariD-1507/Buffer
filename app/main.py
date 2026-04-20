import streamlit as st
import osmnx as ox

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