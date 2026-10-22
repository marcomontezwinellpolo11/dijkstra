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
    pass


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
    """
    pass