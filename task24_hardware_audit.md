# Task 24 — Hardware audit and empirical interpretation

This file must be completed on the machine where Task 22 is executed. Do not substitute guessed specifications.

Record:
- CPU model and stepping: `lscpu` (Linux) or system information.
- Physical cores, logical threads, sockets, NUMA nodes: `lscpu`, `numactl --hardware`.
- Cache hierarchy: `lscpu -C` or `getconf -a`; record L1d/L1i/L2/L3 sizes and sharing.
- Memory channels and supported/active speed: vendor/platform documentation or firmware tools; software may not expose the exact active channel count.
- Compiler/runtime and OS version.
- Power governor, turbo state, and thermal conditions if available.

## Interpretation checklist
Compare measured runtime against ideal weak scaling. Increasing time can indicate memory-bandwidth saturation, cache-capacity effects, NUMA-remote accesses, synchronization, scheduler oversubscription, or thermal/power throttling. A sudden step near a thread-count boundary may indicate socket/NUMA placement. Repeat runs, report mean and standard deviation, pin threads where possible, and avoid mixing background load with benchmark execution.

The included scripts produce measurements and plots but cannot identify all hardware properties reliably. Fill this report with actual host output after running the benchmark.
