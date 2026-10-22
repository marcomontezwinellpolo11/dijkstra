# Using the Dijkstra lab

## Order of Operations
1. graph.py
2. dijkstra_naive.py
3. dijkstra_heap.py

The test runner (described below) contains unit tests for each of these.
Scaffolded versions (with some of the work completed) are available under
/scaffolds if you get stuck and aren't sure how to proceed.

## Test Suite (run_all_tests)
**Run `run_all_tests.py` in the project folder whenever you want feedback.**
You edit `graph.py`, `dijkstra_naive.py`, and `dijkstra_heap.py`.
The other files provide tests and activities.

If you get stuck, consult the matching file in /scaffolds for additional hints.

Start by pressing Enter for the naive cycle. Read each section, then press Enter
when ready to run the next one. Fix failures in individual methods first.
Integration checks show whether your components work together.

After naive correctness passes, investigate your scan counts. Make a prediction
before running the experiment and discuss the pattern with your teacher. Then
work on the heap version.

When you return for heap work, run the same file and type **heap** at the first
prompt. From a terminal, `python run_all_tests.py --heap` does the same thing.
You don't need to edit a setting or remember other filenames.

After heap correctness passes, you can compare both versions and view a road-map
demonstration. The comparison checks that your naive version works before using
it. The demonstration explains BFS first and Dijkstra second; it uses provided
example algorithms. Follow the explanation of the colors, then press Enter for
each new picture. Earlier pictures may stay above in the output so you can look
back. If a separate plot window opens on your computer, close it to return to
the console before pressing Enter.

Type **q** at any guided prompt to finish. You can skip the scan activity by
typing **heap**, skip the comparison by typing **v**, or skip a chart with **s**
when those options are offered.

There are no automatic grades for your growth-rate predictions. Use the data,
your loop structure, and discussion with your teacher to explain the patterns.
