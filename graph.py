class WeightedGraph:
    """
    A weighted graph that supports both undirected and directed edges.

    Internally stores adjacency as a dict of dicts:
        { node: { neighbor: weight, ... }, ... }

    Example:
        g = WeightedGraph()
        g.add_edge("A", "B", 4)
        g.get_neighbors("A")  # -> [("B", 4)]
    """

    def __init__(self):
        # This dict is your adjacency structure.
        # Keys are nodes; values are dicts mapping neighbor -> weight.
        # Example after adding edge A-B with weight 4 (undirected):
        #   { "A": {"B": 4}, "B": {"A": 4} }
        self._adj = {}

    def add_node(self, node):
        """
        Add a node to the graph if it doesn't already exist.

        Args:
            node: any hashable value (string, int, etc.)
        """
        # Only add the node if it isn't already a key in self._adj.
        # Hint: a new node starts with an empty neighbor dict: {}
        if node not in self._adj:
            self._adj[node] = {}


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
        # Step 1: make sure both u and v exist as nodes (call add_node).
        # Step 2: record the edge u -> v with the given weight.
        #         self._adj[u][v] = weight
        # Step 3: if not directed, also record v -> u with the same weight.
        self.add_node(u)
        self.add_node(v)
        self._adj[u][v] = weight
        if not directed:
            self._adj[v][u] = weight

    def get_neighbors(self, node):
        """
        Return all neighbors of a node as a list of (neighbor, weight) tuples.

        Args:
            node: the node to look up

        Returns:
            list of (neighbor, weight) tuples, or empty list if node has none

        Hint: dict.items() returns (key, value) pairs — use list() to convert.
        """
        # Look up node in self._adj and convert its inner dict to a list of
        # (neighbor, weight) tuples. Return [] if the node doesn't exist.
        if node in self._adj:
            return list(self._adj[node].items())
        if node not in self._adj:
            return []

    def get_nodes(self):
        """
        Return a list of all nodes in the graph.

        Returns:
            list of all nodes

        Hint: the keys of self._adj are exactly the nodes.
        """
        return list(self._adj.keys())
