"""Dijkstra correctness checks, with isolated methods and separate integration.

Run: python test_correctness.py [--stage graph|naive|heap|all]
Or use run_all_tests.py for pauses between sections. Standard library only.

Student files: graph.py, dijkstra_naive.py, dijkstra_heap.py.
Graph representation: _adj is a dict mapping nodes to neighbor/weight dicts.
No solution modules, city_map, plotting packages, or performance tests are used.
"""

import argparse
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
import importlib
import math
import os
import sys
import time
import traceback
from types import MethodType
from unittest.mock import patch


INF = float('inf')
METHODS = ('add_node', 'add_edge', 'get_neighbors', 'get_nodes')


def require(condition, message):
    # Keep checks active even with python -O.
    if not condition:
        raise AssertionError(message)


def equal(actual, expected, label):
    require(actual == expected, f'{label}: expected {expected!r}, got {actual!r}')


def copy_adj(adj):
    return {node: dict(neighbors) for node, neighbors in adj.items()}


class TestTimeout(BaseException):
    # Do not let a student's ordinary `except Exception` swallow the timeout.
    pass


def run_with_timeout(function, seconds):
    """Interrupt ordinary Python loops; not a process-level sandbox.

    As in the linked-list reference, tracing cannot interrupt blocking native
    calls, input(), or sleep(). Restore a debugger's trace when finished.
    """
    deadline = time.monotonic() + seconds
    previous = sys.gettrace()

    def check_time(frame, event, arg):
        if time.monotonic() >= deadline:
            raise TestTimeout(f'Stopped after {seconds:g}s. Possible infinite loop.')
        return check_time

    try:
        sys.settrace(check_time)
        return function()
    finally:
        sys.settrace(previous)


def verify_timeout_support():
    """Finite probes: never test an unknown runtime with an endless loop.

    Verify line callbacks can interrupt code and that our deadline guard fires.
    A runtime that ignores tracing is reported before any student import.
    """
    def finite_probe():
        total = 0
        for number in range(10):
            total += number
        return total

    if not callable(getattr(sys, 'settrace', None)) or not callable(getattr(sys, 'gettrace', None)):
        raise RuntimeError('This Python runtime does not provide sys.settrace/gettrace.')
    previous = sys.gettrace()

    def probe_trace(frame, event, arg):
        if frame.f_code is finite_probe.__code__ and event == 'line':
            raise TestTimeout('Line tracing works')
        return probe_trace

    interrupted = False
    try:
        sys.settrace(probe_trace)
        try:
            finite_probe()
        except TestTimeout:
            interrupted = True
    finally:
        sys.settrace(previous)
    if not interrupted:
        raise RuntimeError('This Python runtime did not deliver interruptible line-trace events.')
    try:
        run_with_timeout(finite_probe, 0)
    except TestTimeout:
        return
    raise RuntimeError('The timeout deadline check did not interrupt the finite probe.')


def timeout_hint(group):
    if group.startswith('shortest_path'):
        return ('Check that each path-tracing iteration moves to prev[current], '
                'and that the chain eventually reaches None.')
    if group == 'dijkstra_naive':
        return ('Check that each main-loop iteration removes the selected node '
                'from unvisited, and that you stop when the remaining nodes are unreachable.')
    if group == 'dijkstra_heap':
        return ('Check that each iteration pops an entry, that finished/stale entries '
                'are handled, and that equal-cost routes are not requeued forever.')
    if group.endswith(' setup'):
        return ('Check for a loop running at the top level of this file. '
                'Put demonstration code under if __name__ == "__main__":.')
    if group in METHODS or group == '__init__':
        return 'Check that every loop in this graph method advances or reaches a stopping condition.'
    return 'Check loops in the graph, Dijkstra function, and predecessor/path tracing.'


class CapturedOutput:
    """Limit debug output so a printing loop cannot fill memory."""
    def __init__(self):
        self.text = ''

    def write(self, text):
        self.text += text[:max(0, 3000 - len(self.text))]
        return len(text)

    def flush(self):
        pass


@dataclass
class Result:
    section: str
    group: str
    name: str
    status: str
    detail: str = ''


