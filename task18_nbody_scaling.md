# Task 18 — N-body scaling: direct vs. Barnes–Hut

## Direct all-pairs
Each iteration computes approximately `N(N-1)` pair interactions, or `Theta(N^2)`. With N proportional to P (fixed particles per processor), total work becomes `Theta(P^2)`. Per-processor arithmetic is not constant because each particle must interact with the growing global population. Unless the interaction is approximated or specially structured, iteration time grows with P and weak scaling fails.

## Barnes–Hut
A tree-code typically reduces work to `O(N log N)` (with constants and accuracy depending on distribution and opening criterion). If N grows proportional to P, total work is `O(P log P)`, and average work per processor is roughly `O(log P)` rather than constant. Tree construction, traversal, remote tree data, and load balance also matter. It scales better than direct all-pairs but is not strictly Gustafson-ideal.

The serial/parallel ratio can rise because tree construction and global reductions do not necessarily parallelize proportionally, while irregular traversal and communication grow. For uniform distributions and good spatial decomposition, Barnes–Hut can achieve much better practical scaling than direct N-body; clustered distributions can produce imbalance.
