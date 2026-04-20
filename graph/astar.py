import heapq
import math


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )

    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def astar(graph, start, end, weight='weight'):
    """
    A* search using composite weights.
    Heuristic = haversine distance.
    """

    pq = [(0, start)]  # (f_score, node)

    g_score = {node: float('inf') for node in graph.nodes}
    g_score[start] = 0

    parent = {node: None for node in graph.nodes}

    explored = 0

    while pq:
        _, current_node = heapq.heappop(pq)
        explored += 1

        if current_node == end:
            break

        # skip outdated entries
        if g_score[current_node] == float('inf'):
            continue

        for neighbor in graph.neighbors(current_node):
            edge_data = graph.get_edge_data(current_node, neighbor)

            # manual min weight (consistent with dijkstra)
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

            tentative_g = g_score[current_node] + min_weight

            if tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                parent[neighbor] = current_node

                lat1 = graph.nodes[neighbor]['y']
                lon1 = graph.nodes[neighbor]['x']
                lat2 = graph.nodes[end]['y']
                lon2 = graph.nodes[end]['x']

                h = haversine(lat1, lon1, lat2, lon2)

                f = tentative_g + h

                heapq.heappush(pq, (f, neighbor))

    # no path case
    if g_score[end] == float('inf'):
        return None, float('inf'), explored

    # reconstruct path
    path = []
    node = end

    while node is not None:
        path.append(node)
        node = parent[node]

    path.reverse()

    return path, g_score[end], explored