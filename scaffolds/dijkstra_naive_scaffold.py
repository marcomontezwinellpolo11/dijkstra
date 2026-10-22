# ──────────────────────────────────────────────────────────────────────────────
# dijkstra_naive.py
#
# You will implement Dijkstra's algorithm here using only plain Python
# data structures.
#
# The approach: keep a set of unvisited nodes. Each iteration, scan the
# entire set to find the unvisited node with the lowest known distance.
# This is called the "naive" or "unvisited set" approach.
#
# Once you have this working, move on to dijkstra_heap.py.
# ──────────────────────────────────────────────────────────────────────────────


def dijkstra_naive(graph, start):
    """
    Run Dijkstra's algorithm using an unvisited-set scan (no heap).

    Each iteration, find the unvisited node with the smallest known distance
    by scanning all unvisited nodes — a simple loop, no special data structure.

    Args:
        graph (WeightedGraph): the graph to search
        start: the node to start from

    Returns:
        (dist, prev, op_count) where:
            dist      — dict mapping each node to its shortest distance from start.
                        Unreachable nodes map to float('inf').
            prev      — dict mapping each node to the previous node on the
                        shortest path. The start node maps to None.
            op_count  — int, total number of "scan steps" performed while
                        searching for the minimum each iteration. Used to
                        demonstrate the cost of the naive approach.
    """
    # --- Step 1: Initialize distances and prev ---
    # Every node starts at infinity except start, which is 0.
    dist = {node: float('inf') for node in graph.get_nodes()}
    dist[start] = 0
    prev = {node: None for node in graph.get_nodes()}

    # --- Step 2: Set up the unvisited set ---
    # All nodes begin as unvisited.
    unvisited = set(graph.get_nodes())

    # --- Step 3: Operation counter ---
    # Increment this each time you examine a node while scanning for the min.
    op_count = 0

    # --- Step 4: Main loop ---
    # Keep going as long as there are unvisited nodes.
    while unvisited:

        # Find the unvisited node with the smallest distance.
        # Scan every node in unvisited, compare dist[node], track the minimum.
        # Increment op_count once per node examined during this scan.
        #
        # Hint: start with current_node = None, current_dist = float('inf'),
        # then loop through unvisited updating both when you find something smaller.
        current_node = None
        current_dist = float('inf')
        for node in unvisited:
            op_count += 1
            # TODO: if dist[node] < current_dist, update current_node and current_dist
            pass

        # If the best unvisited distance is still infinity, all remaining nodes
        # are unreachable — stop early.
        if current_dist == float('inf'):
            break

        # Remove current_node from unvisited.
        # TODO: unvisited.remove(current_node)
        pass

        # Relax neighbors.
        # For each (neighbor, weight) from graph.get_neighbors(current_node):
        #   new_cost = dist[current_node] + weight
        #   if new_cost < dist[neighbor], update dist and prev.
        for neighbor, weight in graph.get_neighbors(current_node):
            new_cost = current_dist + weight
            if new_cost < dist[neighbor]:
                # TODO: update dist[neighbor] and prev[neighbor]
                pass

    return dist, prev, op_count


def shortest_path_naive(graph, start, end):
    """
    Return the shortest path from start to end as a list of nodes,
    or None if no path exists. Uses dijkstra_naive internally.

    Args:
        graph (WeightedGraph): the graph to search
        start: the starting node
        end: the destination node

    Returns:
        list of nodes [start, ..., end], or None if unreachable

    Hint: call dijkstra_naive, check dist[end], then trace backwards
    through prev from end to start, then reverse.
    """
    dist, prev, _ = dijkstra_naive(graph, start)

    if dist[end] == float('inf'):
        return None

    path = []
    current = end
    while current is not None:
        # TODO: append current to path, then move current to prev[current]
        pass

    # TODO: reverse and return path
    pass