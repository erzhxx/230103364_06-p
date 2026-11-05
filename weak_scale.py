#!/usr/bin/env python3
"""Weak-scaling CPU benchmark using Python multiprocessing."""
import argparse, csv, math, os, statistics, time
from concurrent.futures import ProcessPoolExecutor

def work(args):
    n, seed = args
    # Deterministic floating-point workload; each worker gets the same amount.
    x = (seed % 997 + 1) / 997.0
    acc = 0.0
    for i in range(1, n + 1):
        x = (x * 1.000000119 + (i % 97) * 1e-9) % 1.0
        acc += math.sqrt(x + 1e-12)
    return acc

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--work-per-thread",type=int,default=500000)
    ap.add_argument("--runs",type=int,default=5)
    ap.add_argument("--max-workers",type=int,default=os.cpu_count() or 1)
    ap.add_argument("--output",default="benchmarks/results.csv")
    a=ap.parse_args()
    counts=sorted(set([1,2,4,8, max(1,a.max_workers)]))
    counts=[p for p in counts if p<=a.max_workers]
    out=a.output
    os.makedirs(os.path.dirname(out) or ".",exist_ok=True)
    with open(out,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["threads","run","runtime_seconds","checksum","work_per_thread"])
        for p in counts:
            for r in range(1,a.runs+1):
                start=time.perf_counter()
                with ProcessPoolExecutor(max_workers=p) as ex:
                    results=list(ex.map(work,[(a.work_per_thread,i+1) for i in range(p)]))
                elapsed=time.perf_counter()-start
                w.writerow([p,r,f"{elapsed:.9f}",f"{sum(results):.12g}",a.work_per_thread])
                print(f"threads={p:>3} run={r} time={elapsed:.4f}s")
    print(f"Results saved to {out}")

if __name__=="__main__": main()
