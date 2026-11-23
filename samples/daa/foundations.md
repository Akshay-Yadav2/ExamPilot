# Foundations: asymptotics, divide and conquer, graph search

## Asymptotic notation

f(n) = O(g(n)) means there are constants c > 0 and n₀ such that f(n) ≤ c·g(n) for all n ≥ n₀: an upper bound. Ω is the matching lower bound and Θ means both hold. Constant factors and lower-order terms are ignored, so 3n² + 10n log n = Θ(n²). A common exam trap: O is an upper bound, so n = O(n²) is true, just not tight.

## Divide and conquer and the master theorem

Divide and conquer splits a problem into a subproblems of size n/b, solves them recursively, and combines the results in f(n) time, giving T(n) = aT(n/b) + f(n). Compare f(n) with n^(log_b a). If f is polynomially smaller, T(n) = Θ(n^(log_b a)). If they are equal up to Θ, T(n) = Θ(n^(log_b a) log n). If f is polynomially larger and regular, T(n) = Θ(f(n)). Merge sort is a = 2, b = 2, f(n) = Θ(n), so Θ(n log n).

## BFS, DFS and topological sort

Breadth-first search visits vertices in order of distance from the source using a queue and finds shortest paths in unweighted graphs in O(V + E). Depth-first search explores as deep as possible first and records discovery and finish times. Ordering vertices by decreasing DFS finish time gives a topological sort of a DAG. A back edge found during DFS means the graph has a cycle.

## Strongly connected components

A strongly connected component is a maximal set of vertices where every vertex can reach every other. Kosaraju's algorithm runs DFS once to get finish times, transposes the graph, then runs DFS on the transpose in decreasing finish-time order; each tree of the second pass is one SCC. Total time is O(V + E). Contracting each SCC to a single vertex gives a DAG.
