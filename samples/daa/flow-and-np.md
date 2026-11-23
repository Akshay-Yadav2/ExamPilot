# Network flow and NP-completeness

## Flow networks

A flow network is a directed graph with a source s, a sink t and a capacity c(u, v) ≥ 0 on each edge. A flow respects capacities (0 ≤ f(u, v) ≤ c(u, v)) and conservation (flow in equals flow out at every vertex except s and t). The value of a flow is the net flow leaving s.

## Ford-Fulkerson method

Start with zero flow. While the residual graph has an augmenting path from s to t, push as much flow as the path's bottleneck residual capacity allows. Residual edges include backward edges, which let the algorithm undo flow sent earlier. With integer capacities it terminates in O(E·|f*|). Edmonds-Karp picks the shortest augmenting path with BFS and runs in O(VE²) regardless of capacities.

## Max-flow min-cut theorem

An s-t cut (S, T) has capacity equal to the sum of capacities of edges from S to T. The max-flow min-cut theorem says the maximum flow value equals the minimum cut capacity. When Ford-Fulkerson stops, the vertices reachable from s in the residual graph form S of a minimum cut.

## Bipartite matching

To find a maximum matching in a bipartite graph with sides L and R, add a source connected to every vertex in L and a sink connected from every vertex in R, give every edge capacity 1, and run max flow. Integer capacities give an integral maximum flow, and the edges from L to R carrying flow form a maximum matching.

## P, NP and reductions

P is the class of decision problems solvable in polynomial time. NP is the class whose yes-instances have certificates that can be checked in polynomial time. A polynomial-time reduction A ≤p B transforms instances of A into instances of B with the same answer. If A ≤p B and B is in P, then A is in P. To show a new problem is hard, reduce a known hard problem to it, not the other way around.

## NP-completeness

A problem is NP-complete if it is in NP and every problem in NP reduces to it. Cook-Levin: SAT is NP-complete. Standard chain: SAT ≤p 3-SAT ≤p Independent Set ≤p Vertex Cover, and 3-SAT ≤p Subset Sum. To prove X is NP-complete: show X is in NP, then reduce a known NP-complete problem to X and prove both directions of the correspondence.
