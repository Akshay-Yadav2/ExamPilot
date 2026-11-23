# Probability and Bayesian networks

## Bayes' rule

Bayes' rule: P(A | B) = P(B | A) P(A) / P(B). It turns a causal model P(effect | cause) into a diagnostic one P(cause | effect). Example: a test for a disease with 1% prevalence, 90% sensitivity and a 5% false positive rate gives P(disease | positive) = 0.009 / (0.009 + 0.0495) ≈ 0.15, much lower than most people guess.

## Independence and conditional independence

A and B are independent if P(A, B) = P(A) P(B). A and B are conditionally independent given C if P(A, B | C) = P(A | C) P(B | C). Conditional independence is what makes large joint distributions tractable: naive Bayes assumes all features are conditionally independent given the class.

## Bayesian networks

A Bayesian network is a directed acyclic graph where each node is a random variable with a conditional probability table P(X | Parents(X)). The joint distribution factorises as the product of these tables: P(x_1, ..., x_n) = Π_i P(x_i | parents(X_i)). A node is conditionally independent of its non-descendants given its parents.

## D-separation

In a chain A → B → C or a common cause A ← B → C, observing B blocks the path between A and C. In a common effect (v-structure) A → B ← C, A and C are independent until B or one of its descendants is observed; observing it makes them dependent, which is called explaining away.

## Inference

Exact inference by enumeration sums the joint distribution over the hidden variables and is exponential in the number of variables. Variable elimination does the same computation but caches intermediate factors and eliminates variables one at a time. Approximate methods such as rejection sampling and likelihood weighting estimate probabilities from samples.
