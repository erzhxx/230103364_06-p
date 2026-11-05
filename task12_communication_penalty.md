# Task 12 — Gustafson model with communication penalty

Let `alpha0` be non-communication serial fraction and `C(P)>=0` be communication time normalized to the ideal one-unit parallel runtime. A simple additive fixed-time model is
`T_parallel(P)=1+C(P)`, with useful compute-time fractions `alpha0` serial and `1-alpha0` parallel. The equivalent serial work is `alpha0 + P(1-alpha0)`. Define effective scaled speedup against the same one-unit reference as
`S_C(P)=[alpha0+P(1-alpha0)]/[1+C(P)]`.

If communication is a fraction of observed runtime rather than an additive penalty, use `alpha_eff(P)=[alpha0+C(P)]/[1+C(P)]` and
`S_C(P)=P-alpha_eff(P)(P-1)`. These conventions are related but not identical; the first treats C as extra elapsed time, the second folds it into the observed serial/overhead fraction.

Examples:
- `C(P)=c log2(P)` models tree/network diameter or collective costs.
- `C(P)=c sqrt(P)` can approximate surface exchange growth for some decompositions.
For positive c, either penalty eventually prevents ideal linear speedup. In the square-root case the additive model behaves asymptotically like `O(sqrt(P))`; in the logarithmic case it behaves roughly as `O(P/log P)`. The model is intentionally phenomenological: actual communication depends on topology, message size, overlap, bisection bandwidth, and collective algorithm.
