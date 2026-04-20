import heapq
import time

# ============================================================
# features/reviews.py  — Teammate 1
#
# DSA Concepts:
#   1. Max-Heap per edge  — stores the last 50 user reviews per road edge.
#      Python's heapq is a min-heap, so we negate scores to simulate max-heap.
#      Each review = (score, timestamp, type)
#      type can be: "pothole", "construction", "traffic", "clear"
#
#   2. Time-Decay Scoring Formula:
#      score = sum(review_i x 0.95^(now - time_i))
#      Newer reviews count more; old ones fade exponentially.
#
#   3. Edge Penalty → plugs into graph/weights.py composite weight formula.
#      get_edge_penalty(edge) returns a float added to Dijkstra edge weight.
#
#   4. Colour overlay → map/render.py colours roads red/orange/green
#      based on the review penalty score of each edge.
#
# Variable naming mirrors dijkstra.py / replacement.py / waypoints.py:
#   pq, current_node, neighbor, edge_data, weight, new_dist, path, etc.
# ============================================================

# ---------------------------------------------------------------------------
# Global review store
# ---------------------------------------------------------------------------

# review_store[(u, v)] = list of (negated_score, timestamp, review_type)
# Stored as a MIN-heap on negated scores → behaves as a MAX-heap on real scores.
# "u → v" edge key matches the directed edge format used in dijkstra.py.
review_store = {}       # { (u, v) : [(-score, timestamp, review_type), ...] }

MAX_REVIEWS_PER_EDGE = 50   # cap — same spirit as the 50-review limit in the spec


# ---------------------------------------------------------------------------
# 1. add_review  — add a review to the max-heap for an edge
# ---------------------------------------------------------------------------

def add_review(edge, score, review_type):
    """
    Adds a user review to the max-heap for the given directed edge,
    then recalculates the edge penalty so Dijkstra picks it up immediately.

    Max-Heap simulation:
        Python's heapq is a min-heap.
        We negate `score` before pushing so that heapq.heappop()
        always returns the HIGHEST real score first — same trick used
        in rank_hospitals() in emergency.py where heappush stores
        (final_score, ...) and the lowest score wins.

    Review tuple stored:
        (-score, timestamp, review_type)
        Negation  → simulates max-heap on score.
        Timestamp → used by time-decay formula in get_edge_penalty().
        Type      → "pothole" | "construction" | "traffic" | "clear"

    Args:
        edge        : tuple (u, v) — directed edge, same format as
                      graph.get_edge_data(u, v) calls in dijkstra.py
        score       : float in [0, 10] — 10 = perfect road, 0 = terrible
        review_type : str — one of "pothole", "construction", "traffic", "clear"

    Side effects:
        Updates review_store[(u, v)].
        If heap exceeds MAX_REVIEWS_PER_EDGE, the lowest-scored review
        (least negative = most negative real score when inverted) is dropped
        to keep the heap bounded at 50 entries.
    """
    u, v = edge     # unpack directed edge — same pattern as (u, v, data) in weights.py

    # Initialise heap for this edge if not seen before
    if (u, v) not in review_store:
        review_store[(u, v)] = []

    heap = review_store[(u, v)]

    # Current timestamp — seconds since epoch (float)
    # Same role as `now` in the time-decay formula: 0.95^(now - time_i)
    now = time.time()

    # Negate score → min-heap behaves as max-heap on real scores
    negated_score = -score

    heapq.heappush(heap, (negated_score, now, review_type))

    # ── Bounded heap: keep only the last MAX_REVIEWS_PER_EDGE entries ──
    # If over the cap, drop the entry with the LOWEST real score
    # (= the HIGHEST negated score in the min-heap = the root after inversion).
    # We rebuild the heap after removal to maintain heap invariant.
    if len(heap) > MAX_REVIEWS_PER_EDGE:
        # Find and remove the entry with the highest negated_score
        # (= lowest real score = least useful review)
        max_neg = heap[0][0]    # root of min-heap = smallest negated = worst review
        max_neg_idx = 0
        i = 1
        while i < len(heap):
            if heap[i][0] > max_neg:    # manual max search — no max() builtin
                max_neg = heap[i][0]
                max_neg_idx = i
            i = i + 1

        # Swap with last element and pop (standard heap deletion pattern)
        heap[max_neg_idx] = heap[-1]
        heap.pop()
        heapq.heapify(heap)     # restore heap invariant after deletion

    print(f"  [REVIEW] Edge ({u} → {v}) | Type: {review_type} | "
          f"Score: {score} | Heap size: {len(heap)}")

    # Recalculate and display updated penalty immediately
    penalty = get_edge_penalty(edge)
    print(f"  [REVIEW] Updated penalty for edge ({u} → {v}): {penalty:.4f}")


