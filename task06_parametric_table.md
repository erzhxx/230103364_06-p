# Task 06 — Parametric speedup (alpha = 0.04)

Use `S(P)=P-0.04(P-1)=0.96P+0.04` and `E(P)=S(P)/P=0.96+0.04/P`.

| P | S(P) | E(P) |
|---:|---:|---:|
| 16 | 15.4000 | 96.250000% |
| 64 | 61.4800 | 96.062500% |
| 256 | 245.8000 | 96.015625% |
| 1,024 | 983.0800 | 96.003906% |
| 4,096 | 3,932.2000 | 96.000977% |
| 16,384 | 15,728.6800 | 96.000244% |


Efficiency decreases monotonically from 96.25% at 16 processors toward 96% as P grows. The absolute loss is small because alpha is only 4%; the limiting efficiency is `1-alpha=96%`. Speedup itself continues to grow approximately linearly.
