# Task 01 — Strong Scaling vs. Weak Scaling

## Amdahl (1967): fixed-size / strong scaling
Amdahl holds the total problem size (work) fixed. If fraction `s` is serial and `1-s` is perfectly parallel, then
`T_A(P) = sT_1 + (1-s)T_1/P`, hence `S_A(P)=1/[s+(1-s)/P]`.
As `P -> infinity`, the parallel part tends to zero but the serial part remains: `S_A -> 1/s`. The dimension of a fixed `d`-dimensional grid remains constant; only the work distribution changes. For example, an `N^d` grid retains the same `N` as P grows.

## Gustafson (1988): fixed-time / weak scaling
Gustafson holds elapsed parallel runtime approximately constant while increasing the amount of parallel work with processor count. If the measured serial time fraction on P processors is `alpha`, normalized parallel runtime is `alpha + p = 1`; the equivalent serial work is `alpha + Pp`. Thus
`S_G(P)=alpha+P(1-alpha)=P-alpha(P-1)`.
For a regular d-dimensional domain with fixed work per processor, total grid volume grows as P and its linear dimension grows as `N(P) proportional to P^(1/d)`. In particular, a 3D cubic grid has `N proportional to P^(1/3)`.

## Why the names differ
"Fixed-size" asks how much faster the same job finishes. "Fixed-time" asks how much larger a job can be completed in the same time. Amdahl is appropriate when the workload is externally fixed; Gustafson is appropriate when larger machines are used to solve proportionally larger scientific problems. Neither law guarantees ideal scaling: communication, load imbalance, memory bandwidth, synchronization, and algorithmic complexity can change with P.
