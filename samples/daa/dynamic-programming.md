# Dynamic programming

Dynamic programming solves a problem by combining solutions to overlapping subproblems, solving each subproblem once and storing the answer. It applies when the problem has optimal substructure (an optimal solution contains optimal solutions to subproblems) and overlapping subproblems (a naive recursion solves the same subproblem many times).

## Recipe

1. Define the subproblem in words, for example "OPT(i, w) = best value using items 1..i with capacity w".
2. Write the recurrence, including base cases.
3. Pick an evaluation order so every subproblem is computed after the ones it depends on.
4. Recover the actual solution, not just its value, by storing choices or walking the table backwards.
Most lost points on exams come from skipping step 1 and writing a table without saying what an entry means.

## Memoization vs tabulation

Memoization is top-down: write the recursion and cache results in a dictionary or array, so each subproblem is computed once. Tabulation is bottom-up: fill a table in an order that respects dependencies. Both have the same asymptotic running time. Memoization only touches the subproblems that are actually needed; tabulation avoids recursion overhead and makes it easy to cut space by keeping only the previous row.

## 0/1 knapsack

Items have weights w_i and values v_i, capacity W. OPT(i, c) = max(OPT(i − 1, c), v_i + OPT(i − 1, c − w_i)) when w_i ≤ c. The table has n·W entries, each filled in O(1), so the algorithm runs in O(nW). This is pseudo-polynomial, not polynomial: W is written with only log W bits, so O(nW) is exponential in the size of the input. Knapsack is NP-hard, which is consistent with this.

## Longest common subsequence

For strings X of length m and Y of length n, let c[i][j] be the LCS length of the prefixes X[1..i] and Y[1..j]. If X[i] = Y[j] then c[i][j] = c[i − 1][j − 1] + 1, otherwise c[i][j] = max(c[i − 1][j], c[i][j − 1]). Base cases c[0][j] = c[i][0] = 0. Time and space are O(mn); the length alone needs only two rows of space.

## Edit distance

Edit distance is the minimum number of insertions, deletions and substitutions that turn X into Y. D[i][j] = min(D[i − 1][j] + 1, D[i][j − 1] + 1, D[i − 1][j − 1] + [X[i] ≠ Y[j]]), with D[i][0] = i and D[0][j] = j. It runs in O(mn). The same table shape as LCS, but minimising cost instead of maximising matches.
