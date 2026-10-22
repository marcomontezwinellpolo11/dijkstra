"""Run this file locally or with Pickcode's Run button.

Enter = naive cycle; type heap = heap cycle. No settings need editing.
Terminal shortcuts: --heap, --stage graph, --correctness-only, --no-pause.
"""
import argparse
import importlib
import math
import os
import sys

from test_correctness import run_correctness_tests, TestTimeout


class FinishSession(Exception):
    """A normal user-requested finish, not a test failure."""


def choose(message, allowed=('',), *, eof='q'):
    """Only explicit Enter advances; closed input never launches a demo."""
    while True:
        try:
            answer = input(message).strip().lower()
        except (EOFError, OSError):
            answer = eof
        if answer == 'q':
            raise FinishSession()
        if answer in allowed:
            return answer
        print('Choose ' + ', '.join('Enter' if x == '' else x for x in allowed) + ', or q to finish.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    start = parser.add_mutually_exclusive_group()
    start.add_argument('--heap', action='store_true', help='go directly to heap correctness')
    start.add_argument('--stage', choices=('graph', 'naive', 'heap', 'all'), help='choose the starting stage')
    parser.add_argument('--correctness-only', action='store_true', help='skip analysis and plots')
    parser.add_argument('--no-pause', action='store_true', help='run correctness only, with no input prompts')
    parser.add_argument('--no-plots', action='store_true', help='keep analysis tables; skip charts and visualization')
    parser.add_argument('--timeout', type=float, default=2, help='seconds per correctness check')
    parser.add_argument('--color', choices=('auto', 'always', 'never'), default='always')
    parser.add_argument('--visualization-mode', choices=('step', 'auto'), default='step')
    parser.add_argument('--delay', type=float, default=4, help='seconds per frame in optional auto mode')
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be positive and finite')
    if not math.isfinite(args.delay) or args.delay <= 0:
        parser.error('--delay must be positive and finite')
    terminal = getattr(sys.stdout, 'isatty', lambda: False)()
    use_color = (args.color == 'always' or args.color == 'auto' and terminal) and 'NO_COLOR' not in os.environ
    analysis = not (args.correctness_only or args.no_pause)
    graph_verified = False
    naive_verified = False
    any_failure = False
    session_rows = []

    def cycle(kind):
        nonlocal graph_verified, naive_verified, any_failure
        print('\n' + '=' * 60)
        print(('NAIVE CYCLE' if kind == 'naive' else 'HEAP CYCLE' if kind == 'heap' else 'GRAPH') + ': CORRECTNESS')
        print('Isolated checks test one student function. Integration checks combine them.')
        first = True

        def before_section(title):
            nonlocal first
            if not first and not args.no_pause:
                choose('\nPress Enter to run ' + title.lower() + ', or q to finish: ')
            first = False

        rows = run_correctness_tests(kind, before_section=before_section,
                                     seconds=args.timeout, use_color=use_color,
                                     graph_verified=graph_verified and kind != 'graph')
        session_rows.extend(rows)
        ok = bool(rows) and all(row.status == 'PASS' for row in rows)
        any_failure |= not ok
        if ok:
            graph_verified = True
            if kind == 'naive':
                naive_verified = True
        return ok

    def activity(label, function):
        """A display/experiment failure does not rewrite correctness results."""
        try:
            function()
            return True
        except (Exception, TestTimeout, SystemExit) as exc:
            if isinstance(exc, FinishSession):
                raise
            print(f'\n{label} stopped: {type(exc).__name__}: {exc}')
            print('Your correctness results above still stand. You can continue to the next activity.')
            return False

    try:
        print('DIJKSTRA LAB')
        print('Implement graph -> complete naive -> investigate its work -> optimize with a heap.')
        print('Press Enter at each reading break; q finishes the session.')
        stage = 'heap' if args.heap else args.stage
        if stage is None:
            stage = 'naive' if args.no_pause else (
                'heap' if choose('\nPress Enter for naive correctness, or type heap to go directly to heap correctness: ', ('', 'heap')) == 'heap' else 'naive')
        if stage == 'all':
            stage = 'naive'
        if stage == 'graph':
            cycle('graph')
            return 1 if any_failure else 0

        if stage == 'naive':
            passed = cycle('naive')
            if not passed:
                print('\nNaive analysis is waiting for the graph and naive correctness checks to pass.')
                if args.no_pause:
                    # A diagnostic run still reaches independent heap checks.
                    cycle('heap')
                    return 1
                answer = choose('Press Enter to finish and fix these errors, or type heap to check heap code anyway: ', ('', 'heap'))
                if answer == '':
                    return 1
            elif analysis:
                answer = choose('\nNaive correctness passed. Enter = scan-count activity; heap = skip to heap correctness: ', ('', 'heap'))
                if answer == '':
                    def scans():
                        from demonstrations.performance import run_scan_count
                        run_scan_count(importlib.import_module('graph').WeightedGraph,
                                       importlib.import_module('dijkstra_naive').dijkstra_naive,
                                       prompt=choose, plots=not args.no_plots,
                                       seconds=max(5, args.timeout))
                    activity('Scan-count activity', scans)
                    print('\nNext work: implement dijkstra_heap.py. When ready, run this file and type heap.')
                    choose('Press Enter to check heap code now, or q to finish here: ')
            elif not args.no_pause:
                choose('\nPress Enter for heap correctness, or q to finish: ')

        if not cycle('heap'):
            print('\nComparison and visualization are waiting for heap correctness to pass.')
            return 1
        if not analysis:
            return 1 if any_failure else 0

        answer = choose('\nHeap correctness passed. Enter = compare implementations; v = skip to visualization: ', ('', 'v'))
        if answer == '':
            if not naive_verified:
                print('\nThe comparison also needs a working naive implementation.')
                print('Its correctness will be checked now; the earlier scan-count activity will not repeat.')
                check_naive = choose('Press Enter to check naive correctness for the comparison, or v to skip the comparison: ', ('', 'v'))
                if check_naive == '':
                    cycle('naive')
            if naive_verified:
                def comparison():
                    from demonstrations.performance import run_comparison
                    run_comparison(importlib.import_module('graph').WeightedGraph,
                                   importlib.import_module('dijkstra_naive').dijkstra_naive,
                                   importlib.import_module('dijkstra_heap').dijkstra_heap,
                                   prompt=choose, plots=not args.no_plots,
                                   seconds=max(5, args.timeout))
                activity('Comparison activity', comparison)
            else:
                print('Comparison skipped: both implementations must pass correctness first.')

        if args.no_plots:
            print('Visualization skipped (--no-plots).')
        else:
            def visualization():
                from demonstrations.bfs_vs_dijkstra import run_visualization
                run_visualization(prompt=choose, mode=args.visualization_mode, delay=args.delay)
            # The visualization introduces its colors BEFORE asking to begin.
            activity('Visualization', visualization)
        print('\nLab session complete. Bring your observations and predictions to your teacher.')
        return 1 if any_failure else 0
    except FinishSession:
        print('\nSession finished. Run run_all_tests.py again whenever you are ready.')
        return 1 if any_failure else 0
    finally:
        if session_rows:
            passed = sum(row.status == 'PASS' for row in session_rows)
            failed = sum(row.status == 'FAIL' for row in session_rows)
            skipped = sum(row.status == 'SKIP' for row in session_rows)
            print(f'\nCorrectness this session: {passed} passed, {failed} failed, {skipped} skipped sections.')


if __name__ == '__main__':
    sys.exit(main())