def run_case(section, group, name, function, seconds=2):
    output = CapturedOutput()

    def unexpected_input(*args, **kwargs):
        raise RuntimeError(
            'input() was called inside a correctness check. Tested functions '
            'should use their arguments and return results without prompting. '
            'Move interactive demonstrations under if __name__ == "__main__":.')

    try:
        with redirect_stdout(output), redirect_stderr(output), patch('builtins.input', unexpected_input):
            run_with_timeout(function, seconds)
        return Result(section, group, name, 'PASS')
    except (Exception, TestTimeout, SystemExit) as exc:
        detail = f'{type(exc).__name__}: {exc}'
        if isinstance(exc, TestTimeout):
            detail += '\nHint: ' + timeout_hint(group)
        elif isinstance(exc, RecursionError):
            detail += '\nHint: check the recursion base case and whether a function keeps calling itself.'
        elif isinstance(exc, SystemExit):
            detail += '\nHint: return a result from the tested function instead of calling exit()/sys.exit().'
        # Prefer the student source location over the assertion in this file.
        frames = traceback.extract_tb(exc.__traceback__)
        student_names = {'graph.py', 'dijkstra_naive.py', 'dijkstra_heap.py'}
        for frame in reversed(frames):
            if os.path.basename(frame.filename) in student_names:
                detail += f' [{os.path.basename(frame.filename)}:{frame.lineno}]'
                break
        if output.text.strip():
            detail += '\nCaptured output (first 3000 characters):\n' + output.text.strip()
        return Result(section, group, name, 'FAIL', detail)


class TrustedGraph:
    """Small test fixture; does not import or call the student's graph."""
    def __init__(self, adj):
        self._adj = copy_adj(adj)

    def add_node(self, node):
        self._adj.setdefault(node, {})

    def add_edge(self, u, v, weight, directed=False):
        self.add_node(u)
        self.add_node(v)
        self._adj[u][v] = weight
        if not directed:
            self._adj[v][u] = weight

    def get_nodes(self):
        return list(self._adj)

    def get_neighbors(self, node):
        return list(self._adj.get(node, {}).items())


def isolated_graph(cls, target, adj=None):
    """Bypass student __init__; replace every public sibling method.

    The _adj contract is explicit in the supplied starters. Mutations are
    inspected directly, so a broken getter cannot hide a correct mutator.
    """
    graph = object.__new__(cls)
    if adj is not None:
        graph._adj = copy_adj(adj)
    for name in METHODS:
        if name != target:
            setattr(graph, name, MethodType(getattr(TrustedGraph, name), graph))
    return graph


def check_adjacency(graph, expected):
    actual = getattr(graph, '_adj', None)
    require(isinstance(actual, dict), '_adj must be a dictionary of dictionaries')
    require(all(isinstance(v, dict) for v in actual.values()),
            'Each value in _adj must be a neighbor -> weight dictionary')
    equal(actual, expected, 'stored adjacency')


