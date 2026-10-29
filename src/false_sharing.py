#!/usr/bin/env python3
"""Milestone 2 - false sharing reproduction, remediation and Karp-Flatt diagnosis.

Variants
  unpadded    : worker p increments shared[p]      (8 counters share ONE 64-byte line)
  padded      : worker p increments shared[p * 8]  (each counter on its own 64-byte line)
  privatized  : worker p counts in a local variable, ONE locked write at the end

Implementation notes
  * mp.Array(..., lock=False) (== RawArray) is used: with the default lock=True every
    `arr[i] += 1` would take a mutex and lock contention, not cache coherence, would dominate.
  * The array start is not guaranteed 64-byte aligned, so we compute the first
    64-byte-aligned element index (`base`) and index relative to it. This makes
    "indices 0..7 = one cache line" literally true.
  * A Barrier releases all workers together; the parent starts the clock when the
    barrier opens, so process start-up cost is excluded.

Karp-Flatt:  e(P) = (1/S_P - 1/P) / (1 - 1/P)
  Here EVERY worker does K increments, so total work grows with P and the serial
  reference for the same work is P*T_1. Two columns are reported:
   e_handout       : literal handout formula  (P*T_P/T_1 - 1)/(P-1)   (ideal scaling -> 1.0)
   e_work_adjusted : same formula with S_P = P*T_1/T_P               (ideal scaling -> 0.0)
"""
import argparse
import ctypes
import multiprocessing as mp
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
K = 5_000_000
PS = [1, 2, 4, 8]
LINE_INTS = 8                 # 64 B / 8 B
VARIANTS = ["unpadded", "padded", "privatized"]


def aligned_base(arr):
    off = (-ctypes.addressof(arr)) % 64
    return off // 8 if off % 8 == 0 else 0


def worker_unpadded(arr, base, wid, iters, barrier, lock):
    idx = base + wid
    barrier.wait()
    for _ in range(iters):
        arr[idx] += 1


def worker_padded(arr, base, wid, iters, barrier, lock):
    idx = base + wid * LINE_INTS
    barrier.wait()
    for _ in range(iters):
        arr[idx] += 1


def worker_privatized(arr, base, wid, iters, barrier, lock):
    local = 0
    barrier.wait()
    for _ in range(iters):
        local += 1
    with lock:                                   # single synchronized write
        arr[base + wid * LINE_INTS] = local


WORKERS = {"unpadded": worker_unpadded, "padded": worker_padded, "privatized": worker_privatized}


def slot(variant, base, w):
    return base + (w if variant == "unpadded" else w * LINE_INTS)


def run_once(ctx, variant, P, iters):
    arr = ctx.Array(ctypes.c_int64, 8 * LINE_INTS + 2 * LINE_INTS, lock=False)
    base = aligned_base(arr)
    barrier, lock = ctx.Barrier(P + 1), ctx.Lock()
    procs = [ctx.Process(target=WORKERS[variant], args=(arr, base, w, iters, barrier, lock))
             for w in range(P)]
    for p in procs:
        p.start()
    barrier.wait()
    t0 = time.perf_counter_ns()
    for p in procs:
        p.join()
    t1 = time.perf_counter_ns()
    total = sum(arr[slot(variant, base, w)] for w in range(P))
    return (t1 - t0) / 1e9, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--iters", type=int, default=K)
    a = ap.parse_args()
    ctx = mp.get_context("fork" if "fork" in mp.get_all_start_methods() else "spawn")
    try:
        ncpu = len(__import__("os").sched_getaffinity(0))
    except AttributeError:
        ncpu = mp.cpu_count()
    print(f"usable CPUs: {ncpu}  (P > CPUs means oversubscription, no true parallelism)")

    res = {}
    for variant in VARIANTS:
        for P in PS:
            times, sums = [], []
            for _ in range(a.reps):
                t, s = run_once(ctx, variant, P, a.iters)
                times.append(t)
                sums.append(s)
            res[(variant, P)] = (times, sums)
            print(f"{variant:11s} P={P}  median {statistics.median(times):.3f}s  sum={sums[-1]}", flush=True)

    cols = ["variant", "P", "K", "run_times_s", "median_time_s", "speedup_T1_over_TP",
            "scaled_speedup", "e_handout", "e_work_adjusted", "final_sum", "expected_sum", "sum_ok"]
    lines = ["\t".join(cols)]
    for variant in VARIANTS:
        T1 = statistics.median(res[(variant, 1)][0])
        for P in PS:
            times, sums = res[(variant, P)]
            TP = statistics.median(times)
            exp = P * a.iters
            ok = all(s == exp for s in sums)
            if P == 1:
                e1 = e2 = "NA"
            else:
                e1 = f"{(P * TP / T1 - 1) / (P - 1):.4f}"
                e2 = f"{(TP / T1 - 1) / (P - 1):.4f}"
            lines.append("\t".join(map(str, [
                variant, P, a.iters, ",".join(f"{t:.4f}" for t in times), f"{TP:.4f}",
                f"{T1 / TP:.4f}", f"{P * T1 / TP:.4f}", e1, e2, sums[-1], exp, ok])))
    out = ROOT / "results/false_sharing_karp_flatt.tsv"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
