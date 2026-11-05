# Task 11 — Gustafson vs. Sun–Ni memory-bounded speedup

Gustafson's fixed-time model assumes the parallel workload can grow with P while elapsed time stays approximately fixed. Its simplified form is `S_G(P)=alpha+(1-alpha)P`. It is a good model when the workload is chosen to use the available compute capacity and memory is sufficient.

Sun and Ni's memory-bounded speedup model adds the system's memory capacity and the relationship between memory size and solvable problem size. Their 1993 paper studies fixed-size, fixed-time, and memory-bounded speedup; in its simplified treatment, Amdahl's fixed-size and Gustafson's fixed-time models appear as special cases of the broader memory-bounded framework. More detailed formulations also account for uneven workload allocation and communication overhead.

Gustafson may **overestimate** throughput when memory per processor is insufficient to hold the enlarged problem, when memory bandwidth saturates, or when communication and synchronization rise with P. It may **underestimate** throughput when additional aggregate memory enables a problem to grow faster than the linear fixed-time assumption, or when data reuse/cache effects improve as the problem is restructured. The direction depends on the workload's memory-growth function and architecture; it is not a universal inequality.

A useful conceptual distinction is: compute-bounded scaling asks how much work can be completed in fixed time; memory-bounded scaling asks how the solvable work changes as aggregate memory capacity changes. Exact Sun–Ni equations depend on their model's memory/workload assumptions, so the simplified Gustafson equation should not be presented as a substitute for the full model.

**Reference:** X.-H. Sun and L. M. Ni, “Scalable Problems and Memory-Bounded Speedup,” *Journal of Parallel and Distributed Computing*, 19(1), 27–37 (1993), DOI: 10.1006/jpdc.1993.1087. https://www.sciencedirect.com/science/article/pii/S0743731583710877
