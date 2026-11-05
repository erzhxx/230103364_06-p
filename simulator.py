#!/usr/bin/env python3
"""Compare Amdahl strong scaling and Gustafson weak scaling."""
import argparse, csv, math
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--alpha",type=float,default=0.04)
    ap.add_argument("--max-p",type=int,default=16384)
    ap.add_argument("--output",default="benchmarks/simulation.csv")
    ap.add_argument("--plot",default="plots/scaling_comparison.png")
    ap.add_argument("--points",type=int,default=100)
    a=ap.parse_args()
    if not 0.001 <= a.alpha <= 0.20: ap.error("alpha must be in [0.001, 0.20]")
    if not 1 <= a.max_p <= 65536: ap.error("max-p must be in [1, 65536]")
    # Log-spaced integer processor counts, plus endpoints.
    vals={1,a.max_p}
    for i in range(a.points):
        vals.add(max(1,min(a.max_p,round(math.exp(math.log(a.max_p)*i/max(1,a.points-1))))))
    ps=sorted(vals)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="") as f:
        w=csv.writer(f); w.writerow(["P","alpha","amdahl_speedup","gustafson_speedup","gustafson_efficiency"])
        for p in ps:
            amd=1/(a.alpha+(1-a.alpha)/p)
            gus=p-a.alpha*(p-1)
            w.writerow([p,a.alpha,amd,gus,gus/p])
    try:
        import matplotlib.pyplot as plt
        x=ps
        amd=[1/(a.alpha+(1-a.alpha)/p) for p in x]
        gus=[p-a.alpha*(p-1) for p in x]
        plt.figure(figsize=(8,5))
        plt.plot(x,x,label="Ideal linear")
        plt.plot(x,amd,label="Amdahl (strong)")
        plt.plot(x,gus,label="Gustafson (weak)")
        plt.xscale("log",base=2); plt.yscale("log",base=2)
        plt.xlabel("Processor count P"); plt.ylabel("Speedup")
        plt.title(f"Scaling comparison (alpha={a.alpha:g})")
        plt.grid(True,which="both",alpha=.25); plt.legend(); plt.tight_layout()
        pth=Path(a.plot); pth.parent.mkdir(parents=True,exist_ok=True)
        plt.savefig(pth,dpi=200); plt.close()
    except ImportError:
        print("matplotlib not installed; CSV created, plot skipped")
    print(f"Wrote {out}")

if __name__=="__main__": main()
