# Results — Karp–Flatt Empirical Scalability Diagnostics

## Hardware profile
- CPU: Intel Core i5-12500H (reported for this machine)
- Logical processors: 16 (reported previously; verify if required)
- OS: Windows
- Python version: add the output of python --version if required by the instructor

## Measured results

All runtime values below were provided from the actual runs.

| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Architectural diagnosis |
|---|---:|---:|---:|---:|---:|---|
| A: Serial Tail | 3.777 | 2.165 | 1.425 | 0.146 | 0.170 | Runtime decreases with more processes; e is in a similar range but not perfectly constant |
| B: Lock Contention | 2.665 | 12.333 | 12.574 | 8.256 | 5.958 | Severe lock contention: multiple processes make the program much slower |
| C: Privatized State | 0.543 | 0.326 | 0.228 | 0.202 | 0.226 | Privatization restores speedup, but scaling is not near-linear |

## Speedup and efficiency

- Speedup: Sp = T1 / Tp
- Karp–Flatt: e(p) = ((p * Tp / T1) - 1) / (p - 1)
- Four-process parallel efficiency: E4 = S4 / 4

| Experiment | S2 | S4 | E4 |
|---|---:|---:|---:|
| A: Serial Tail | 1.74x | 2.65x | 66.3% |
| B: Lock Contention | 0.22x | 0.21x | 5.3% |
| C: Privatized State | 1.66x | 2.38x | 59.5% |

## Conclusions

1. **Experiment A:** Runtime decreases as the number of processes increases. The Karp–Flatt values are in the same general range, although they rise from 0.146 to 0.170 rather than remaining perfectly constant.
2. **Experiment B:** The shared counter is protected by a lock on every increment. The two- and four-process runs are both much slower than the one-process run, showing that synchronization overhead dominates.
3. **Experiment C:** Each process accumulates values locally and the results are combined at the end. This avoids locking on every increment and restores speedup. However, the measured Karp–Flatt values (0.202 and 0.226) are above the expected target of 0.05, and four-process efficiency is about 59.5%, below the 70% target. These are the actual measured values and should be reported honestly.
4. Exact results depend on hardware, Python version, and system load.
