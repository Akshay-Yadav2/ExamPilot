# Markov decision processes and reinforcement learning

## Markov decision processes

An MDP has states S, actions A, a transition model P(s' | s, a), a reward function R(s, a, s') and a discount factor γ between 0 and 1. The Markov property says the next state depends only on the current state and action. A policy π maps states to actions, and the goal is a policy that maximises expected discounted reward.

## Bellman equations

The optimal value function satisfies the Bellman optimality equation: V*(s) = max_a Σ_{s'} P(s' | s, a) [R(s, a, s') + γ V*(s')]. The Q-value Q*(s, a) is the expected utility of taking action a in s and acting optimally afterwards, and V*(s) = max_a Q*(s, a).

## Value iteration

Value iteration starts with V_0(s) = 0 and repeatedly applies the Bellman optimality update to every state: V_{k+1}(s) = max_a Σ P(s' | s, a)[R + γ V_k(s')]. It converges to V* when γ < 1, and the optimal policy is extracted by acting greedily with respect to the final values. Each iteration costs O(S²A).

## Policy iteration

Policy iteration alternates two steps. Policy evaluation computes V^π for the current fixed policy, either by solving a system of linear equations or by iterating the Bellman expectation equation. Policy improvement makes the policy greedy with respect to V^π. It stops when the policy no longer changes and usually needs far fewer iterations than value iteration, though each iteration is more expensive.

## Q-learning

Q-learning is model-free reinforcement learning: the agent does not know P or R and learns from experienced transitions (s, a, r, s'). The update is Q(s, a) ← Q(s, a) + α [r + γ max_{a'} Q(s', a') − Q(s, a)]. It is off-policy: it learns the optimal Q-values while following an exploratory policy such as ε-greedy, which picks a random action with probability ε.
