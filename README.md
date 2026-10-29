# Parallel Computing Practice Lab — Karp–Flatt

## Requirements
- Python 3.8 or newer (Python 3.11 is suitable)
- No third-party packages required

## Run on Windows
Open Command Prompt or PowerShell in this folder and run each command:

    python exp_a_serial.py
    python exp_b_contention.py
    python exp_c_fixed.py

Each script benchmarks P = 1, 2, 4 and prints runtime, speedup, and Karp–Flatt e(p).

## Important
- Run each experiment separately.
- The contention experiment performs 2,000,000 locked increments and may take a while.
- Results vary by machine and background load. The measured results are recorded in RESULTS.md.
- The handout describes expected diagnostic trends, not guaranteed exact timings.
- Increment counts are divided evenly for P = 1, 2, 4.

## Submission
This work is stored on branch practice-230103364 in the connected GitHub repository.
