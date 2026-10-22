"""Guided observations of student code. No growth-rate answers are printed.

Random graphs are seeded, connected, sparse and identical for both algorithms.
Counters measure different work; timings include tracing overhead so ordinary
Python loops can still be interrupted in local Python and Pickcode.
"""
import random
import statistics
import time

from test_correctness import (run_case, check_solver_result, check_adjacency,
                              build_student_graph)

SIZES = (40, 80, 160, 320)
REPEATS = 3


class ActivityError(Exception):
    pass


def guarded_call(label, function, seconds):
    box = []
    result = run_case('analysis', label, label, lambda: box.append(function()), seconds)
    if result.status != 'PASS':
        raise ActivityError(result.detail)
    return box[0]


def make_adjacency(n, seed=2026):
    rng = random.Random(seed + n)
    adj = {node: {} for node in range(n)}
    def edge(u, v):
        if u != v and v not in adj[u]:
            adj[u][v] = adj[v][u] = rng.randint(1, 20)
    for node in range(1, n):
        edge(node, rng.randrange(node))
    for _ in range(n * 2):
        edge(rng.randrange(n), rng.randrange(n))
    return adj


def known_distances(adj, start=0):
    """Independent Bellman-Ford oracle; never use one student's answer as a key."""
    dist = dict.fromkeys(adj, float('inf'))
    dist[start] = 0
    for _ in range(len(adj) - 1):
        changed = False
        for u, neighbors in adj.items():
            for v, weight in neighbors.items():
                new = dist[u] + weight
                if new < dist[v]:
                    dist[v] = new
                    changed = True
        if not changed:
            break
    return dist


def sample(cls, solver, adj, expected, seconds):
    # A fresh graph prevents one run from changing another run's input.
    graph = guarded_call('graph construction', lambda: build_student_graph(cls, adj), seconds)
    check_adjacency(graph, adj)
    def measured():
        start = time.perf_counter()
        result = solver(graph, 0)
        return result, time.perf_counter() - start
    result, elapsed = guarded_call(solver.__name__, measured, seconds)
    check_solver_result(result, adj, 0, expected)
    check_adjacency(graph, adj)
    return result[2], elapsed


def show_plot(make_figure):
    """Import plotting only on demand; tables remain useful if it is unavailable."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        print(f'Chart unavailable: {exc}. The table above still contains the results.')
        return
    figure = None
    try:
        figure = make_figure(plt)
        print('If a separate plot window opens, close it to return to the console.')
        plt.show()
    finally:
        if figure is not None:
            plt.close(figure)


def ratio(value, previous):
    return '-' if previous in (None, 0) else f'{value / previous:.2f}x'


def run_scan_count(cls, solver, *, prompt, plots=True, seconds=5):
    print('\nSCAN-COUNT INVESTIGATION')
    print('Each graph has twice as many nodes as the previous graph.')
    print('Your counter should count each candidate examined while selecting the next node.')
    print('Predict: when the number of nodes doubles, what will happen to the scan count?')
    prompt('Discuss or write your prediction. Press Enter to run the experiment: ')
    rows = []
    previous = None
    print(f"\n{'Nodes':>8} {'Undirected edges':>18} {'Scan steps':>14} {'Change':>10}")
    for n in SIZES:
        adj = make_adjacency(n)
        ops, _ = sample(cls, solver, adj, known_distances(adj), seconds)
        edges = sum(map(len, adj.values())) // 2
        print(f'{n:>8} {edges:>18} {ops:>14,} {ratio(ops, previous):>10}', flush=True)
        rows.append((n, ops))
        previous = ops
    if not any(ops for _, ops in rows):
        print('All counts are zero. Inspect where you increment op_count before interpreting this experiment.')
    print('\nDiscuss: how does doubling the input change the work?')
    print('Which part of your loop accounts for that pattern? What would you predict for 640 nodes?')
    print('What information would help you choose the next node without scanning every remaining node?')
    if plots:
        if prompt('Press Enter to view the scan-count chart, or s to skip the chart: ', ('', 's')) == '':
            def chart(plt):
                fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
                ax.plot([r[0] for r in rows], [r[1] for r in rows], 'o-', linewidth=2, color='#2563eb')
                ax.set(title='Your scan count as the graph grows', xlabel='Nodes', ylabel='Candidates examined')
                ax.grid(alpha=.25)
                return fig
            show_plot(chart)
    return rows


def run_comparison(cls, naive, heap, *, prompt, plots=True, seconds=5):
    print('\nCOMPARE YOUR IMPLEMENTATIONS')
    print('Both versions receive the same seeded graph at each size, with three runs each.')
    print('Scan steps and heap pops count different kinds of work; their ratio is not a speedup.')
    print('Elapsed times include loop-safety checks. Treat them as rough observations, not precise benchmarks.')
    print('Predict: which measurements will change most after replacing the scan with a heap?')
    prompt('Press Enter to measure both implementations: ')
    rows = []
    print(f"\n{'Nodes':>6} {'Scan steps':>12} {'Heap pops':>12} {'Naive sec*':>12} {'Heap sec*':>12}")
    for n in SIZES:
        adj = make_adjacency(n)
        expected = known_distances(adj)
        samples = {'naive': [], 'heap': []}
        for repeat in range(REPEATS):
            order = [('naive', naive), ('heap', heap)]
            if repeat % 2:
                order.reverse()
            for label, solver in order:
                samples[label].append(sample(cls, solver, adj, expected, seconds))
        scan = statistics.median(x[0] for x in samples['naive'])
        pops = statistics.median(x[0] for x in samples['heap'])
        nt = statistics.median(x[1] for x in samples['naive'])
        ht = statistics.median(x[1] for x in samples['heap'])
        rows.append((n, scan, pops, nt, ht))
        print(f'{n:>6} {scan:>12,.0f} {pops:>12,.0f} {nt:>12.5f} {ht:>12.5f}', flush=True)
    print('\n* Median elapsed seconds with loop protection enabled.')
    print('Discuss: compare each counter with ITSELF as the graph grows.')
    print('Does one heap pop represent the same work as one candidate examined? What is missing from those counters?')
    print('Which parts of Dijkstra stayed the same? Which part did the new data structure change?')
    print('What growth model would you propose for each implementation, and what evidence supports it?')
    if plots and prompt('Press Enter to view the comparison charts, or s to skip them: ', ('', 's')) == '':
        def chart(plt):
            fig, axes = plt.subplots(3, 1, figsize=(10, 11), constrained_layout=True)
            data = [(1, 'Naive scan steps', 'Candidates examined', '#2563eb'),
                    (2, 'Heap removals', 'Heap pops', '#d97706')]
            for ax, (col, title, ylabel, color) in zip(axes, data):
                ax.plot([r[0] for r in rows], [r[col] for r in rows], 'o-', color=color)
                ax.set(title=title, xlabel='Nodes', ylabel=ylabel)
                ax.grid(alpha=.25)
            axes[2].plot([r[0] for r in rows], [r[3] for r in rows], 'o-', label='Naive')
            axes[2].plot([r[0] for r in rows], [r[4] for r in rows], 'o-', label='Heap')
            axes[2].set(title='Median elapsed time (includes loop-protection overhead)', xlabel='Nodes', ylabel='Seconds')
            axes[2].legend()
            axes[2].grid(alpha=.25)
            return fig
        show_plot(chart)
    return rows


if __name__ == '__main__':
    print('Start run_all_tests.py in the project folder. It checks correctness before these activities.')
