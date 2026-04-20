import os
import osmnx as ox

# -------------------------------------------------------
# Download graph for a specific city
# -------------------------------------------------------
def download_city(city_name, network_type="drive"):
    print(f"Downloading map for {city_name}...")

    graph = ox.graph_from_place(city_name, network_type=network_type)
    graph = ox.add_edge_lengths(graph)

    os.makedirs("data", exist_ok=True)

    # file name based on city
    file_name = f"data/{city_name.replace(',', '').replace(' ', '_')}.graphml"

    ox.save_graphml(graph, file_name)

    print(f"Saved → {file_name}")
    print(f"Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")

    return graph


# -------------------------------------------------------
# Load graph (or download if not present)
# -------------------------------------------------------
def load_city_graph(city_name):
    file_name = f"data/{city_name.replace(',', '').replace(' ', '_')}.graphml"

    if os.path.exists(file_name):
        print(f"Loading saved graph for {city_name}...")
        graph = ox.load_graphml(file_name)
        print(f"Loaded. Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")
        return graph
    else:
        return download_city(city_name)