# ---------------------------------------------------------------------------
# 2. _time_decay_score  — time-decay formula (internal helper)
# ---------------------------------------------------------------------------

def _time_decay_score(heap):
    """
    Applies the time-decay scoring formula across all reviews in a heap:

        score = sum(review_i × 0.95^(now - time_i))

    where:
        review_i  = real (positive) score of review i
        time_i    = Unix timestamp when review i was submitted
        now       = current Unix timestamp
        0.95      = decay factor — reviews fade by 5% per second
                    (in a real system, time_i would be in hours/days;
                     here seconds are used for testability)

    Newer reviews (small now - time_i) → exponent near 0 → weight near 1.0
    Older reviews (large now - time_i) → exponent large → weight near 0.

    Variable names mirror the formula exactly:
        now, time_i, review_i, decay, weighted_sum

    Args:
        heap : list of (-score, timestamp, review_type) tuples
               (the raw heap from review_store — scores are negated)

    Returns:
        weighted_sum : float — time-decayed aggregate score
                       Higher = better road condition.
                       Lower  = more penalised by Dijkstra.
    """
    now = time.time()       # current time — same `now` as in add_review()

    weighted_sum = 0.0      # accumulator for sum(review_i × 0.95^(now - time_i))

    i = 0
    while i < len(heap):
        negated_score, time_i, review_type = heap[i]   # unpack stored tuple
        review_i = -negated_score                       # un-negate to get real score

        delta = now - time_i                            # age of review in seconds
        decay = 0.95 ** delta                           # exponential decay factor

        weighted_sum = weighted_sum + (review_i * decay)    # accumulate

        i = i + 1

    return weighted_sum


# ---------------------------------------------------------------------------
# 3. get_edge_penalty  — penalty plugged into Dijkstra weight
# ---------------------------------------------------------------------------

def get_edge_penalty(edge):
    """
    Returns a float penalty for the given directed edge to be ADDED
    to its Dijkstra weight in graph/weights.py's composite formula.

    Integration point (graph/weights.py):
        composite_weight = base_length + traffic_penalty + get_edge_penalty(edge)
    (Same pattern as how bed_score is factored into final_score in emergency.py:
        final_score = (0.6 * travel_time) - (0.4 * bed_score))

    Penalty formula:
        If no reviews → penalty = 0.0  (no data, no penalty)
        Else:
            decayed_score = _time_decay_score(heap)   ← higher = better road
            normalised    = decayed_score / len(heap) ← average per review
            penalty       = max(0, 10 - normalised)   ← invert: bad road → high penalty

    Score=10 (perfect road) → penalty = 0.0   (Dijkstra won't avoid it)
    Score=0  (pothole-ridden) → penalty = 10.0 (Dijkstra strongly avoids it)

    Args:
        edge : tuple (u, v) — directed edge key, same format as graph.get_edge_data(u, v)

    Returns:
        penalty : float ≥ 0.0
    """
    u, v = edge

    if (u, v) not in review_store:
        return 0.0      # no reviews → no penalty → Dijkstra unaffected

    heap = review_store[(u, v)]

    if len(heap) == 0:
        return 0.0

    decayed_score = _time_decay_score(heap)     # sum of time-decayed scores

    # Normalise by number of reviews to get average decayed score
    normalised = decayed_score / len(heap)

    # Invert: a score of 10 = perfect road → 0 penalty
    #         a score of 0  = terrible road → 10 penalty
    penalty = 10.0 - normalised

    # Clamp to [0, inf) — penalty can't be negative (a great road doesn't help Dijkstra)
    if penalty < 0.0:
        penalty = 0.0

    return penalty


# ---------------------------------------------------------------------------
# 4. get_edge_colour  — colour overlay for map/render.py
# ---------------------------------------------------------------------------