def graph_cases(cls):
    cases = []

    def constructor():
        graph = isolated_graph(cls, '__init__')
        cls.__init__(graph)
        check_adjacency(graph, {})

    def independent_storage():
        a, b = (isolated_graph(cls, '__init__') for _ in range(2))
        cls.__init__(a)
        cls.__init__(b)
        check_adjacency(a, {})
        check_adjacency(b, {})
        a._adj['probe'] = {}
        check_adjacency(b, {})

    cases.extend([('__init__', 'new graph starts empty', constructor),
                  ('__init__', 'each graph owns its adjacency', independent_storage)])

    def mutation(target, name, before, args, expected, kwargs=None):
        def check():
            graph = isolated_graph(cls, target, before)
            getattr(graph, target)(*args, **(kwargs or {}))
            check_adjacency(graph, expected)
        cases.append((target, name, check))

    mutation('add_node', 'add to empty graph', {}, ('A',), {'A': {}})
    mutation('add_node', 'preserve other nodes', {'A': {}}, ('B',), {'A': {}, 'B': {}})
    mutation('add_node', 'adding existing node preserves its edges',
             {'A': {'B': 4}, 'B': {}}, ('A',), {'A': {'B': 4}, 'B': {}})
    mutation('add_node', 'hashable labels: tuple, integer, None',
             {0: {}, None: {}}, ((2, 3),), {0: {}, None: {}, (2, 3): {}})
    mutation('add_edge', 'default edge goes both ways and creates endpoints',
             {}, ('A', 'B', 5), {'A': {'B': 5}, 'B': {'A': 5}})
    mutation('add_edge', 'explicit directed edge creates endpoints, only goes forward',
             {}, ('A', 'B', 3), {'A': {'B': 3}, 'B': {}}, {'directed': True})
    mutation('add_edge', 'one existing endpoint keeps its other edges',
             {'A': {'C': 2}, 'C': {'A': 2}}, ('A', 'B', 7),
             {'A': {'C': 2, 'B': 7}, 'C': {'A': 2}, 'B': {'A': 7}})
    mutation('add_edge', 'directed edge preserves unrelated and reverse edges',
             {'A': {'C': 2}, 'B': {'A': 8}, 'C': {}}, ('A', 'B', 3),
             {'A': {'C': 2, 'B': 3}, 'B': {'A': 8}, 'C': {}}, {'directed': True})
    mutation('add_edge', 'zero weight is a real edge', {}, ('A', 'B', 0),
             {'A': {'B': 0}, 'B': {'A': 0}})
    mutation('add_edge', 'fractional weight is preserved', {}, ('A', 'B', 1.25),
             {'A': {'B': 1.25}, 'B': {'A': 1.25}}, {'directed': False})

    for name, adj, node, expected in [
        ('no neighbors in empty graph', {}, 'missing', []),
        ('isolated node', {'A': {}}, 'A', []),
        ('unknown node', {'A': {}}, 'missing', []),
        ('all neighbor/weight pairs exactly once',
         {'A': {'B': 4, 'C': 0, 'D': 1.25}, 'B': {}, 'C': {}, 'D': {}},
         'A', [('B', 4), ('C', 0), ('D', 1.25)]),
    ]:
        def check(adj=adj, node=node, expected=expected):
            graph = isolated_graph(cls, 'get_neighbors', adj)
            actual = graph.get_neighbors(node)
            require(isinstance(actual, list), f'get_neighbors must return a list; got {actual!r}')
            require(all(isinstance(pair, tuple) and len(pair) == 2 for pair in actual),
                    f'Neighbors must be (neighbor, weight) tuples; got {actual!r}')
            require(len(actual) == len(expected) and set(actual) == set(expected),
                    f'Expected pairs {expected!r} in any order; got {actual!r}')
            check_adjacency(graph, adj)
        cases.append(('get_neighbors', name, check))

    for name, adj in [('empty graph', {}), ('isolated node', {'A': {}}),
                      ('all nodes, including isolated and mixed hashable labels',
                       {'A': {0: 2}, 0: {}, (2, 3): {}, None: {}})]:
        def check(adj=adj):
            graph = isolated_graph(cls, 'get_nodes', adj)
            actual = graph.get_nodes()
            require(isinstance(actual, list), f'get_nodes must return a list; got {actual!r}')
            require(len(actual) == len(adj) and set(actual) == set(adj),
                    f'Expected nodes {list(adj)!r}, once each in any order; got {actual!r}')
            check_adjacency(graph, adj)
        cases.append(('get_nodes', name, check))
    return cases


# Fixed, hand-checkable expected distances. No student or solution algorithm
# calculates the expected answers; neither implementation is the other's oracle.
SCENARIOS = [
    ('single node', {'A': {}}, 'A', {'A': 0}),
    ('cheaper route takes more hops',
     {'A': {'B': 1, 'C': 10}, 'B': {'C': 2}, 'C': {}},
     'A', {'A': 0, 'B': 1, 'C': 3}),
    ('directed edges cannot be followed backwards',
     {'A': {'B': 2}, 'B': {'C': 3}, 'C': {}},
     'B', {'A': INF, 'B': 0, 'C': 3}),
    ('unreachable component and isolated node',
     {'A': {'B': 2}, 'B': {'A': 2}, 'X': {'Y': 1}, 'Y': {'X': 1}, 'Z': {}},
     'A', {'A': 0, 'B': 2, 'X': INF, 'Y': INF, 'Z': INF}),
    ('zero-cost cycle terminates with valid predecessors',
     {'A': {'B': 0, 'C': 5}, 'B': {'A': 0, 'C': 2}, 'C': {'B': 2}},
     'A', {'A': 0, 'B': 0, 'C': 2}),
    ('improve an earlier estimate; stale heap entries must not spoil results',
     {'A': {'B': 9, 'C': 1}, 'B': {'D': 1}, 'C': {'B': 1, 'D': 8}, 'D': {}},
     'A', {'A': 0, 'B': 2, 'C': 1, 'D': 3}),
    ('equal-cost routes: either valid predecessor is accepted',
     {'A': {'B': 1, 'C': 1}, 'B': {'D': 1}, 'C': {'D': 1}, 'D': {}},
     'A', {'A': 0, 'B': 1, 'C': 1, 'D': 2}),
    ('fractional weights',
     {'A': {'B': 0.1, 'C': 0.9}, 'B': {'C': 0.2}, 'C': {}},
     'A', {'A': 0, 'B': 0.1, 'C': 0.3}),
    ('integer zero is a valid start node',
     {0: {1: 2, 2: 8}, 1: {2: 3}, 2: {}},
     0, {0: 0, 1: 2, 2: 5}),
]


