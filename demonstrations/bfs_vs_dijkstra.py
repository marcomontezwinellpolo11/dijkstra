"""Large, sequential snapshots using the show/pause approach from visualize2.

BFS runs first, then Dijkstra. Default: Enter advances each frame.
Images are not cleared from browser output history. No FuncAnimation is used.
This is a provided conceptual demonstration, not a recording of student code.

Optional direct launch from the project folder:
    python -m demonstrations.bfs_vs_dijkstra
    python -m demonstrations.bfs_vs_dijkstra --auto --delay 4
"""
from collections import deque
import heapq
import math
import textwrap

from .city_map import DEMO_EDGES, DEMO_POSITIONS, adjacency

COLORS = {'unseen': '#e5e7eb', 'frontier': '#bae6fd', 'processed': '#2563eb',
          'current': '#fbbf24', 'path': '#22c55e'}
BACKGROUND = '#111827'


def reconstruct(parent, start, end):
    if end not in parent:
        return None
    path, node = [], end
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path if path and path[0] == start else None


def record_bfs(adj, start, end):
    queue = deque([start])
    discovered = {start}
    processed = set()
    parent = {start: None}
    steps = []

    def snapshot(current, action, done=False, path=None):
        steps.append(dict(current=current, processed=frozenset(processed),
                          frontier=frozenset(queue), waiting=list(queue),
                          action=action, done=done, path=path))
    snapshot(None, f'Start with {start} in the queue. Road costs are ignored when choosing the next node.')
    found = False
    while queue:
        node = queue.popleft()
        if node == end:
            found = True
            processed.add(node)
            snapshot(node, f'{end} reached. Stop the search and follow the parent links.')
            break
        added = []
        for neighbor in adj[node]:
            if neighbor not in discovered:
                discovered.add(neighbor)
                parent[neighbor] = node
                queue.append(neighbor)
                added.append(neighbor)
        processed.add(node)
        detail = ', '.join(added) if added else 'none'
        snapshot(node, f'Expand {node}. Add newly discovered neighbors to the back of the queue: {detail}.')
    path = reconstruct(parent, start, end) if found else None
    snapshot(None, 'Follow parent links to recover the route.' if path else 'The queue is empty; no route exists.', True, path)
    return steps


def record_dijkstra(adj, start, end):
    dist = dict.fromkeys(adj, float('inf'))
    dist[start] = 0
    parent = {start: None}
    heap = [(0, start)]
    processed = set()
    steps = []

    def snapshot(current, action, done=False, path=None):
        waiting = sorted((cost, node) for node, cost in dist.items()
                         if node not in processed and cost < float('inf'))
        steps.append(dict(current=current, processed=frozenset(processed),
                          frontier=frozenset(node for _, node in waiting), waiting=waiting,
                          dist=dict(dist), action=action, done=done, path=path))
    snapshot(None, f'Best known cost to {start} is 0. All other costs begin at infinity.')
    found = False
    while heap:
        cost, node = heapq.heappop(heap)
        if node in processed:
            continue
        processed.add(node)
        if node == end:
            found = True
            snapshot(node, f'{end} selected at cost {cost}. Its cheapest route is now settled.')
            break
        improvements = []
        for neighbor, weight in adj[node].items():
            new_cost = cost + weight
            if new_cost < dist[neighbor]:
                old = dist[neighbor]
                dist[neighbor] = new_cost
                parent[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))
                improvements.append(f'{neighbor}: {format_cost(old)} -> {format_cost(new_cost)}')
        detail = '; '.join(improvements) if improvements else 'none'
        snapshot(node, f'Expand {node} at cost {cost}. Improve best known costs: {detail}.')
    path = reconstruct(parent, start, end) if found else None
    snapshot(None, 'Follow predecessor links to recover the route.' if path else 'No reachable candidates remain.', True, path)
    return steps


def format_cost(value):
    return 'infinity' if value == float('inf') else f'{value:g}'


def path_cost(adj, path):
    return sum(adj[u][v] for u, v in zip(path, path[1:]))


def node_state(node, step):
    if step['done'] and node in (step['path'] or []):
        return 'path'
    if node == step['current']:
        return 'current'
    if node in step['processed']:
        return 'processed'
    if node in step['frontier']:
        return 'frontier'
    return 'unseen'


