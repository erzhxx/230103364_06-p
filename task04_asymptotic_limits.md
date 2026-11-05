# Task 04 — Asymptotic parallel efficiency

Gustafson speedup is `S_G(P)=P-alpha(P-1)=(1-alpha)P+alpha`.
Divide by P:
`E_G(P)=S_G(P)/P=(1-alpha)+alpha/P`.
For fixed `0<=alpha<=1`, `lim(P->infinity) alpha/P=0`, hence
**`lim E_G(P)=1-alpha`**.

For Amdahl, `S_A(P)=1/[alpha+(1-alpha)/P]`. Its efficiency is
`E_A(P)=S_A(P)/P = 1/[alpha P + (1-alpha)]`.
If `alpha>0`, denominator tends to infinity and **`lim E_A(P)=0`**. If alpha=0, efficiency remains one. The distinction is fundamental: Gustafson's scaled workload retains a constant fraction of useful parallel time, while Amdahl's fixed workload spreads a finite amount of parallel work over ever more processors.
