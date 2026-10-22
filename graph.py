class WeightedGraph:
    """
    A weighted graph that supports both undirected and directed edges.

    Internally stores adjacency as a dict of dicts:
        { node: { neighbor: weight, ... }, ... }
    """

    def __init__(self):
        pass

    def add_node(self, node):
        """
        Add a node to the graph if it doesn't already exist.

        Args:
            node: any hashable value (string, int, etc.)
        """
        pass

    def add_edge(self, u, v, weight, directed=False):
        """
        Add a weighted edge between nodes u and v.
        Both nodes are added automatically if they don't exist yet.

        Args:
            u: starting node
            v: ending node
            weight (int or float): the cost/distance of this edge
            directed (bool): if False (default), add edges in both directions.
                             if True, only add the edge from u to v.
        """
        pass

    def get_neighbors(self, node):
        """
        Return all neighbors of a node as a list of (neighbor, weight) tuples.

        Args:
            node: the node to look up

        Returns:
            list of (neighbor, weight) tuples, or empty list if node has none
        """
        pass

    def get_nodes(self):
        """
        Return a list of all nodes in the graph.

        Returns:
            list of all nodes
        """
        pass