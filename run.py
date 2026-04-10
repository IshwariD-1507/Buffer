from graph.loader import load_city_graph
graph= load_city_graph()
print("Graph loaded successfully!")

from graph.loader import load_city_graph
from graph.dijkstra import dijkstra
import osmnx as ox

graph = load_city_graph()

# Example: pick random nodes
nodes = list(graph.nodes)
start = nodes[0]
end = nodes[100]

path, dist = dijkstra(graph, start, end)

print("Distance:", dist)
print("Path length:", len(path))