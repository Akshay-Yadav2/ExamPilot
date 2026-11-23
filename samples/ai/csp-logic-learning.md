# CSPs, logic and learning

## Constraint satisfaction problems

A CSP has variables, a domain for each variable and constraints on combinations of values. Backtracking search assigns one variable at a time and backtracks when a constraint is violated. Useful heuristics: minimum remaining values (pick the variable with the fewest legal values), degree heuristic (break ties by most constraints), and least constraining value (try the value that rules out the fewest choices for neighbours). Forward checking and arc consistency (AC-3) prune domains early.

## Propositional and first-order logic

A sentence is valid if it is true in every model and satisfiable if it is true in some model. KB entails α (KB ⊨ α) if α is true in every model where KB is true. Resolution is a complete inference rule for propositional logic when sentences are in conjunctive normal form: to prove α, add ¬α to KB and derive the empty clause. First-order logic adds objects, relations and the quantifiers ∀ and ∃.

## Supervised learning

Supervised learning fits a function from labelled examples. The data is split into training, validation and test sets; the test set is used once at the end. Overfitting means low training error but high test error, and is reduced with more data, regularisation or simpler models. The bias-variance trade-off: simple models have high bias, flexible models have high variance.

## Neural networks

A neural network stacks layers of units that compute a weighted sum of their inputs followed by a non-linear activation such as ReLU or sigmoid. Without the non-linearity, any number of layers collapses to a single linear function. Networks are trained by gradient descent on a loss, with backpropagation using the chain rule to compute the gradient for every weight.
