# Search

A search problem has an initial state, actions, a transition model, a goal test and a path cost. Search algorithms build a tree of paths from the initial state; graph search additionally remembers explored states so it does not expand the same state twice.

## Uninformed search

Breadth-first search expands the shallowest node first using a FIFO queue. It is complete and optimal when all step costs are equal, with time and space O(b^d), where b is the branching factor and d the depth of the shallowest goal. Depth-first search uses a LIFO stack, needs only O(bm) space, but is not optimal and not complete in infinite spaces. Uniform-cost search expands the node with the lowest path cost g(n) and is optimal for any non-negative step costs.

## Iterative deepening

Iterative deepening runs depth-limited DFS with limits 0, 1, 2, ... until it finds a goal. It combines the O(bd) memory of DFS with the completeness and optimality (for unit costs) of BFS. Re-expanding the upper levels costs little because most nodes are at the deepest level.

## Greedy best-first and A*

Greedy best-first search expands the node with the smallest heuristic h(n), the estimated cost to the goal. It is fast but neither complete nor optimal. A* expands the node with the smallest f(n) = g(n) + h(n), the estimated cost of the cheapest solution through n.

## Admissible and consistent heuristics

A heuristic is admissible if it never overestimates the true cost to reach the goal. A heuristic is consistent if h(n) ≤ c(n, a, n') + h(n') for every successor n'. Consistency implies admissibility. A* tree search is optimal with an admissible heuristic; A* graph search is optimal with a consistent heuristic. For the 8-puzzle, the number of misplaced tiles and the Manhattan distance are both admissible, and Manhattan distance dominates misplaced tiles.