def close(actual, expected, label):
    require(type(actual) in (int, float), f'{label}: expected a number, got {actual!r}')
    require(math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9),
            f'{label}: expected {expected!r}, got {actual!r}')


def check_solver_result(result, adj, start, expected):
    require(isinstance(result, tuple) and len(result) == 3,
            f'Return (dist, prev, op_count) as a tuple; got {result!r}')
    dist, prev, ops = result
    require(isinstance(dist, dict), f'dist must be a dict; got {dist!r}')
    require(isinstance(prev, dict), f'prev must be a dict; got {prev!r}')
    require(type(ops) is int and ops >= 0,
            f'op_count must be a nonnegative integer; got {ops!r}')
    equal(set(dist), set(expected), 'nodes in dist (include unreachable nodes)')
    for node, wanted in expected.items():
        close(dist[node], wanted, f'dist[{node!r}]')
    require(start in prev and prev[start] is None, 'prev[start] must be None')
    require(set(prev) <= set(adj), 'prev contains a node outside the graph')
    for node, distance in expected.items():
        # The starter explicitly promises prev[start] = None, but does not
        # require entries for unreachable nodes. Missing or None is fine.
        if distance == INF:
            require(prev.get(node) is None,
                    f'Unreachable node {node!r} must not have a predecessor')
            continue
        seen, current = set(), node
        while current != start:
            require(current not in seen, f'Cycle in prev when tracing from {node!r}')
            seen.add(current)
            require(current in prev, f'prev is missing reachable node {current!r}')
            parent = prev[current]
            require(parent in adj and current in adj[parent],
                    f'prev[{current!r}] = {parent!r} is not an incoming graph edge')
            close(dist[parent] + adj[parent][current], dist[current],
                  f'Cost through prev[{current!r}] (update prev when improving dist)')
            current = parent


def algorithm_cases(module, kind):
    name = 'dijkstra_' + kind
    cases = []
    for title, adj, start, expected in SCENARIOS:
        def check(adj=adj, start=start, expected=expected):
            graph = TrustedGraph(adj)
            result = getattr(module, name)(graph, start)
            check_solver_result(result, adj, start, expected)
            check_adjacency(graph, adj)
        cases.append((name, title, check))
    return cases


def path_cases(module, kind):
    solver_name = 'dijkstra_' + kind
    path_name = 'shortest_path_naive' if kind == 'naive' else 'shortest_path'
    cases = []
    data = [
        ('reverse a multi-edge predecessor chain',
         {'S': 0, 'A': 2, 'B': 5, 'T': 9},
         {'S': None, 'A': 'S', 'B': 'A', 'T': 'B'}, 'S', 'T', ['S', 'A', 'B', 'T']),
        ('direct neighbor', {'A': 0, 'B': 4}, {'A': None, 'B': 'A'}, 'A', 'B', ['A', 'B']),
        ('start equals end', {'A': 0}, {'A': None}, 'A', 'A', ['A']),
        ('unreachable destination returns None',
         {'A': 0, 'Z': INF}, {'A': None, 'Z': None}, 'A', 'Z', None),
        ('zero is a valid start, not the end of a chain',
         {0: 0, 1: 2, 2: 5}, {0: None, 1: 0, 2: 1}, 0, 2, [0, 1, 2]),
        ('zero is a valid intermediate node',
         {2: 0, 0: 1, 1: 2}, {2: None, 0: 2, 1: 0}, 2, 1, [2, 0, 1]),
    ]
    for title, dist, prev, start, end, expected in data:
        def check(dist=dist, prev=prev, start=start, end=end, expected=expected):
            adj = {node: {} for node in dist}
            for node, parent in prev.items():
                if parent is not None:
                    adj[parent][node] = dist[node] - dist[parent]
            graph = TrustedGraph(adj)

            def known_result(received_graph, received_start):
                require(received_graph is graph, f'{path_name} must pass its graph to {solver_name}')
                equal(received_start, start, f'start passed to {solver_name}')
                return dict(dist), dict(prev), 0

            # Patch only inside this case; always restore, even after a timeout.
            # create=True allows independent path tests if the solver is absent.
            with patch.object(module, solver_name, side_effect=known_result, create=True) as mock:
                actual = getattr(module, path_name)(graph, start, end)
                if expected is None:
                    require(actual is None, f'Unreachable path: expected None, got {actual!r}')
                else:
                    require(isinstance(actual, list), f'Path must be a list; got {actual!r}')
                    equal(actual, expected, 'path in start-to-end order')
                if start != end:
                    require(mock.called, f'{path_name} should use {solver_name} internally')
        cases.append((path_name, title, check))
    return cases


