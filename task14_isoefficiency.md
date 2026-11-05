# Task 14 — Isoefficiency under Gustafson scaling

Isoefficiency asks how total problem size W must grow with P to keep parallel efficiency fixed in the presence of overhead. In a Gustafson-compliant ideal weak-scaling program, each processor receives a fixed local workload `w0`; hence `W(P)=P*w0`.

If the measured serial/overhead fraction alpha remains constant, `E_G(P)=1-alpha+alpha/P`, so efficiency approaches `1-alpha` and is bounded away from zero. No superlinear growth beyond W proportional to P is required in this idealized model: the weak-scaling workload itself is linear in P.

This is not a general isoefficiency theorem for arbitrary algorithms. In standard overhead analysis, efficiency `E = 1/[1+T_o/(W)]` (up to model conventions); keeping E constant requires W to grow at least proportionally to overhead `T_o(P)`. If communication overhead is `O(P log P)` or synchronization overhead grows faster than P, the required isoefficiency function is correspondingly superlinear. Thus the Gustafson-compliant case has `W(P)=Theta(P)` only under bounded per-processor overhead and constant alpha.
