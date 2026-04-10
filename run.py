from graph.loader import load_city_graph
graph= load_city_graph()
print("Graph loaded successfully!")


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

from map.render import plot_route
import osmnx as ox

graph = load_city_graph()

# Convert place to nearest node
start_point = (18.5204, 73.8567)  # Pune example
end_point = (18.5314, 73.8446)

start_node = ox.distance.nearest_nodes(graph, start_point[1], start_point[0])
end_node = ox.distance.nearest_nodes(graph, end_point[1], end_point[0])

# Run Dijkstra
path, dist = dijkstra(graph, start_node, end_node)

print("Distance:", dist)

# Plot map
m = plot_route(graph, path)

# Save map
m.save("route.html")

print("Map saved as route.html")