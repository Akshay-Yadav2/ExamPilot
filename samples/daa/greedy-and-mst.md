# Greedy algorithms and minimum spanning trees

A greedy algorithm builds a solution one step at a time, always taking the choice that looks best right now and never undoing it. Greedy is correct only when the problem has the greedy-choice property, which has to be proved, usually with an exchange argument.

## Exchange arguments

To prove a greedy algorithm optimal, take any optimal solution that differs from the greedy one. Find the first place they differ and show that swapping the optimal solution's choice for the greedy choice does not make it worse. Repeating the swap turns the optimal solution into the greedy one without losing value, so greedy is optimal too.

## Activity selection

Given intervals with start and finish times, choose the largest set of non-overlapping intervals. Sort by finish time and repeatedly take the first interval that starts after the last chosen one finishes. This runs in O(n log n) for the sort. Picking the earliest start or the shortest interval does not work; earliest finish time is the rule with an exchange-argument proof.

## Cut property

A cut partitions the vertices into S and V − S. The cut property says: the minimum-weight edge crossing any cut belongs to some minimum spanning tree (to every MST if weights are distinct). Both Kruskal's and Prim's algorithms are correct because every edge they add is the lightest edge across some cut.

## Kruskal's algorithm

Sort all edges by weight and add each edge if it does not create a cycle with the edges already chosen. Cycle checks use a union-find (disjoint set) structure with union by rank and path compression. Total time is O(E log E), dominated by the sort, which is the same as O(E log V).

## Prim's algorithm

Grow a single tree from a start vertex. Keep a priority queue of vertices outside the tree keyed by the lightest edge connecting them to the tree, and repeatedly add the closest vertex. With a binary heap Prim runs in O(E log V). It looks like Dijkstra, but the key is the weight of one edge, not the total path length.
