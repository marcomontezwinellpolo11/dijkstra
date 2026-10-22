# ──────────────────────────────────────────────────────────────────────────────
# dijkstra_heap.py
#
# Complete dijkstra_naive.py first, then run run_all_tests.py.
# Use the scan-count activity to investigate how its work grows.
# When you are ready for this version, run the same file and enter 'heap'.
#
# A min-heap supports adding an item and removing the smallest item.
# You will use it to select the next node without scanning the whole
# unvisited set each time. Investigate how this changes the work required
# in the comparison activity after your heap implementation is correct.
#
# ── Python's heapq module ─────────────────────────────────────────────────────
#
# Python provides a min-heap via the heapq module:
#
#   import heapq
#
#   heap = []
#   heapq.heappush(heap, (3, "C"))   # push (priority, item)
#   heapq.heappush(heap, (1, "A"))
#   heapq.heappush(heap, (2, "B"))
#
#   heapq.heappop(heap)   # -> (1, "A")  — always the smallest first
#   heapq.heappop(heap)   # -> (2, "B")
#
# For Dijkstra's, push (distance, node) tuples so the heap always gives you
# the unvisited node with the smallest known distance.
#
# One subtlety: you may push the same node multiple times with different
# distances as you discover shorter paths. That's fine — just skip a node
# if you've already finalized it (use a visited set, same as naive).
# ──────────────────────────────────────────────────────────────────────────────

import heapq


def dijkstra_heap(graph, start):
    """
    Run Dijkstra's algorithm using a min-heap priority queue.

    Args:
        graph (WeightedGraph): the graph to search
        start: the node to start from

    Returns:
        (dist, prev, op_count) where:
            dist      — dict mapping each node to its shortest distance from start.
                        Unreachable nodes map to float('inf').
            prev      — dict mapping each node to the previous node on the
                        shortest path. The start node maps to None.
            op_count  — int, number of times a node was popped from the heap.
                        Compare this to the naive scan count in the perf tests.
    """
    # --- Step 1: Initialize distances and prev (same as naive) ---
    dist = {node: float('inf') for node in graph.get_nodes()}
    dist[start] = 0
    prev = {node: None for node in graph.get_nodes()}

    # --- Step 2: Set up the heap ---
    # Push the start node with cost 0. Format: (cost, node)
    heap = [(0, start)]

    # --- Step 3: Visited set and op counter ---
    visited = set()
    op_count = 0

    # --- Step 4: Main loop ---
    while heap:
        # Pop the (cost, node) tuple with the smallest cost.
        # Hint: heapq.heappop(heap) returns the smallest item.
        current_cost, current_node = heapq.heappop(heap)
        op_count += 1

        # If already visited, skip — we've already found the best path here.
        if current_node in visited:
            continue

        # TODO: mark current_node as visited
        pass

        # Relax neighbors — same logic as naive.
        for neighbor, weight in graph.get_neighbors(current_node):
            new_cost = current_cost + weight
            if new_cost < dist[neighbor]:
                # TODO: update dist[neighbor] and prev[neighbor]
                # TODO: push (new_cost, neighbor) onto the heap
                pass

    return dist, prev, op_count


def shortest_path(graph, start, end):
    """
    Return the shortest path from start to end as a list of nodes,
    or None if no path exists. Uses dijkstra_heap internally.

    Args:
        graph (WeightedGraph): the graph to search
        start: the starting node
        end: the destination node

    Returns:
        list of nodes [start, ..., end], or None if unreachable

    Hint: same pattern as shortest_path_naive — call dijkstra_heap,
    check dist[end], trace backwards through prev, reverse.
    """
    dist, prev, _ = dijkstra_heap(graph, start)

    if dist[end] == float('inf'):
        return None

    path = []
    current = end
    while current is not None:
        # TODO: append current to path, move current to prev[current]
        pass

    # TODO: reverse and return path
    pass