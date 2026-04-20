import random
from features.reviews import get_edge_penalty


def apply_composite_weights(graph, mode="Normal"):
    """
    Adds a realistic weight to each edge by combining
    distance, traffic, road conditions, and user reviews.
    """

    for u, v, edge_data in graph.edges(data=True):

        # base distance of the road
        base_length = edge_data.get('length', 1)

        # simulate traffic conditions
        if mode == "Normal":
            traffic_mult = random.uniform(1, 1.5)
        elif mode == "Rush Hour":
            traffic_mult = random.uniform(2, 3)
        elif mode == "Emergency":
            # slightly relaxed traffic for emergency vehicles
            traffic_mult = random.uniform(1.2, 2) * 0.7
        else:
            traffic_mult = 1

        # random real-world factors
        crowd_penalty = random.uniform(0, 50)
        road_quality_penalty = random.uniform(0, 30)

        # penalty from user reviews (potholes, traffic, etc.)
        review_penalty = get_edge_penalty((u, v))

        # final weight used by routing algorithms
        edge_data["weight"] = (
            base_length * traffic_mult
            + crowd_penalty
            + road_quality_penalty
            + review_penalty
        )

    return graph