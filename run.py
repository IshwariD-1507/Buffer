from graph.loader import load_city_graph
from graph.dijkstra import dijkstra
from graph.weights import apply_composite_weights
from graph.astar import astar
from map.render import plot_route

import osmnx as ox

# -----------------------
# Load graph ONCE
# -----------------------
graph = load_city_graph()
print("Graph loaded successfully!")

# -----------------------
# Coordinates (your example)
# -----------------------
start_point = (18.53, 73.86)
end_point = (18.5208, 73.8554)

# Convert to nearest nodes
start_node = ox.distance.nearest_nodes(graph, start_point[1], start_point[0])
end_node = ox.distance.nearest_nodes(graph, end_point[1], end_point[0])

# -----------------------
# Apply composite weights
# -----------------------
graph = apply_composite_weights(graph, mode="Rush Hour")

# -----------------------
# Run Dijkstra (with weight)
# -----------------------
path_dij, dist_dij = dijkstra(graph, start_node, end_node, weight='weight')

# -----------------------
# Run A* (IMPORTANT: 3 outputs)
# -----------------------
path_astar, dist_astar, explored = astar(graph, start_node, end_node, weight='weight')

# -----------------------
# Comparison
# -----------------------
print("\n===== COMPARISON =====")
print("Dijkstra Distance:", dist_dij)
print("A* Distance:", dist_astar)
print("A* Nodes Explored:", explored)
print("Dijkstra Path Length:", len(path_dij))

# -----------------------
# Plot A* route
# -----------------------
m = plot_route(graph, path_astar)

# Save map
m.save("route.html")
print("Map saved as route.html")
