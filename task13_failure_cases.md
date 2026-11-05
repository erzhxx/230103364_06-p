# Task 13 — Cases where ideal weak scaling fails

## 1. All-pairs N-body with direct interactions
For N particles, each particle interacts with N-1 others, so work is `O(N^2)`. If N grows in proportion to P to keep particles per processor fixed, total work grows as `O(P^2)`, not O(P). The interaction count per particle grows with global N, and data exchange/force accumulation can increase. Constant local workload is therefore not enough to preserve constant iteration time.

## 2. Breadth-first search on power-law graphs
Increasing graph size and processor count does not preserve a fixed local amount of useful work at every level. Frontier sizes vary dramatically; high-degree hubs create contention, remote adjacency-list accesses, and load imbalance. Global frontier termination and visited-state synchronization require communication. A larger graph can increase synchronization depth and skew, so elapsed time is not constant.

Other examples include distributed sorting with global all-to-all exchanges and sparse iterative solvers whose convergence iteration count changes with problem size. Gustafson's premise is most credible when per-processor work remains similar and communication/algorithmic structure do not deteriorate.
