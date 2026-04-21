import heapq

def dijkstra(graph, start, end, weight='weight'):
    """
    Standard Dijkstra's algorithm using the given edge weight.
    Defaults to 'weight' so it works with composite weights.
    """

    pq = [(0, start)]  # (distance, node)

    # initialize distances
    distances = {node: float('inf') for node in graph.nodes}
    distances[start] = 0

    # parent tracking for path reconstruction
    parent = {node: None for node in graph.nodes}

    while pq:
        current_distance, current_node = heapq.heappop(pq)

        # skip outdated entries
        if current_distance > distances[current_node]:
            continue

        if current_node == end:
            break

        for neighbor in graph.neighbors(current_node):
            edge_data = graph.get_edge_data(current_node, neighbor)

            # manually find minimum weight among parallel edges
            min_weight = float('inf')
            for key in edge_data:
                d = edge_data[key]
                if weight in d:
                    w = d[weight]
                elif 'length' in d:
                    w = d['length']
                else:
                    w = 1

                if w < min_weight:
                    min_weight = w

            new_dist = current_distance + min_weight

            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = current_node
                heapq.heappush(pq, (new_dist, neighbor))
            if distances[end] == float('inf'):
                return None, float('inf')

    # reconstruct path
    path = []
    node = end

    while node is not None:
        path.append(node)
        node = parent[node]

    path.reverse()

    return path, distances[end]
def dijkstra_all(graph, start, weight='weight'):
    """
    One-to-All Dijkstra. 
    Calculates the shortest paths from a start node to ALL other nodes in the graph simultaneously.
    """
    pq = [(0, start)]
    distances = {node: float('inf') for node in graph.nodes}
    distances[start] = 0
    parent = {node: None for node in graph.nodes}

    while pq:
        current_distance, current_node = heapq.heappop(pq)

        # skip outdated entries
        if current_distance > distances[current_node]:
            continue

        # NOTICE: We removed the "if current_node == end: break" part!
        # We want it to map out the entire nearby area.

        for neighbor in graph.neighbors(current_node):
            edge_data = graph.get_edge_data(current_node, neighbor)

            # manually find minimum weight among parallel edges
            min_weight = float('inf')
            for key in edge_data:
                d = edge_data[key]
                w = d.get(weight, d.get('length', 1))
                if w < min_weight:
                    min_weight = w

            new_dist = current_distance + min_weight

            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = current_node
                heapq.heappush(pq, (new_dist, neighbor))

    # Return the entire map of distances and parents
    return distances, parent