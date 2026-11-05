# Task 02 — First-principles derivation of scaled speedup

Normalize observed parallel runtime to one:
`T_P = s + p = 1`, where `s` is serial elapsed-time fraction and `p` is parallel elapsed-time fraction. Therefore `p=1-s`.

On P processors, the parallel portion represents work performed concurrently. A hypothetical single processor would execute that same parallel work P times serially, while the serial portion is unchanged. Equivalent serial runtime is therefore
`T_1,eq = s + Pp`.

Scaled speedup compares the equivalent serial runtime with the actual parallel runtime:
`S(P) = T_1,eq / T_P = (s+Pp)/(s+p)`.
Since `s+p=1`, this becomes `S(P)=s+Pp`.
Substitute `p=1-s`:
`S(P)=s+P(1-s)=P-s(P-1)`.

The task sheet denotes the serial fraction observed on the parallel machine by `alpha`. Setting `s=alpha` gives
`S(P)=P-alpha(P-1)=alpha+(1-alpha)P`.
The result is linear in P for fixed alpha. At P=1 it equals one; for alpha=0 it equals P; for alpha=1 it equals one.
