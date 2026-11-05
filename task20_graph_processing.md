# Task 20 — BFS and PageRank on power-law graphs

Dense linear algebra usually has regular data layout, predictable work, and contiguous communication patterns. Power-law graph workloads are irregular: a small number of high-degree vertices (hubs) coexist with many low-degree vertices, producing skewed work and memory traffic.

BFS frontier sizes vary by level. Some levels expose abundant parallelism; others are narrow and leave processors idle. High-degree vertices can cause atomic-update contention, duplicate edge visits, and uneven partition loads. Distributed BFS also needs frontier exchange and global termination detection.

PageRank performs repeated sparse matrix-vector-like updates, but adjacency lists cause irregular gathers, and each iteration needs rank contributions to be aggregated. Communication volume and memory latency can dominate arithmetic. Adding vertices and edges in proportion to P does not guarantee a stable degree distribution, frontier structure, partition cut, or iteration count.

Consequently, alpha and per-processor time are not constant. Partitioning, vertex reordering, hybrid push/pull BFS, communication aggregation, and NUMA-aware placement can help, but graph analytics is less naturally weak-scalable than regular dense numerical kernels.
