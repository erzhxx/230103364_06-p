#!/usr/bin/env python3
"""Fit observed alpha from weak-scaling benchmark CSV."""
import argparse, csv, json, math
from collections import defaultdict
from pathlib import Path
import statistics

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="benchmarks/results.csv")
    ap.add_argument("--output",default="benchmarks/fit.json")
    ap.add_argument("--plot",default="plots/empirical_fit.png")
    a=ap.parse_args()
    groups=defaultdict(list)
    with open(a.input,newline="") as f:
        for row in csv.DictReader(f):
            groups[int(row["threads"])].append(float(row["runtime_seconds"]))
    if len(groups)<2: raise SystemExit("Need at least two thread-count configurations.")
    ps=sorted(groups)
    means=[statistics.mean(groups[p]) for p in ps]
    sds=[statistics.stdev(groups[p]) if len(groups[p])>1 else 0.0 for p in ps]
    # Gustafson: S(P)=P-alpha(P-1). Use empirical speedup T(1)/T(P).
    t1=means[0]
    observed=[t1/t for t in means]
    xs=[p-1 for p in ps]
    ys=[p-s for p,s in zip(ps,observed)]
    denom=sum(x*x for x in xs)
    alpha=sum(x*y for x,y in zip(xs,ys))/denom if denom else 0.0
    alpha=max(0.0,min(1.0,alpha))
    result={"alpha_fitted":alpha,"thread_counts":ps,"mean_runtime_seconds":means,
            "runtime_stddev_seconds":sds,"empirical_speedup_vs_1_thread":observed,
            "note":"Least-squares fit constrained to Gustafson form; interpret cautiously if runtimes are noisy."}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    with open(a.output,"w") as f: json.dump(result,f,indent=2)
    try:
        import matplotlib.pyplot as plt
        plt.errorbar(ps,observed,yerr=[(t1*sd/(m*m)) if m else 0 for sd,m in zip(sds,means)],
                     fmt="o",label="Measured")
        plt.plot(ps,[p-alpha*(p-1) for p in ps],label=f"Gustafson fit (alpha={alpha:.4f})")
        plt.plot(ps,[1/(alpha+(1-alpha)/p) for p in ps],label="Amdahl reference")
        plt.plot(ps,ps,"--",label="Ideal linear")
        plt.xlabel("Threads"); plt.ylabel("Speedup vs. one worker")
        plt.title("Empirical and theoretical scaling"); plt.grid(True,alpha=.25); plt.legend(); plt.tight_layout()
        Path(a.plot).parent.mkdir(parents=True,exist_ok=True); plt.savefig(a.plot,dpi=200); plt.close()
    except ImportError: print("matplotlib missing; fit saved, plot skipped")
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
