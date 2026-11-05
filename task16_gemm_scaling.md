# Task 16 — Dense matrix multiplication (GEMM)

For square dense GEMM, work is proportional to `N^3`; storage for A, B, and C is proportional to `N^2`. Under ideal weak scaling with fixed work per processor, total operations grow proportional to P:
`N(P)^3 proportional to P`, hence **`N(P)=N(1)*P^(1/3)`**.
The matrix dimension grows with the cube root of processor count, while matrix storage grows as `N^2 proportional to P^(2/3)`. A table of dimension multipliers:

| P relative to 1 | N multiplier |
|---:|---:|
| 8 | 2 |
| 64 | 4 |
| 512 | 8 |
| 4,096 | 16 |
| 32,768 | 32 |

This assumes ideal compute scaling and ignores communication lower bounds, memory capacity, and the redistribution of A/B blocks. Classical 2D block matrix multiplication communicates data even when arithmetic work per processor is held constant.