def graph_integration_cases(cls):
    def sequence():
        graph = cls()
        graph.add_node('isolated')
        graph.add_edge('A', 'B', 4)
        graph.add_edge('B', 'C', 2, directed=True)
        graph.add_node('B')
        expected = {'isolated': {}, 'A': {'B': 4}, 'B': {'A': 4, 'C': 2}, 'C': {}}
        check_adjacency(graph, expected)
        nodes = graph.get_nodes()
        require(isinstance(nodes, list) and len(nodes) == len(expected)
                and set(nodes) == set(expected), f'Unexpected nodes: {nodes!r}')
        for node, neighbors in expected.items():
            actual = graph.get_neighbors(node)
            require(isinstance(actual, list) and len(actual) == len(neighbors)
                    and set(actual) == set(neighbors.items()),
                    f'After mixed additions, neighbors of {node!r}: expected {neighbors!r}, got {actual!r}')

    def separate():
        a, b = cls(), cls()
        a.add_edge('A', 'B', 2)
        equal(b.get_nodes(), [], 'second graph after changing first graph')
        equal(b.get_neighbors('A'), [], 'second graph has no edges from first')

    return [('graph', 'constructor, additions, and queries work together', sequence),
            ('graph', 'mutations stay within their own graph', separate)]


# Same roads and expected distances as city_map.py, copied as test data so
# integration really uses the student graph, never graph_SOLUTION.
CITY_EDGES = [
    ('Ashford', 'Brindleton', 4), ('Ashford', 'Crestholm', 9),
    ('Brindleton', 'Crestholm', 6), ('Brindleton', 'Dover', 8),
    ('Brindleton', 'Elmwick', 3), ('Crestholm', 'Elmwick', 5),
    ('Crestholm', 'Fairhaven', 11), ('Dover', 'Gorton', 7),
    ('Fairhaven', 'Hartwell', 4), ('Hartwell', 'Ivywood', 6),
]
CITY_DIST = {'Ashford': 0, 'Brindleton': 4, 'Crestholm': 9, 'Dover': 12,
             'Elmwick': 7, 'Fairhaven': 20, 'Gorton': 19, 'Hartwell': 24,
             'Ivywood': 30, 'Jasperton': INF, 'Keldmere': INF}


def city_adjacency():
    adj = {node: {} for node in CITY_DIST}
    for u, v, weight in CITY_EDGES:
        adj[u][v] = adj[v][u] = weight
    return adj


def build_student_graph(cls, adj):
    graph = cls()
    for node in adj:
        graph.add_node(node)
    for node, neighbors in adj.items():
        for neighbor, weight in neighbors.items():
            graph.add_edge(node, neighbor, weight, directed=True)
    return graph


def check_path(path, adj, start, end, distance):
    if distance == INF:
        require(path is None, f'Path to unreachable {end!r}: expected None, got {path!r}')
        return
    require(isinstance(path, list) and path, f'Expected a nonempty path list, got {path!r}')
    equal(path[0], start, 'first node in path')
    equal(path[-1], end, 'last node in path')
    require(len(path) == len(set(path)), f'Path should not repeat nodes: {path!r}')
    cost = 0
    for u, v in zip(path, path[1:]):
        require(u in adj and v in adj[u], f'Path uses missing/directed-backward edge {u!r} -> {v!r}')
        cost += adj[u][v]
    close(cost, distance, f'cost of path {path!r}')


