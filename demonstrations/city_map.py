"""Two fictional road networks used by this lab; no student/solution imports.

CITY_EDGES preserves the original correctness map.
DEMO_EDGES is a different map chosen so fewest hops and lowest cost disagree.
"""
CITY_EDGES = [
    ('Ashford', 'Brindleton', 4), ('Ashford', 'Crestholm', 9),
    ('Brindleton', 'Crestholm', 6), ('Brindleton', 'Dover', 8),
    ('Brindleton', 'Elmwick', 3), ('Crestholm', 'Elmwick', 5),
    ('Crestholm', 'Fairhaven', 11), ('Dover', 'Gorton', 7),
    ('Fairhaven', 'Hartwell', 4), ('Hartwell', 'Ivywood', 6),
]
ALL_CITIES = ['Ashford', 'Brindleton', 'Crestholm', 'Dover', 'Elmwick',
              'Fairhaven', 'Gorton', 'Hartwell', 'Ivywood', 'Jasperton', 'Keldmere']
CONNECTED_CITIES = ALL_CITIES[:-2]
ASHFORD_DISTANCES = dict(zip(ALL_CITIES, [0, 4, 9, 12, 7, 20, 19, 24, 30, float('inf'), float('inf')]))
ASHFORD_TO_HARTWELL_PATH = ['Ashford', 'Crestholm', 'Fairhaven', 'Hartwell']

DEMO_EDGES = [
    ('Ashford', 'Brindleton', 1), ('Brindleton', 'Ivywood', 50),
    ('Ashford', 'Crestholm', 4), ('Crestholm', 'Dover', 4),
    ('Dover', 'Elmwick', 4), ('Elmwick', 'Ivywood', 4),
    ('Ashford', 'Fairhaven', 10), ('Fairhaven', 'Gorton', 3),
]
DEMO_POSITIONS = {
    'Ashford': (0, 2), 'Brindleton': (2, 3), 'Ivywood': (6, 3),
    'Crestholm': (0, 0), 'Dover': (2, 0), 'Elmwick': (4, 0),
    'Fairhaven': (2, 1.5), 'Gorton': (4, 1.5),
}


def adjacency(edges, nodes=()):
    result = {node: {} for node in nodes}
    for u, v, weight in edges:
        result.setdefault(u, {})[v] = weight
        result.setdefault(v, {})[u] = weight
    return result


def build_city_map(graph_class):
    """The caller supplies the student's graph class explicitly."""
    graph = graph_class()
    for city in ALL_CITIES:
        graph.add_node(city)
    for u, v, weight in CITY_EDGES:
        graph.add_edge(u, v, weight)
    return graph
