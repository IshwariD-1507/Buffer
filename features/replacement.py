import networkx as nx
from graph.astar import astar  # reuse existing A*


# 🔹 Find the best ambulance (closest to emergency)
def find_best_ambulance(graph, emergency_node, ambulances):
    best = None
    min_dist = float('inf')

    for amb in ambulances:
        try:
            dist = nx.shortest_path_length(graph, amb, emergency_node, weight='length')
            if dist < min_dist:
                min_dist = dist
                best = amb
        except:
            continue

    return best


# 🔹 Bidirectional Dijkstra to find optimal rendezvous point
def find_rendezvous_point(graph, start, end):
    forward = nx.single_source_dijkstra_path_length(graph, start, weight='length')
    backward = nx.single_source_dijkstra_path_length(graph.reverse(copy=True), end, weight='length')

    best_node = None
    best_cost = float('inf')

    for node in graph.nodes:
        if node in forward and node in backward:
            cost = forward[node] + backward[node]
            if cost < best_cost:
                best_cost = cost
                best_node = node

    return best_node


# 🔹 Handle ambulance distress and reroute using A*
def handle_distress(graph, current_node, hospital):
    rendezvous = find_rendezvous_point(graph, current_node, hospital)

    # Safety check
    if rendezvous is None:
        return [], [], None

    try:
        path1 = astar(graph, current_node, rendezvous)
        path2 = astar(graph, rendezvous, hospital)
    except:
        return [], [], None

    return path1, path2, rendezvous
