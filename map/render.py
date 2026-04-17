import folium

def plot_route(graph, path):
    route_coords= [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in path]  #gets the coordinates of the nodes in the path
    start_lat, start_lon=route_coords[0]
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
    folium.PolyLine(route_coords, color="blue", weight=5).add_to(m)   #draws the route on the map with a blue line
    folium.Marker(route_coords[0], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)  #marks the start point of the route with a green marker
    folium.Marker(route_coords[-1], tooltip="End", icon=folium.Icon(color="red")).add_to(m)  #marks the end point of the route with a red marker

    return m  #returns the map object with the route plotted on it
def plot_emergency_route(graph, path, candidate_hospitals, output_file="emergency_route.html"):
    """
    Renders the emergency route on an interactive Folium map.

    Visual scheme:
        🔵  Blue marker       — Ambulance current position (path[0])
        🟢  Green circle      — Candidate hospitals found by BFS
        🟢  Green cross       — Best / selected hospital (path[-1])
        🔴  Red polyline      — Optimal route from ambulance to best hospital

    Args:
        graph               : NetworkX MultiDiGraph
        path                : Ordered list of node IDs (ambulance → best hospital)
        candidate_hospitals : List of all candidate hospital node IDs (from BFS)
        output_file         : Filename to save the HTML map (default: emergency_route.html)

    Returns:
        m (folium.Map)      : The rendered Folium map object
    """
    if not path:
        print("[RENDER] ERROR: Path is empty — nothing to render.")
        return None

    # -----------------------------------------------------------------------
    # Extract coordinates for the route
    # -----------------------------------------------------------------------
    route_coords = []
    for node_id in path:
        node_data = graph.nodes[node_id]
        lat = node_data['y']
        lon = node_data['x']
        route_coords.append((lat, lon))

    # Centre the map on the midpoint of the route
    mid_idx = len(route_coords) // 2
    map_center = route_coords[mid_idx]

    m = folium.Map(location=map_center, zoom_start=14, tiles="OpenStreetMap")

    # -----------------------------------------------------------------------
    # Draw the emergency route — bold red polyline
    # -----------------------------------------------------------------------
    folium.PolyLine(
        locations=route_coords,
        color="red",
        weight=6,
        opacity=0.85,
        tooltip="🚑 Emergency Route",
    ).add_to(m)

    # -----------------------------------------------------------------------
    # Ambulance start marker — blue icon
    # -----------------------------------------------------------------------
    start_lat, start_lon = route_coords[0]
    folium.Marker(
        location=(start_lat, start_lon),
        popup=folium.Popup("<b>🚑 Ambulance Position</b>", max_width=200),
        tooltip="Ambulance",
        icon=folium.Icon(color="blue", icon="ambulance", prefix="fa"),
    ).add_to(m)

    # -----------------------------------------------------------------------
    # All candidate hospitals — small green circle markers
    # -----------------------------------------------------------------------
    best_hospital_node = path[-1]

    for hosp_node in candidate_hospitals:
        # Skip the best hospital — it gets its own prominent marker below
        if hosp_node == best_hospital_node:
            continue

        node_data = graph.nodes[hosp_node]
        hosp_lat = node_data['y']
        hosp_lon = node_data['x']

        folium.CircleMarker(
            location=(hosp_lat, hosp_lon),
            radius=8,
            color="green",
            fill=True,
            fill_color="lightgreen",
            fill_opacity=0.7,
            popup=folium.Popup(f"<b>🏥 Candidate Hospital</b><br>Node: {hosp_node}", max_width=200),
            tooltip=f"Candidate Hospital ({hosp_node})",
        ).add_to(m)

    # -----------------------------------------------------------------------
    # Best / selected hospital — prominent green cross marker
    # -----------------------------------------------------------------------
    dest_lat, dest_lon = route_coords[-1]
    folium.Marker(
        location=(dest_lat, dest_lon),
        popup=folium.Popup(
            f"<b>🏥 SELECTED HOSPITAL</b><br>Node: {best_hospital_node}<br>"
            "<i>Optimal destination based on travel time & bed availability</i>",
            max_width=250,
        ),
        tooltip="✅ Best Hospital",
        icon=folium.Icon(color="green", icon="plus-sign", prefix="glyphicon"),
    ).add_to(m)

    # -----------------------------------------------------------------------
    # Save to file
    # -----------------------------------------------------------------------
    m.save(output_file)
    print(f"[RENDER] Emergency route map saved → {output_file}")

    return m
