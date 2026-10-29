#!/usr/bin/env bash
# One-shot runner: executes every milestone in order, commits and tags each one.
# Usage:  ./run_all.sh <8-digit-student-id>
# Tip: plug in the laptop, close browsers/IDEs, do not touch the machine while it runs.
set -euo pipefail
cd "$(dirname "$0")"
ID="${1:?usage: ./run_all.sh <8-digit student id>}"
PY="${PYTHON:-python3}"
[ -d .git ] || git init -q -b main
git config user.name  >/dev/null 2>&1 || git config user.name  "student"
git config user.email >/dev/null 2>&1 || git config user.email "student@example.com"
$PY -c "import numpy" 2>/dev/null || $PY -m pip install numpy
$PY -c "import numba" 2>/dev/null || $PY -m pip install numba || echo "numba unavailable -> pure-python dense kernel"

checkpoint() { git add . && git commit -q --allow-empty -m "$1" && git tag -f "$2" >/dev/null && echo "== tagged $2"; }

$PY src/profile_env.py --student-id "$ID"
checkpoint "M0: Environment and salting configuration" M0-ENV

$PY src/stride_bench.py
$PY src/dense_kernel.py
checkpoint "M1: Memory stride and loop interchange benchmarking" M1-LOCALITY

$PY src/false_sharing.py
checkpoint "M2: False sharing reproduction and Karp-Flatt analysis" M2-SHARING

$PY src/scaling_study.py        # add --peak-bw-gbs <GB/s> if you know your DRAM peak (e.g. 2ch DDR4-3200 = 51.2)
checkpoint "M3: Strong and weak scaling evaluation" M3-SCALING

$PY verify_outputs.py
checkpoint "M4: Final verification and completed practicum submission" M4-FINAL
echo "Done. Fill in README.md, amend if needed, then: git push origin main --tags"
