import random
def apply_composite_weights(graph, mode="Normal"):      #graph is imported file and mode is how heavy the traffic is normal or rush hour etc        
    for u, v, edge_data in graph.edges(data=True):     #loops through all the edges in the graph and gets the data associated with each edge
        base_length= edge_data.get('length',1)  #gets the length of the edge, if not available defaults to 1

        if mode== "Normal":
            traffic_mult= random.uniform(1, 1.5) #random multiplier for traffic between 1 and 1.5
        elif mode== "Rush Hour":
            traffic_mult= random.uniform(2, 3) #random multiplier for traffic between 1.5 and 2.5
        elif mode == "Emergency":
            traffic_mult = random.uniform(1.2, 2) * 0.7  #random multiplier for traffic between 1.2 and 2, then reduced by 30% to simulate emergency conditions
        else:
            traffic_mult = 1
        
        crowd_penalty=random.uniform(0, 50)  #random penalty for crowd between 0 and 50
        road_quality_penalty = random.uniform(0, 30)   #random penalty for road quality between 0 and 30
        
        edge_data["weight"] = base_length * traffic_mult + crowd_penalty + road_quality_penalty  #calculates the composite weight for the edge based on length, traffic multiplier, crowd penalty, and road quality penalty

    return graph  #returns the graph with updated weights for each edge     

