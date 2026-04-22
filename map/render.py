import folium
from features.reviews import get_all_edge_colours


def plot_route(graph, path):
    # get coordinates of route
    route_coords = [(graph.nodes[n]['y'], graph.nodes[n]['x']) for n in path]

    # center map at start
    start_lat, start_lon = route_coords[0]
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)

    # draw main route
    folium.PolyLine(route_coords, color="blue", weight=5).add_to(m)

    # mark start and end
    folium.Marker(route_coords[0], tooltip="Start",
                  icon=folium.Icon(color="green")).add_to(m)

    folium.Marker(route_coords[-1], tooltip="End",
                  icon=folium.Icon(color="red")).add_to(m)

    return m


def plot_route_with_reviews(graph, path):
    """
    Same as plot_route, but also shows road conditions using colours.
    """

    route_coords = [(graph.nodes[n]['y'], graph.nodes[n]['x']) for n in path]
    start_lat, start_lon = route_coords[0]

    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)

    # get edge colours from review system
    colour_map = get_all_edge_colours(graph)

    # draw all roads with colours (light lines)
    for u, v, data in graph.edges(data=True):
        lat1, lon1 = graph.nodes[u]['y'], graph.nodes[u]['x']
        lat2, lon2 = graph.nodes[v]['y'], graph.nodes[v]['x']

        colour = colour_map.get((u, v), "gray")

        folium.PolyLine(
            [(lat1, lon1), (lat2, lon2)],
            color=colour,
            weight=2,
            opacity=0.5
        ).add_to(m)

    # draw main route on top
    folium.PolyLine(route_coords, color="blue", weight=6).add_to(m)

    # markers
    folium.Marker(route_coords[0], tooltip="Start",
                  icon=folium.Icon(color="green")).add_to(m)

    folium.Marker(route_coords[-1], tooltip="End",
                  icon=folium.Icon(color="red")).add_to(m)

    return m

def plot_emergency_route(graph, path, hospital_nodes):
    if not path:
        return None
    
    route_coords = [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in path]
    start_lat, start_lon = route_coords[0]
    
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
    
    folium.PolyLine(route_coords, color="red", weight=6).add_to(m)
    
    folium.Marker(route_coords[0], tooltip="Ambulance", 
                  icon=folium.Icon(color="blue")).add_to(m)
    
    folium.Marker(route_coords[-1], tooltip="Best Hospital", 
                  icon=folium.Icon(color="red", icon="plus")).add_to(m)
    
    for node in hospital_nodes:
        try:
            lat = graph.nodes[node]['y']
            lon = graph.nodes[node]['x']
            folium.Marker([lat, lon], tooltip="Nearby Hospital", 
                          icon=folium.Icon(color="green", icon="plus")).add_to(m)
        except:
            continue
    
    return m

def plot_waypoint_route(graph, path, waypoint_nodes):
    """
    Draw the ambulance route that passes through petrol pump waypoints.
 
    Visual encoding:
      BLUE polyline   : full route  (same colour as render.py's plot_route)
      GREEN marker    : Start node  (same as render.py)
      RED marker      : End node    (same as render.py)
      ORANGE circles  : Each petrol pump waypoint on the route
 
    Args:
        graph          : NetworkX MultiDiGraph — same as render.py
        path           : list of node IDs from dijkstra_with_waypoints()
        waypoint_nodes : list of petrol pump node IDs from get_petrol_pump_nodes()
 
    Returns:
        m : folium.Map — same return type as render.py's plot_route()
    """
    # Same coordinate extraction as render.py
    route_coords = [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in path]
 
    start_lat, start_lon = route_coords[0]   # same variable names as render.py
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
 
    # Blue polyline — same as render.py
    folium.PolyLine(route_coords, color="blue", weight=5, tooltip="Waypoint Route").add_to(m)
 
    # Start/end markers — same colours and pattern as render.py
    folium.Marker(route_coords[0],  tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(route_coords[-1], tooltip="End",   icon=folium.Icon(color="red")).add_to(m)
 
    # Build waypoint lookup dict — no set() builtin
    waypoint_lookup = {}
    i = 0
    while i < len(waypoint_nodes):
        waypoint_lookup[waypoint_nodes[i]] = True
        i = i + 1
 
    # Orange circle marker for every petrol pump that appears in the path
    j = 0
    while j < len(path):
        node = path[j]
        if node in waypoint_lookup:
            lat = graph.nodes[node]['y']   # 'y' = latitude  (same as render.py)
            lon = graph.nodes[node]['x']   # 'x' = longitude (same as render.py)
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color="orange",
                fill=True,
                fill_color="orange",
                fill_opacity=0.9,
                tooltip="Petrol Pump Waypoint"
            ).add_to(m)
        j = j + 1
 
    return m
 
 
