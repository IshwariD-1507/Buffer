import folium

def plot_route(graph, path):
    route_coords= [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in path]  #gets the coordinates of the nodes in the path
    start_lat, start_lon=route_coords[0]
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
    folium.PolyLine(route_coords, color="blue", weight=5).add_to(m)   #draws the route on the map with a blue line
    folium.Marker(route_coords[0], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)  #marks the start point of the route with a green marker
    folium.Marker(route_coords[-1], tooltip="End", icon=folium.Icon(color="red")).add_to(m)  #marks the end point of the route with a red marker

    return m  #returns the map object with the route plotted on it