def algorithm_integration_cases(cls, module, kind):
    solver_name = 'dijkstra_' + kind
    path_name = 'shortest_path_naive' if kind == 'naive' else 'shortest_path'
    cases = []
    scenarios = SCENARIOS + [('city map from Ashford', city_adjacency(), 'Ashford', CITY_DIST)]
    for title, adj, start, expected in scenarios:
        def check(adj=adj, start=start, expected=expected):
            graph = build_student_graph(cls, adj)
            check_solver_result(getattr(module, solver_name)(graph, start), adj, start, expected)
            for end, distance in expected.items():
                path = getattr(module, path_name)(graph, start, end)
                check_path(path, adj, start, end, distance)
            check_adjacency(graph, adj)
        cases.append((kind, title, check))

    def repeated_calls():
        adj = {'A': {'B': 2}, 'B': {'A': 2, 'C': 3}, 'C': {'B': 3}}
        graph = build_student_graph(cls, adj)
        for start, expected in [('A', {'A': 0, 'B': 2, 'C': 5}),
                                ('C', {'A': 5, 'B': 3, 'C': 0}),
                                ('A', {'A': 0, 'B': 2, 'C': 5})]:
            check_solver_result(getattr(module, solver_name)(graph, start), adj, start, expected)
        check_adjacency(graph, adj)
    cases.append((kind, 'repeated searches reset state and preserve the graph', repeated_calls))
    return cases


def color(text, code, enabled):
    return f'\033[{code}m{text}\033[0m' if enabled else text


def show_results(results, use_color=False):
    for group in dict.fromkeys(row.group for row in results):
        rows = [row for row in results if row.group == group]
        passed = sum(row.status == 'PASS' for row in rows)
        if all(row.status == 'SKIP' for row in rows):
            label, code = 'SKIP', '33'
        else:
            label, code = ('PASS', '32') if passed == len(rows) else ('FAIL', '31')
        print(color(f'  [{label}] {group}: {passed}/{len(rows)} checks passed', code, use_color))
        for row in rows:
            if row.status != 'PASS':
                print(f'      {row.name}')
                for line in row.detail.splitlines():
                    print('        ' + line)


