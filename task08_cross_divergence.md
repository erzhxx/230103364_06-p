# Task 08 — Amdahl vs. Gustafson at P=128

Given `s=alpha=0.08`, `P=128`:

Amdahl:
`S_A=1/[0.08+0.92/128]=1/0.0871875=11.469534...`.

Gustafson:
`S_G=128-0.08(127)=117.84`.

Absolute difference: `117.84-11.469534=106.370466`.
Using Amdahl as the percentage-discrepancy baseline:
`(S_G-S_A)/S_A*100 = 927.18%` (approximately).
Ratio: `S_G/S_A = 10.274...`.

They diverge because Amdahl fixes the total workload and divides its parallel portion among more processors. Gustafson scales the parallel work to use the available processors while retaining approximately the same elapsed time. The two predictions answer different questions, so the discrepancy is not a numerical inconsistency.
