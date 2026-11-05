# Task 19 — Monte Carlo weak scaling

Monte Carlo paths are nearly embarrassingly parallel: each path can be simulated independently. With fixed paths per worker, useful work grows approximately linearly with P and the ideal Gustafson speedup is close to P.

Non-zero alpha arises from initialization, random-number generator stream/seed assignment, result aggregation, output formatting, and final serialization. A reduction tree over P workers has `ceil(log2(P))` communication stages. If each stage costs latency L and communicates a fixed-size partial result, reduction time is approximately `L*ceil(log2(P))` (plus bandwidth and local reduction costs). A simple normalized overhead model is `C_red(P)=c log2(P)`; substituting into Task 12 gives
`S(P)=[alpha0+(1-alpha0)P]/[1+c log2(P)]`.
Alternatively, if reduction is folded into the observed serial fraction, use `alpha_eff(P)` and `S=P-alpha_eff(P)(P-1)`.

Counter-based or leapfrog/splittable PRNG streams can reduce seed coordination and avoid correlated streams. Reproducible deterministic reductions may cost more than nondeterministic aggregation. The actual alpha should be measured rather than assumed to be zero.