def run_correctness_tests(stage='all', *, pause=False, seconds=2, use_color=False,
                          before_section=None, graph_verified=False):
    """Return structured Result rows. Run every selected isolated group.

    --stage naive selects graph + naive; --stage heap selects graph + heap.
    graph_verified is used only by the guided runner after graph checks passed
    in the same run. before_section is called BEFORE importing/executing a group.
    Only integrations whose dependencies passed are run. Missing/syntax-broken
    modules fail their own setup without preventing other modules' unit tests.
    """
    require(stage in ('all', 'graph', 'naive', 'heap'), 'Unknown stage')
    require(math.isfinite(seconds) and seconds > 0, 'Timeout must be positive and finite')
    try:
        verify_timeout_support()
    except Exception as exc:
        row = Result('setup', 'timeout support', 'Python loop-timeout capability', 'FAIL',
                     f'{type(exc).__name__}: {exc}\n'
                     'Student code was not run because loop protection could not be verified. '
                     'Try ordinary Run rather than Debug, or run these files in local Python.')
        show_results([row], use_color)
        return [row]
    print('Python loop-timeout check: ready.')
    selected = ['graph'] + (['naive', 'heap'] if stage == 'all' else
                            [] if stage == 'graph' else [stage])
    modules, results, units_ok = {}, [], {}
    if graph_verified:
        require('graph' in sys.modules, 'Graph reuse requires an earlier passing cycle in this process')
        modules['graph'] = sys.modules['graph']
        units_ok['graph'] = True
        selected.remove('graph')
        print('Graph checks already passed in this run.')
    first = True

    def begin_section(title):
        nonlocal first, pause
        if before_section is not None:
            before_section(title)
        elif pause and not first:
            try:
                input('\nPress Enter to run ' + title.lower() + '...')
            except (EOFError, OSError):
                pause = False
        first = False
        print(color('\n' + title, '36', use_color), flush=True)

    def display(title, rows):
        show_results(rows, use_color)
        results.extend(rows)

    for component in selected:
        begin_section(f'ISOLATED: {component}')
        print(f'Checking isolated {component} functions (up to {seconds:g}s per check)...', flush=True)
        module_name = 'graph' if component == 'graph' else 'dijkstra_' + component

        def load(module_name=module_name, component=component):
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError as exc:
                if exc.name == module_name:
                    raise ImportError(
                        f'Create {module_name}.py beside these tests by copying your '
                        'chosen minimal/moderate starter. Solution files are never loaded automatically.') from exc
                raise
            modules[component] = module

        setup = run_case('isolated', component + ' setup', 'load ' + module_name + '.py', load, seconds)
        if setup.status == 'FAIL':
            units_ok[component] = False
            display(f'ISOLATED: {component}', [setup])
            continue
        module = modules[component]
        # Defer attribute lookup to individual cases, so one missing method
        # does not prevent testing the remaining functions in that module.
        if component == 'graph':
            if not isinstance(getattr(module, 'WeightedGraph', None), type):
                rows = [Result('isolated', 'graph setup', 'WeightedGraph class', 'FAIL',
                               'graph.py must define a class named WeightedGraph.')]
            else:
                rows = [run_case('isolated', group, title, check, seconds)
                        for group, title, check in graph_cases(module.WeightedGraph)]
        else:
            rows = [run_case('isolated', group, title, check, seconds)
                    for group, title, check in algorithm_cases(module, component) + path_cases(module, component)]
        units_ok[component] = all(row.status == 'PASS' for row in rows)
        display(f'ISOLATED: {component}', rows)

    graph_ok = graph_verified
    for component in selected:
        dependencies = ['graph'] if component == 'graph' else ['graph', component]
        failed = [name for name in dependencies if not units_ok.get(name, False)]
        if component != 'graph' and units_ok.get('graph') and not graph_ok:
            failed.append('graph integration')
        if failed:
            print(color(f'\nINTEGRATION: {component}', '36', use_color))
            display(f'INTEGRATION: {component}', [Result(
                'integration', component, 'waiting for prerequisites', 'SKIP',
                'Fix these groups first: ' + ', '.join(failed) + '. Isolated tests above still ran.')])
            continue
        begin_section(f'INTEGRATION: {component}')
        cls = modules['graph'].WeightedGraph
        cases = (graph_integration_cases(cls) if component == 'graph' else
                 algorithm_integration_cases(cls, modules[component], component))
        rows = [run_case('integration', group, title, check, seconds)
                for group, title, check in cases]
        display(f'INTEGRATION: {component}', rows)
        if component == 'graph':
            graph_ok = all(row.status == 'PASS' for row in rows)

    passed = sum(row.status == 'PASS' for row in results)
    failed = sum(row.status == 'FAIL' for row in results)
    skipped = sum(row.status == 'SKIP' for row in results)
    print(f'\nSummary: {passed} passed, {failed} failed, {skipped} integration sections skipped.')
    ok = bool(results) and all(row.status == 'PASS' for row in results)
    if ok:
        print(color('All selected correctness checks passed.', '32', use_color))
        if stage == 'graph':
            print('Next: work on dijkstra_naive.py, then run run_all_tests.py.')
        elif stage == 'naive':
            print('Naive correctness passed. The guided runner offers scan-count exploration next.')
        elif stage == 'heap':
            print('Heap correctness passed. The guided runner offers comparison and visualization next.')
        else:
            print('Graph, naive, and heap correctness are ready. Performance/visualization are separate.')
    else:
        print('Start with the failing isolated groups. Skipped integration is not a pass.')
    return results


def run_session(stage='all', *, pause=False, seconds=2, color_mode='auto'):
    """Run without argparse or sys.exit; suitable for an IDE Run button."""
    require(color_mode in ('auto', 'always', 'never'), 'Unknown color setting')
    is_terminal = getattr(sys.stdout, 'isatty', lambda: False)()
    use_color = color_mode == 'always' or (color_mode == 'auto' and is_terminal
                                          and 'NO_COLOR' not in os.environ)
    print('DIJKSTRA: CORRECTNESS CHECKS')
    print('Isolated = one student method/function; integration = student components together.')
    rows = run_correctness_tests(stage, pause=pause, seconds=seconds, use_color=use_color)
    return bool(rows) and all(row.status == 'PASS' for row in rows)


def main(argv=None, *, guided=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('graph', 'naive', 'heap', 'all'), default='all',
                        help='graph only, graph+naive, graph+heap, or all (default)')
    parser.add_argument('--no-pause', action='store_true', help='disable section pauses')
    parser.add_argument('--timeout', type=float, default=2, help='seconds per case (default: 2)')
    parser.add_argument('--color', choices=('auto', 'always', 'never'), default='auto')
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be positive and finite')
    ok = run_session(args.stage, pause=guided and not args.no_pause,
                     seconds=args.timeout, color_mode=args.color)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
