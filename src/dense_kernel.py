#!/usr/bin/env python3
"""Milestone 1, Task 1.2 - loop interchange i-j-k vs i-k-j on flat row-major buffers.

Backend: Numba JIT if installed (sub-block M = N/2), otherwise pure Python on
flat lists with a small block (--M, default 128) so it fits the time window.
The SAME function source is used for both backends.
Both loops use the full N-wide leading dimension, so B[k*N+j] really strides by N.
"""
import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from salt import get_student_params  # noqa: E402

try:
    from numba import njit
    HAVE_NUMBA = True
except ImportError:
    HAVE_NUMBA = False


def ijk_py(A, B, C, N, M):
    """Algorithm A: naive. Inner loop strides by N through B."""
    for i in range(M):
        iN = i * N
        for j in range(M):
            acc = 0.0                      # C[i,j] accumulated in a register
            for k in range(M):
                acc += A[iN + k] * B[k * N + j]
            C[iN + j] = acc


def ikj_py(A, B, C, N, M):
    """Algorithm B: interchanged. A[i,k] hoisted; inner loop is stride-1 on B and C."""
    for i in range(M):
        iN = i * N
        for k in range(M):
            a = A[iN + k]
            kN = k * N
            for j in range(M):
                C[iN + j] += a * B[kN + j]


def load_params(args):
    p = ROOT / "results/salted_params.json"
    if args.student_id:
        return get_student_params(args.student_id)
    if p.exists():
        return json.loads(p.read_text())
    sys.exit("need --student-id or results/salted_params.json")


def timed(fn, A, B, C, N, M):
    t0 = time.perf_counter()
    fn(A, B, C, N, M)
    return time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student-id")
    ap.add_argument("--M", type=int, help="sub-block size (default N/2 with numba, 128 pure python)")
    ap.add_argument("--force-python", action="store_true")
    ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()

    prm = load_params(a)
    N, seed = prm["N"], prm["seed"]
    use_nb = HAVE_NUMBA and not a.force_python
    M = a.M or (N // 2 if use_nb else 128)
    rng = np.random.default_rng(seed)
    A_np = rng.random(N * N)
    B_np = rng.random(N * N)

    if use_nb:
        f_ijk, f_ikj = njit(ijk_py), njit(ikj_py)
        A, B = A_np, B_np
        new_c = lambda: np.zeros(N * N)
        w = np.zeros(16 * 16)
        f_ijk(A, B, w, 16, 8)      # JIT warm-up (excluded from timing)
        f_ikj(A, B, w, 16, 8)
        to_np = lambda C: np.asarray(C).reshape(N, N)[:M, :M]
        backend = f"numba {__import__('numba').__version__}"
    else:
        f_ijk, f_ikj = ijk_py, ikj_py
        A, B = A_np.tolist(), B_np.tolist()
        new_c = lambda: [0.0] * (N * N)
        to_np = lambda C: np.array(C).reshape(N, N)[:M, :M]
        backend = "pure-python"

    t_ijk, t_ikj = [], []
    for r in range(a.runs):
        C1 = new_c()
        t_ijk.append(timed(f_ijk, A, B, C1, N, M))
        C2 = new_c()
        t_ikj.append(timed(f_ikj, A, B, C2, N, M))
        print(f"run {r}: i-j-k {t_ijk[-1]:.4f}s   i-k-j {t_ikj[-1]:.4f}s", flush=True)
    S1, S2 = to_np(C1), to_np(C2)
    diff = float(np.max(np.abs(S1 - S2)))
    digest = hashlib.sha256(np.round(S1, 6).tobytes()).hexdigest()
    med_n, med_i = statistics.median(t_ijk), statistics.median(t_ikj)
    res = {
        "student_id": prm["student_id"], "N": N, "M": M, "seed": seed, "backend": backend,
        "runs": a.runs, "times_ijk_s": t_ijk, "times_ikj_s": t_ikj,
        "median_ijk_s": med_n, "median_ikj_s": med_i,
        "speedup": med_n / med_i,
        "max_abs_diff": diff, "epsilon": 1e-12, "diff_within_epsilon": diff <= 1e-12,
        "digest_sha256_round6": digest,
        "note": "C[i,j] kept in a register in i-j-k so the comparison isolates memory locality",
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/loop_interchange.json").write_text(json.dumps(res, indent=2))
    print(f"\nN={N} M={M} [{backend}]  speedup S = {res['speedup']:.2f}x   max|diff| = {diff:.2e}")


if __name__ == "__main__":
    main()
