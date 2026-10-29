#!/usr/bin/env python3
"""Milestone 4 - automated numerical verification (stand-in for the course-provided script).

Run from repo root:  python3 src/verify_outputs.py     (or python3 verify_outputs.py via the wrapper)
Checks M0..M3 and writes results/verification_receipt.sig (HMAC-SHA256 keyed by the student ID
over the SHA-256 of every result file).
"""
import csv
import hashlib
import hmac
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from salt import get_student_params  # noqa: E402
import dense_kernel as dk            # noqa: E402
import scaling_study as ss           # noqa: E402

R = ROOT / "results"
fails = []


def report(ok, msg):
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    if not ok:
        fails.append(msg)


def tsv(name):
    with open(R / name) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main():
    # ---- M0
    sp = json.loads((R / "salted_params.json").read_text())
    hp = json.loads((R / "host_profile.json").read_text())
    exp = get_student_params(sp["student_id"])
    ok = (exp == sp and 1024 <= sp["N"] <= 1536 and sp["N"] % 64 == 0
          and hp["cache"]["cache_line_bytes"] and hp["cpu"]["physical_cores"] and hp["cpu"]["logical_threads"])
    report(ok, "Milestone 0: Host topology and salted parameters validated.")

    # ---- M1: recompute a small instance + check stored result
    li = json.loads((R / "loop_interchange.json").read_text())
    n, m = 64, 48
    rng = np.random.default_rng(sp["seed"])
    A, B = rng.random(n * n), rng.random(n * n)
    C1, C2 = np.zeros(n * n), np.zeros(n * n)
    dk.ijk_py(A, B, C1, n, m)
    dk.ikj_py(A, B, C2, n, m)
    d12 = float(np.max(np.abs(C1 - C2)))
    ref = (A.reshape(n, n)[:m, :m] @ B.reshape(n, n)[:m, :m])
    dref = float(np.max(np.abs(C1.reshape(n, n)[:m, :m] - ref)))
    digest = hashlib.sha256(np.round(C1.reshape(n, n)[:m, :m], 6).tobytes()).hexdigest()
    ok = d12 <= 1e-12 and dref <= 1e-9 and li["max_abs_diff"] <= 1e-12 and li["N"] == sp["N"]
    report(ok, f"Milestone 1: Matrix numerical digest matches reference: {digest[:8]}... "
               f"(ikj-ijk={d12:.1e}, stored={li['max_abs_diff']:.1e}, vs numpy={dref:.1e})")

    # ---- M2
    rows = tsv("false_sharing_karp_flatt.tsv")
    ok = all(int(r["final_sum"]) == int(r["P"]) * int(r["K"]) == int(r["expected_sum"]) for r in rows)
    last = rows[-1]
    report(ok, f"Milestone 2: Reduction sum exact match ({len(rows)} runs): "
               f"{last['final_sum']} == {int(last['P']) * int(last['K'])}.")

    # ---- M3: recompute serial reference for salted N and compare with every strong row
    rows = tsv("scaling_metrics.tsv")
    iters = int(rows[0]["iters"])
    ref = ss.reference_checksum(sp["N"], iters, sp["seed"])
    strong = [r for r in rows if r["study"] == "strong"]
    ok = all(r["checksum_ok"] == "True" for r in rows) and all(r["checksum"] == ref for r in strong)
    report(ok, "Milestone 3: Stencil numerical tolerance verified (bitwise equal to serial reference).")

    if fails:
        print(f"\n{len(fails)} check(s) failed - no receipt written.")
        sys.exit(1)

    files = ["host_profile.json", "salted_params.json", "stride_results.tsv", "loop_interchange.json",
             "false_sharing_karp_flatt.tsv", "scaling_metrics.tsv", "roofline_summary.json"]
    payload = "\n".join(f"{f}:{hashlib.sha256((R / f).read_bytes()).hexdigest()}" for f in files)
    sig = hmac.new(sp["student_id"].encode(), payload.encode(), hashlib.sha256).hexdigest()
    (R / "verification_receipt.sig").write_text(sig + "\n")
    print("All empirical datasets verified successfully. Emitting verification_receipt.sig.")


if __name__ == "__main__":
    main()