def render_frame(algorithm, step, index, total, adj, start, end):
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Patch

    fig = plt.figure(figsize=(12, 8), dpi=120, facecolor=BACKGROUND)
    ax = fig.add_axes([.06, .27, .88, .56])
    ax.set(xlim=(-.9, 6.9), ylim=(-.65, 3.8))
    ax.axis('off')
    title = 'BFS: explore by number of roads' if algorithm == 'BFS' else 'Dijkstra: explore by best known cost'
    fig.text(.5, .955, title, ha='center', color='white', fontsize=20, weight='bold')
    fig.text(.5, .905, f'{start} to {end}   |   Step {index + 1} of {total}',
             ha='center', color='#cbd5e1', fontsize=15)
    path_edges = set()
    if step['done'] and step['path']:
        path_edges = {frozenset((u, v)) for u, v in zip(step['path'], step['path'][1:])}
    drawn = set()
    for u, neighbors in adj.items():
        for v, weight in neighbors.items():
            key = frozenset((u, v))
            if key in drawn:
                continue
            drawn.add(key)
            x1, y1 = DEMO_POSITIONS[u]
            x2, y2 = DEMO_POSITIONS[v]
            highlighted = key in path_edges
            ax.plot([x1, x2], [y1, y2], lw=4 if highlighted else 2,
                    color=COLORS['path'] if highlighted else '#94a3b8', zorder=1)
            dx, dy = x2-x1, y2-y1
            length = math.hypot(dx, dy)
            mx = (x1+x2)/2 - .13*dy/length
            my = (y1+y2)/2 + .13*dx/length
            ax.text(mx, my, str(weight), color='white', ha='center', va='center',
                    fontsize=15, weight='bold', zorder=4,
                    bbox=dict(boxstyle='round,pad=.2', facecolor=BACKGROUND, edgecolor='none'))
    for node, (x, y) in DEMO_POSITIONS.items():
        state = node_state(node, step)
        height = .50 if 'dist' in step else .40
        box = FancyBboxPatch((x-.66, y-height/2), 1.32, height,
                             boxstyle='round,pad=.03,rounding_size=.08',
                             facecolor=COLORS[state], edgecolor='white', lw=1, zorder=5)
        ax.add_patch(box)
        label = node
        if 'dist' in step:
            value = step['dist'][node]
            label += '\ncost: ' + ('\u221e' if value == float('inf') else format_cost(value))
        ax.text(x, y, label, ha='center', va='center', fontsize=13,
                color='white' if state == 'processed' else '#111827',
                weight='bold', linespacing=1.4, zorder=6)
        if node in (start, end):
            ax.text(x, y+height/2+.12, 'START' if node == start else 'GOAL',
                    ha='center', color='#cbd5e1', fontsize=11, weight='bold')
    action = step['action']
    if step['done'] and step['path']:
        action = 'Route: ' + ' -> '.join(step['path'])
        action += f"\n{len(step['path'])-1} roads; total cost {path_cost(adj, step['path'])}."
    else:
        action = '\n'.join(textwrap.wrap(action, 92))
    fig.text(.07, .205, action, va='top', color='white', fontsize=13, linespacing=1.4)
    if not step['done']:
        waiting = (', '.join(step['waiting']) if algorithm == 'BFS' else
                   ', '.join(f'{node} ({format_cost(cost)})' for cost, node in step['waiting']))
        label = 'Queue, next first: ' if algorithm == 'BFS' else 'Best waiting candidates: '
        fig.text(.07, .105, '\n'.join(textwrap.wrap(label + (waiting or 'empty'), 100)),
                 color='#cbd5e1', fontsize=11, va='top')
    handles = [Patch(facecolor=COLORS[key], label=label) for key, label in
               [('unseen', 'Not reached'), ('frontier', 'Waiting'), ('processed', 'Processed'),
                ('current', 'Current'), ('path', 'Final route')]]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .015),
               ncol=5, fontsize=11, frameon=False, labelcolor='white')
    return fig


def run_visualization(*, prompt, mode='step', delay=4):
    if mode not in ('step', 'auto') or not math.isfinite(delay) or delay <= 0:
        raise ValueError('Use mode=step or auto, and a positive finite delay.')
    print('\nBFS, THEN DIJKSTRA: A GUIDED ROAD-MAP DEMONSTRATION')
    print('This provided example illustrates the algorithms; it is not a recording of your code.')
    print('Road labels are travel costs. BFS chooses by hop count; Dijkstra chooses by total cost.')
    print('Gray = not reached; light blue = waiting; blue = processed; orange = current; green = final route.')
    print('A frame shows the current node and the changes from examining its roads.')
    print('Dijkstra labels show best known costs; waiting nodes may still receive improvements.')
    print('We will finish BFS before starting Dijkstra on exactly the same map.')
    print('Each image may remain in Pickcode output so you can scroll back.')
    print('Locally, close a separate plot window to return to the console before pressing Enter.')
    print('Predict: will the route with the fewest roads also have the smallest total cost?')
    prompt('Press Enter to begin BFS, or q to finish: ')
    import matplotlib.pyplot as plt
    adj = adjacency(DEMO_EDGES)
    start, end = 'Ashford', 'Ivywood'
    results = {}
    old_interactive = plt.isinteractive()
    try:
        plt.ioff()
        for algorithm, recorder in [('BFS', record_bfs), ('Dijkstra', record_dijkstra)]:
            if algorithm == 'Dijkstra':
                print('\nBFS is finished. Before Dijkstra, predict where considering road costs could change the choices.')
                prompt('Press Enter to start Dijkstra, or q to finish: ')
            steps = recorder(adj, start, end)
            for index, step in enumerate(steps):
                if index and mode == 'step':
                    prompt(f'Press Enter for {algorithm} step {index + 1}/{len(steps)}, or q to finish: ')
                print(f'\n{algorithm} step {index + 1}/{len(steps)}: {step["action"]}')
                fig = render_frame(algorithm, step, index, len(steps), adj, start, end)
                try:
                    if mode == 'auto':
                        # The same show/pause mechanism as visualize2, with a
                        # longer delay and a fresh full-width figure per frame.
                        plt.show(block=False)
                        plt.pause(delay)
                    else:
                        # Closing the live figure does not erase an already
                        # published image in an IDE's output history.
                        plt.show()
                finally:
                    plt.close(fig)
            path = steps[-1]['path']
            results[algorithm] = path
            print(f'{algorithm} route: ' + ' -> '.join(path))
            print(f'{len(path)-1} roads; total cost {path_cost(adj, path)}.')
    finally:
        plt.interactive(old_interactive)
    print('\nDiscuss: why did the algorithms choose different routes?')
    print('Which question does each algorithm answer? When would they agree?')
    return results


if __name__ == '__main__':
    import argparse
    from run_all_tests import choose, FinishSession
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--auto', action='store_true')
    parser.add_argument('--delay', type=float, default=4)
    args = parser.parse_args()
    try:
        run_visualization(prompt=choose, mode='auto' if args.auto else 'step', delay=args.delay)
    except FinishSession:
        print('Visualization finished.')
