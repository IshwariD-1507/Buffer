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