# Adversarial search

Games like chess are modelled as two-player, zero-sum, deterministic games with perfect information. MAX tries to maximise the utility at the end of the game and MIN tries to minimise it.

## Minimax

Minimax computes the value of each node by assuming both players play optimally: a MAX node takes the maximum of its children's values and a MIN node takes the minimum. It is a complete depth-first exploration of the game tree, with time O(b^m) and space O(bm), where m is the maximum depth.

## Alpha-beta pruning

Alpha-beta pruning returns the same value as minimax while skipping branches that cannot influence the decision. Alpha is the best value MAX can guarantee so far on the path, and beta is the best value MIN can guarantee. When a node's value is known to be worse than alpha or beta allows, its remaining children are pruned. Pruning never changes the result at the root.

## Move ordering

The effectiveness of alpha-beta depends on the order in which moves are examined. With perfect move ordering alpha-beta examines O(b^(m/2)) nodes, so the effective branching factor drops to √b and the search can go about twice as deep as minimax in the same time. With random ordering it is roughly O(b^(3m/4)).

## Cutoffs and evaluation functions

Real games are too deep to search to the end, so search stops at a depth limit and applies an evaluation function that estimates the utility of a position, usually a weighted sum of features such as material. A quiescence search extends the search in unstable positions, for example during an exchange of pieces, to avoid the horizon effect.
