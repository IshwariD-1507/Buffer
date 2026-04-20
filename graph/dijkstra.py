import heapq
def dijkstra(graph, start, end, weight= 'length'):
    pq= [(0,start)]      #(distance, node)
    distances= {node: float('inf') for node in graph.nodes}  #inf is infinity as we set the initial distance of any node to infinity
    distances[start]= 0
    parent= {node: None for node in graph.nodes}
    while pq:
        current_distance, current_node= heapq.heappop(pq)   #Pops the node with smallest distance
        if current_node== end:
            break
        for neighbor in graph.neighbors(current_node):       #gets all the nodes in the network connected
            edge_data= graph.get_edge_data(current_node, neighbor)   #gets the data associated with the edge between current_node and neighbor
            min_weight= min([d.get(weight,1) for d in edge_data.values()]) #gets the minimum weight of the edge between current_node and neighbor
            new_dist= current_distance + min_weight
            if new_dist< distances[neighbor]:
                distances[neighbor] = new_dist
                parent[neighbor] = current_node
                heapq.heappush(pq, (new_dist, neighbor))  #pushes the neighbor with the new distance into the priority queue
    path= []
    node= end
    while node is not None:
        path.append(node)
        node= parent[node]
            
    path.reverse()  #reverses the path to get the correct order from start to end
    return path, distances[end]  #returns the shortest path and its total distance




