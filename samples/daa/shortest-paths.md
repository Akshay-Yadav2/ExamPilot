# Shortest paths

Single-source shortest paths: given a weighted directed graph G = (V, E) and a source s, find δ(s, v) for every vertex v. All the algorithms here keep an estimate d[v] that starts at ∞ (d[s] = 0) and only ever goes down through relaxation.

## Relaxation

Relaxing edge (u, v) with weight w(u, v) means: if d[u] + w(u, v) < d[v], set d[v] = d[u] + w(u, v) and set the predecessor π[v] = u. Every algorithm in this lecture is a different order of relaxing edges. Estimates never drop below the true distance, so once d[v] = δ(s, v) it stays there.

## Dijkstra's algorithm

Dijkstra keeps a min-priority queue of vertices keyed by d[v]. It repeatedly extracts the vertex u with the smallest estimate, marks it finished, and relaxes every edge leaving u. With a binary heap the running time is O((V + E) log V); with a Fibonacci heap it is O(E + V log V). Key invariant: when u is extracted, d[u] = δ(s, u). The proof assumes every edge weight is non-negative, so any path that leaves the finished set can only get longer.

## Why Dijkstra fails with negative edge weights

Dijkstra finalises a vertex the moment it is extracted and never revisits it. With a negative edge, a path discovered later can pass through that edge and end up cheaper than the distance that was already locked in. Counterexample: s→a has weight 2, s→b has weight 5, b→a has weight −4. Dijkstra extracts a with d[a] = 2 and finishes it, but the true distance is 1 through b. The algorithm still terminates; it just returns a wrong answer.

## Bellman-Ford

Bellman-Ford relaxes every edge V − 1 times, which is enough because a shortest simple path has at most V − 1 edges. It handles negative edge weights and runs in O(VE). After the V − 1 rounds, one more pass over the edges detects a negative-weight cycle reachable from s: if any edge can still be relaxed, such a cycle exists and shortest paths are undefined.

## Shortest paths in a DAG

In a directed acyclic graph, topologically sort the vertices and relax the outgoing edges of each vertex in that order. Every edge is relaxed exactly once, so the running time is O(V + E), and negative weights are fine because there are no cycles. Negating the weights gives longest paths in a DAG, which is how critical-path scheduling works.

## Floyd-Warshall

Floyd-Warshall computes all-pairs shortest paths with dynamic programming over intermediate vertices. d_k[i][j] is the shortest path from i to j using only vertices 1..k as intermediates, and d_k[i][j] = min(d_{k-1}[i][j], d_{k-1}[i][k] + d_{k-1}[k][j]). Three nested loops give O(V³) time and O(V²) space. Negative edges are allowed; a negative value on the diagonal means a negative cycle.
