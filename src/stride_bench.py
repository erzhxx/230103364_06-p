#!/usr/bin/env python3
"""Milestone 1, Task 1.1 - stride latency cliff.

A literal Python loop `total += data[i]` costs ~50 ns/element of interpreter
overhead, which completely hides the 1-5 ns memory effect we want to see.
We therefore perform the SAME strided read-reduction inside NumPy's C loop
(np.add.reduce over the strided view data[::s]); hardware behaviour
(cache lines, prefetcher, TLB) is identical, interpreter noise is gone.
"""
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STRIDES = [1, 2, 4, 8, 16, 32, 64, 128]
N_ELEM = 16_777_216            # 2^24 float64 = 134 MB
WARMUP, RUNS = 5, 5


def main():
    data = np.ones(N_ELEM, dtype=np.float64)   # allocate + first-touch all pages
    line = 64
    try:
        line = json.loads((ROOT / "results/host_profile.json").read_text())["cache"]["cache_line_bytes"]
    except Exception:
        pass
    rows = []
    for s in STRIDES:
        view = data[::s]
        touched = view.shape[0]

        def run():
            return np.add.reduce(view)

        for _ in range(WARMUP):
            run()
        times = []
        for _ in range(RUNS):
            t0 = time.perf_counter_ns()
            total = run()
            t1 = time.perf_counter_ns()
            if total != touched:
                sys.exit(f"reduction wrong for stride {s}: {total} != {touched}")
            times.append(t1 - t0)
        med = int(statistics.median(times))
        lat = med / touched
        lines = touched if s * 8 >= line else N_ELEM * 8 // line   # cache lines crossing the bus
        rows.append({
            "stride_elems": s, "stride_bytes": s * 8, "elements_touched": touched,
            "median_time_ns": med, "latency_ns_per_element": f"{lat:.4f}",
            "lines_fetched": lines,
            "useful_bytes_per_line_fetched": f"{touched * 8 / lines:.1f}",
            "line_traffic_GBps": f"{lines * line / med:.3f}",
        })
    base = float(rows[0]["latency_ns_per_element"])
    for r in rows:
        r["slowdown_vs_stride1"] = f"{float(r['latency_ns_per_element']) / base:.2f}"
    out = ROOT / "results/stride_results.tsv"
    out.parent.mkdir(exist_ok=True)
    cols = list(rows[0].keys())
    with open(out, "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")
    print("\t".join(cols))
    for r in rows:
        print("\t".join(str(r[c]) for c in cols))
    l1, l8 = float(rows[0]["latency_ns_per_element"]), float(rows[3]["latency_ns_per_element"])
    print(f"\ncache-line cliff: stride-8 is {l8 / l1:.1f}x slower per element than stride-1")


if __name__ == "__main__":
    main()
