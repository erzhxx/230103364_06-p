#!/usr/bin/env python3
"""Milestone 3 - strong/weak scaling of a 5-point Jacobi stencil + Roofline positioning.

Kernel  : dst[i,j] = 0.25*(src[i-1,j] + src[i+1,j] + src[i,j-1] + src[i,j+1]),  `iters` sweeps,
          Jacobi ping-pong between two shared grids, fixed boundary.
Decomp  : 1-D row strips, one worker process per strip, shared grids (mp.RawArray),
          a Barrier between sweeps. Each cell is computed by the same ops regardless of P,
          so the final grid is bit-identical to the serial reference -> exact checksum match.
Blocking: strips are processed 8 rows at a time so the temporaries stay in L1/L2
          (otherwise NumPy's 4 passes would multiply DRAM traffic and invalidate the AI estimate).
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import statistics
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from salt import get_student_params  # noqa: E402

BLOCK = 8
FLOPS_PER_POINT = 4          # 3 adds + 1 multiply


# ------------------------------------------------------------------ kernel
def sweep(src, dst, r0, r1, tmp):
    for b0 in range(r0, r1, BLOCK):
        b1 = min(b0 + BLOCK, r1)
        t = tmp[: b1 - b0]
        np.add(src[b0 - 1:b1 - 1, 1:-1], src[b0 + 1:b1 + 1, 1:-1], out=t)
        np.add(t, src[b0:b1, 0:-2], out=t)
        np.add(t, src[b0:b1, 2:], out=t)
        np.multiply(t, 0.25, out=dst[b0:b1, 1:-1])


def partition(n, P):
    base, rem = divmod(n - 2, P)
    out, r = [], 1
    for p in range(P):
        c = base + (1 if p < rem else 0)
        out.append((r, r + c))
        r += c
    return out


def worker(rawa, rawb, n, r0, r1, iters, start_barrier, sync_barrier):
    A = np.frombuffer(rawa, dtype=np.float64).reshape(n, n)
    B = np.frombuffer(rawb, dtype=np.float64).reshape(n, n)
    tmp = np.empty((BLOCK, n - 2))
    src, dst = A, B
    start_barrier.wait()
    for _ in range(iters):
        sweep(src, dst, r0, r1, tmp)
        sync_barrier.wait()
        src, dst = dst, src


def make_init(n, seed):
    return np.random.default_rng(seed).random((n, n))


def checksum_of(grid):
    return float(np.sum(grid, dtype=np.float64)).hex()


def reference_checksum(n, iters, seed):
    """Single-threaded, in-process reference."""
    A, B = make_init(n, seed), make_init(n, seed)
    tmp = np.empty((BLOCK, n - 2))
    src, dst = A, B
    for _ in range(iters):
        sweep(src, dst, 1, n - 1, tmp)
        src, dst = dst, src
    return checksum_of(src)


def run_config(ctx, n, P, iters, seed, reps):
    rawa, rawb = ctx.RawArray("d", n * n), ctx.RawArray("d", n * n)
    A = np.frombuffer(rawa, dtype=np.float64).reshape(n, n)
    B = np.frombuffer(rawb, dtype=np.float64).reshape(n, n)
    init = make_init(n, seed)
    times, sums = [], []
    for _ in range(reps):
        A[:] = init
        B[:] = init
        sb, yb = ctx.Barrier(P + 1), ctx.Barrier(P)
        procs = [ctx.Process(target=worker, args=(rawa, rawb, n, r0, r1, iters, sb, yb))
                 for r0, r1 in partition(n, P)]
        for p in procs:
            p.start()
        sb.wait()
        t0 = time.perf_counter_ns()
        for p in procs:
            p.join()
        t1 = time.perf_counter_ns()
        times.append((t1 - t0) / 1e9)
        sums.append(checksum_of(A if iters % 2 == 0 else B))
    del A, B, init
    return times, sums


# ------------------------------------------------------------------ models
def p_list(maxp):
    ps, p = [], 1
    while p <= maxp:
        ps.append(p)
        p *= 2
    if ps[-1] != maxp:
        ps.append(maxp)
    return ps


def amdahl_fit(Ps, Ss):
    """Least squares for 1/S = 1/P + s(1-1/P)  (linear in s)."""
    num = sum((1 / S - 1 / P) * (1 - 1 / P) for P, S in zip(Ps, Ss) if P > 1)
    den = sum((1 - 1 / P) ** 2 for P in Ps if P > 1)
    return max(0.0, num / den) if den else None


def gustafson_fit(Ps, Ss):
    """Least squares for S = P - a(P-1)."""
    num = sum((P - S) * (P - 1) for P, S in zip(Ps, Ss) if P > 1)
    den = sum((P - 1) ** 2 for P in Ps if P > 1)
    return num / den if den else None


# ------------------------------------------------------------------ roofline
def _bw_worker(m, barrier, out, idx):
    a, b = np.ones(m), np.ones(m)
    np.multiply(b, 3.0, out=a)
    barrier.wait()
    best = 1e9
    for _ in range(5):
        t0 = time.perf_counter()
        np.multiply(b, 3.0, out=a)
        best = min(best, time.perf_counter() - t0)
    out[idx] = best


def measure_bandwidth(ctx, P, l3_bytes):
    per_array = int(min(max((l3_bytes or 0) / P, 32 * 2**20), 128 * 2**20))
    m = per_array // 8
    out = ctx.RawArray("d", P)
    barrier = ctx.Barrier(P)
    procs = [ctx.Process(target=_bw_worker, args=(m, barrier, out, i)) for i in range(P)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    worst = max(out[:])
    return P * 16 * m / worst / 1e9   # STREAM-scale: 8 B read + 8 B write per element (no write-allocate)


def roofline(prof, N, iters, P_max, t_strong_pmax, args, ctx):
    cpu, cache = prof["cpu"], prof["cache"]
    flags = set(cpu.get("simd_flags", []))
    flops_cycle = 32 if "avx512f" in flags else 16 if ("avx2" in flags and "fma" in flags) \
        else 8 if "avx" in flags else 4
    ghz = cpu.get("base_freq_ghz") or 2.0
    peak_gflops = args.peak_gflops or P_max * ghz * flops_cycle
    bw_meas = measure_bandwidth(ctx, P_max, cache.get("l3_shared_bytes"))
    peak_bw = args.peak_bw_gbs or bw_meas
    bw_src = "user-supplied theoretical peak" if args.peak_bw_gbs else \
        "measured STREAM-scale bandwidth (proxy for peak; DRAM spec not readable from OS)"
    ai_ideal = FLOPS_PER_POINT / 16          # read 8 B + write 8 B per point, perfect neighbour reuse
    ai_wa = FLOPS_PER_POINT / 24             # + 8 B write-allocate fill
    ws = 2 * N * N * 8
    levels = [("L1d", cache["l1d_bytes"]), ("L2", cache["l2_bytes"]), ("L3", cache["l3_shared_bytes"])]
    fits = next((nm for nm, sz in levels if sz and ws <= sz), "DRAM")
    ridge = peak_gflops / peak_bw
    attain = min(peak_gflops, ai_ideal * peak_bw)
    measured = FLOPS_PER_POINT * (N - 2) ** 2 * iters / t_strong_pmax / 1e9
    regime = "Memory-Bandwidth Bound" if ai_ideal < ridge else "Compute Bound"
    return {
        "kernel": "5-point Jacobi stencil, float64",
        "flops_per_point": FLOPS_PER_POINT,
        "dram_bytes_per_point_ideal": 16, "dram_bytes_per_point_with_write_allocate": 24,
        "arithmetic_intensity_flop_per_byte": ai_ideal,
        "arithmetic_intensity_with_write_allocate": ai_wa,
        "grid_N": N, "working_set_bytes_two_grids": ws,
        "cache_bytes": {k: v for k, v in levels}, "working_set_fits_in": fits,
        "P_max": P_max, "peak_gflops": peak_gflops,
        "peak_gflops_assumption": f"{P_max} cores x {ghz} GHz x {flops_cycle} DP FLOP/cycle",
        "peak_bandwidth_gbs": peak_bw, "peak_bandwidth_source": bw_src,
        "measured_stream_bandwidth_gbs": bw_meas,
        "ridge_point_flop_per_byte": ridge,
        "attainable_gflops_roofline": attain,
        "measured_gflops_at_Pmax": measured,
        "fraction_of_roofline": measured / attain if attain else None,
        "regime": regime,
        "conclusion": (f"AI={ai_ideal:.3f} FLOP/B is far below the ridge point {ridge:.1f} FLOP/B -> {regime}. "
                       f"Working set ({ws / 2**20:.1f} MiB) fits in {fits}; "
                       + ("it therefore streams from DRAM every sweep." if fits == "DRAM" else
                          f"traffic is served by {fits} bandwidth, not DRAM, so measured performance may "
                          f"exceed the DRAM roofline.")),
    }


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student-id")
    ap.add_argument("--iters", type=int, default=100)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--max-p", type=int, help="override max worker count")
    ap.add_argument("--peak-bw-gbs", type=float, help="theoretical DRAM peak (GB/s) from CPU/DIMM spec")
    ap.add_argument("--peak-gflops", type=float)
    a = ap.parse_args()

    prm = get_student_params(a.student_id) if a.student_id else json.loads((ROOT / "results/salted_params.json").read_text())
    prof = json.loads((ROOT / "results/host_profile.json").read_text())
    N, seed = prm["N"], prm["seed"]
    try:
        usable = len(os.sched_getaffinity(0))
    except AttributeError:
        usable = os.cpu_count()
    maxp = a.max_p or max(1, min(prof["cpu"]["physical_cores"] or usable, usable))
    Ps = p_list(maxp)
    ctx = mp.get_context("fork" if "fork" in mp.get_all_start_methods() else "spawn")
    print(f"N={N} iters={a.iters} P in {Ps}")

    ref = {}
    rows = []
    strong = {}
    ref[N] = reference_checksum(N, a.iters, seed)
    for P in Ps:
        times, sums = run_config(ctx, N, P, a.iters, seed, a.reps)
        strong[P] = statistics.median(times)
        rows.append(dict(study="strong", P=P, N=N, work_points=(N - 2) ** 2, time_s=strong[P],
                         checksum=sums[-1], checksum_ref=ref[N], checksum_ok=all(s == ref[N] for s in sums)))
        print(f"strong P={P}: {strong[P]:.4f}s", flush=True)
    T1 = strong[1]
    S = {P: T1 / strong[P] for P in Ps}
    s_fit = amdahl_fit(Ps, [S[P] for P in Ps])
    for r in rows:
        P = r["P"]
        r["speedup"] = S[P]
        r["efficiency_pct"] = 100 * S[P] / P
        r["serial_fraction_point"] = (1 / S[P] - 1 / P) / (1 - 1 / P) if P > 1 else ""
        r["amdahl_s_fit"] = s_fit
        r["S_max"] = "NA" if s_fit is None else ("inf" if s_fit == 0 else 1 / s_fit)
        if s_fit is None:
            r["amdahl_s_fit"] = "NA"

    weak = {1: T1}
    weak_rows = []
    for P in Ps:
        nP = math.ceil(N * math.sqrt(P))
        if P == 1:
            times, sums, ref[nP] = None, None, ref[N]
            t = T1
            ck = ref[N]
            ok = True
            ckk = ck
        else:
            ref[nP] = reference_checksum(nP, a.iters, seed)
            times, sums = run_config(ctx, nP, P, a.iters, seed, a.reps)
            t = statistics.median(times)
            ok = all(s == ref[nP] for s in sums)
            ckk = sums[-1]
        weak[P] = t
        w1, wP = (N - 2) ** 2, (nP - 2) ** 2
        scaled = P * w1 * T1 / (wP * t)
        weak_rows.append(dict(study="weak", P=P, N=nP, work_points=wP, time_s=t, speedup="",
                              efficiency_pct=100 * scaled / P, serial_fraction_point="",
                              checksum=ckk, checksum_ref=ref[nP], checksum_ok=ok,
                              scaled_speedup=scaled, throughput_Mpts_per_s=wP * a.iters / t / 1e6))
        print(f"weak   P={P}: N_P={nP} {t:.4f}s  scaled speedup {scaled:.2f}", flush=True)
    g_fit = gustafson_fit(Ps, [r["scaled_speedup"] for r in weak_rows])
    for r in weak_rows:
        r["gustafson_alpha_fit"] = "NA" if g_fit is None else g_fit
    for r in rows:
        r.setdefault("scaled_speedup", ""); r.setdefault("throughput_Mpts_per_s", a.iters * r["work_points"] / r["time_s"] / 1e6)
        r["gustafson_alpha_fit"] = ""
    rows += weak_rows

    cols = ["study", "P", "N", "iters", "work_points", "time_s", "speedup", "efficiency_pct",
            "scaled_speedup", "throughput_Mpts_per_s", "serial_fraction_point", "amdahl_s_fit",
            "S_max", "gustafson_alpha_fit", "checksum", "checksum_ref", "checksum_ok"]
    fmt = lambda v: f"{v:.6g}" if isinstance(v, float) else str(v)
    with open(ROOT / "results/scaling_metrics.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            r["iters"] = a.iters
            f.write("\t".join(fmt(r.get(c, "")) for c in cols) + "\n")

    rf = roofline(prof, N, a.iters, maxp, strong[maxp], a, ctx)
    (ROOT / "results/roofline_summary.json").write_text(json.dumps(rf, indent=2))
    if s_fit is None:
        print("\nOnly P=1 available (1 usable core): Amdahl/Gustafson fits need P>=2 -> NA")
    else:
        print(f"\nAmdahl fit: s = {s_fit:.4f}  ->  S_max = {(1 / s_fit) if s_fit else float('inf'):.2f}")
        print(f"Gustafson fit: alpha = {g_fit:.4f}")
    print(f"Roofline: AI={rf['arithmetic_intensity_flop_per_byte']:.3f}  ridge={rf['ridge_point_flop_per_byte']:.2f}  -> {rf['regime']}")
    print(rf["conclusion"])


if __name__ == "__main__":
    main()
