import osmnx as ox
import networkx as nx   
import os

def download_city(city_name="Pune, India", network_type="drive"):
    print(f"Downloading the maps for {city_name}...")
    graph = ox.graph_from_place(city_name, network_type=network_type)
    os.makedirs("data", exist_ok=True)
    ox.save_graphml(graph, "data/city.graphml") #ox.save_graphml() is used to save a street network graph to a file in GraphML format.
    print(f"Done. Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")
    return graph

def load_city_graph():
    if os.path.exists("data/city.graphml"):
        print("Loading saved city graph...")
        graph= ox.load_graphml("data/city.graphml") #ox.load_graphml() is used to load a street network graph from a GraphML file.
        print(f"Loaded. Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")
        return graph
    else:
        return download_city()
    