def plot_replacement_route(graph, path_to_rendezvous, path_from_hospital, rendezvous_node):
    """
    Draw the two-segment handoff route after an ambulance distress signal.
 
    Visual encoding:
      BLUE polyline   : Distressed ambulance -> Rendezvous node
      PURPLE polyline : Replacement ambulance (from hospital) -> Rendezvous node
      GREEN marker    : Distress location (start of segment 1)
      RED marker      : Hospital (start of segment 2)
      ORANGE marker   : Rendezvous / handoff point
 
    Args:
        graph                : NetworkX MultiDiGraph — same as render.py
        path_to_rendezvous   : list of node IDs  distress_node -> rendezvous
                               (path_to_rv from find_rendezvous_node())
        path_from_hospital   : list of node IDs  hospital_node -> rendezvous
                               (path_from_hosp from find_rendezvous_node())
        rendezvous_node      : handoff node ID
                               (rendezvous_node from find_rendezvous_node())
 
    Returns:
        m : folium.Map — same return type as render.py's plot_route()
    """
    # Same coordinate extraction pattern as render.py
    seg1_coords = [(graph.nodes[n]['y'], graph.nodes[n]['x']) for n in path_to_rendezvous]
    seg2_coords = [(graph.nodes[n]['y'], graph.nodes[n]['x']) for n in path_from_hospital]
 
    # Pick map centre
    if len(seg1_coords) > 0:
        start_lat, start_lon = seg1_coords[0]
    elif len(seg2_coords) > 0:
        start_lat, start_lon = seg2_coords[0]
    else:
        print("[T3] WARNING: Both path segments empty — cannot render replacement route.")
        return None
 
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
 
    # Segment 1: distressed ambulance -> rendezvous (BLUE)
    if len(seg1_coords) > 0:
        folium.PolyLine(
            seg1_coords, color="blue", weight=5,
            tooltip="Distressed Ambulance to Rendezvous"
        ).add_to(m)
        folium.Marker(
            seg1_coords[0],
            tooltip="Distress Location",
            icon=folium.Icon(color="green")   # green = start, same as render.py
        ).add_to(m)
 
    # Segment 2: hospital -> rendezvous (PURPLE)
    if len(seg2_coords) > 0:
        folium.PolyLine(
            seg2_coords, color="purple", weight=5,
            tooltip="Replacement Ambulance from Hospital"
        ).add_to(m)
        folium.Marker(
            seg2_coords[0],
            tooltip="Hospital (Replacement Origin)",
            icon=folium.Icon(color="red")     # red = destination/hospital, same as render.py
        ).add_to(m)
 
    # Rendezvous marker — orange, clearly different from start/end colours
    rendezvous_lat = graph.nodes[rendezvous_node]['y']
    rendezvous_lon = graph.nodes[rendezvous_node]['x']
    folium.Marker(
        [rendezvous_lat, rendezvous_lon],
        tooltip="Rendezvous / Handoff Point",
        icon=folium.Icon(color="orange")
    ).add_to(m)
 
    return m
