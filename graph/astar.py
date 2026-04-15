import heapq
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000     #radius earth
    phi1= math.radians(lat1)     #converting latitute coordinates from degrees to radians
    phi2= math.radians(lat2)
    dphi = math.radians(lat2 - lat1)    
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2    #haversine formula to calculate the great-circle distance between two points on a sphere given their longitudes and latitudes
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))   #returns the distance in meters

def astar(graph, start, end, weight='length'):
    pq = [(0, start)]     #(f_score, node)
    g_score = {node: float('inf') for node in graph.nodes}  #g_score is the cost from start to current node
    g_score[start] = 0  
    parent = {node: None for node in graph.nodes} #parent dictionary to reconstruct the path
    explored = 0  #Counts how many nodes A* visits

    while pq:
        _, current = heapq.heappop(pq)     #Pops the node with the lowest f_score
        explored += 1
        if current == end:
            break
        for neighbor in graph.neighbors(current):
            edge_data = graph.get_edge_data(current, neighbor)   #gets the data associated with the edge between current and neighbor
            min_weight = min([d.get(weight, 1) for d in edge_data.values()])  #gets the minimum weight of the edge between current and neighbor
            tentative_g = g_score[current] + min_weight  #tentative g_score for the neighbor
            if tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                parent[neighbor] = current
                lat1 = graph.nodes[neighbor]['y']
                lon1 = graph.nodes[neighbor]['x']
                lat2 = graph.nodes[end]['y']
                lon2 = graph.nodes[end]['x']
                h = haversine(lat1, lon1, lat2, lon2)  #heuristic estimate of the distance from neighbor to end
                f = tentative_g + h     #A* formula
                heapq.heappush(pq, (f, neighbor))   #pushes the neighbor with its f_score into the priority queue
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = parent[node]

    path.reverse()

    return path, g_score[end], explored