def get_edge_colour(edge):
    """
    Returns a colour string for map/render.py to colour the road overlay.

    Colour mapping based on get_edge_penalty():
        penalty < 2.0           → "green"   (clear / good road)
        2.0 ≤ penalty < 5.0     → "orange"  (moderate issues)
        penalty ≥ 5.0           → "red"     (severe: pothole / construction)

    This plugs directly into map/render.py's edge colouring loop:
        for u, v, data in graph.edges(data=True):
            colour = get_edge_colour((u, v))
            # draw edge with `colour`

    Args:
        edge : tuple (u, v) — directed edge key

    Returns:
        colour : str — "green", "orange", or "red"
    """
    penalty = get_edge_penalty(edge)

    if penalty < 2.0:
        return "green"
    elif penalty < 5.0:
        return "orange"
    else:
        return "red"


# ---------------------------------------------------------------------------
# 5. get_all_edge_colours  — bulk colour fetch for map/render.py
# ---------------------------------------------------------------------------

def get_all_edge_colours(graph):
    """
    Iterates over every directed edge in the road graph and returns
    a colour dict for use in map/render.py's rendering loop.

    Variable names mirror dijkstra.py / waypoints.py:
        u, v, data (from graph.edges(data=True))
        edge_data  (same as graph.get_edge_data(u, v) pattern)

    Args:
        graph : road network (NetworkX MultiDiGraph) — same graph passed
                through run.py → dijkstra → weights → here

    Returns:
        colour_map : dict { (u, v): colour_str }
                     e.g. { (123, 456): "red", (456, 789): "green", ... }
    """
    colour_map = {}

    for u, v, data in graph.edges(data=True):   # same iteration as weights.py
        edge = (u, v)
        colour_map[edge] = get_edge_colour(edge)

    return colour_map


# ---------------------------------------------------------------------------
# 6. Test helper — verify route changes after pothole review
# ---------------------------------------------------------------------------

def test_pothole_reroute(graph, start_node, end_node, pothole_edge, weight='weight'):
    """
    Test: add a "pothole" review to an edge, call Dijkstra again,
    verify the route changes to avoid that road.

    Mirrors the test described in the spec image:
        1. Run Dijkstra → record original path.
        2. Add a pothole review to one edge on that path.
        3. Re-run Dijkstra → confirm the penalised edge is avoided.

    Uses the same dijkstra import pattern as handle_distress_signal()
    in replacement.py (imported inside function to avoid circular imports).

    Args:
        graph         : road network (NetworkX MultiDiGraph)
        start_node    : ambulance / route start node ID
        end_node      : destination node ID (e.g. hospital from T2)
        pothole_edge  : tuple (u, v) — edge to receive the pothole review
        weight        : edge attribute key — 'weight' from weights.py

    Returns:
        original_path : list of node IDs before pothole review
        new_path      : list of node IDs after pothole review
        avoided       : bool — True if pothole_edge is absent from new_path
    """
    from graph.dijkstra import dijkstra     # same import style as replacement.py

    print("\n[TEST] ── Pothole Reroute Test ──────────────────────────────")

    # Step 1: Dijkstra before any review
    original_path, original_dist = dijkstra(graph, start_node, end_node)
    print(f"[TEST] Original path length : {len(original_path)} nodes | "
          f"Cost: {original_dist:.1f}")

    # Step 2: Add a severe pothole review (score=0 = worst possible)
    u, v = pothole_edge
    print(f"[TEST] Adding pothole review to edge ({u} → {v})...")
    add_review(pothole_edge, score=0.0, review_type="pothole")

    # Step 3: Re-run Dijkstra — penalty from get_edge_penalty() must be
    # picked up by graph/weights.py before this call in a real pipeline.
    # Here we assume weights.py re-queries get_edge_penalty() each run.
    new_path, new_dist = dijkstra(graph, start_node, end_node)
    print(f"[TEST] New path length      : {len(new_path)} nodes | "
          f"Cost: {new_dist:.1f}")

    # Step 4: Check if pothole edge is avoided in the new path
    # Manual scan — no `in` on tuples to keep DSA logic visible
    avoided = True
    i = 0
    while i < len(new_path) - 1:
        if new_path[i] == u and new_path[i + 1] == v:
            avoided = False     # pothole edge still used — test fails
            break
        i = i + 1

    if avoided:
        print(f"[TEST] ✅ PASS — pothole edge ({u} → {v}) successfully avoided.")
    else:
        print(f"[TEST] ❌ FAIL — pothole edge ({u} → {v}) still in new path.")

    print("[TEST] ────────────────────────────────────────────────────────\n")

    return original_path, new_path, avoided