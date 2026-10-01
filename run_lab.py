import time, json, numpy as np, numba
from numba import njit, prange
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
res = {}
MAXT = numba.config.NUMBA_NUM_THREADS
print("Hardware Threads Detected:", MAXT)

@njit(parallel=True)
def monte_carlo_pi(n):
    inside = 0
    for i in prange(n):
        x = np.random.uniform(0.0, 1.0); y = np.random.uniform(0.0, 1.0)
        if x*x + y*y <= 1.0: inside += 1
    return 4.0*inside/n
_ = monte_carlo_pi(10_000)
SAMPLES = 120_000_000
tcs = sorted(set(t for t in [1,2,4,8,MAXT] if t <= MAXT))
res["mc"] = []
t1 = None
print(f"{'Threads':<8}|{'Time':<10}|{'Speedup':<9}|{'Eff%':<8}|pi")
for t in tcs:
    numba.set_num_threads(t)
    s = time.perf_counter(); p = monte_carlo_pi(SAMPLES); e = time.perf_counter()-s
    if t == 1: t1 = e
    sp = t1/e; ef = sp/t*100
    res["mc"].append(dict(t=t, time=e, speedup=sp, eff=ef, pi=p))
    print(f"{t:<8}|{e:<10.4f}|{sp:<9.2f}|{ef:<8.1f}|{p}")
numba.set_num_threads(MAXT)

# Challenge 1 Q-D demo: serial python-level check is not needed

def mk(axis):
    @njit(parallel=True)
    def f(h, w, max_iter):
        img = np.zeros((h, w), dtype=np.int32)
        if axis == 0:
            for r in prange(h):
                cy = -1.2 + (r/h)*2.4
                for c in range(w):
                    cx = -2.0 + (c/w)*2.5
                    zr = 0.0; zi = 0.0; it = 0
                    while (zr*zr + zi*zi <= 4.0) and (it < max_iter):
                        nr = zr*zr - zi*zi + cx; zi = 2.0*zr*zi + cy; zr = nr; it += 1
                    img[r, c] = it
        else:
            for c in prange(w):
                cx = -2.0 + (c/w)*2.5
                for r in range(h):
                    cy = -1.2 + (r/h)*2.4
                    zr = 0.0; zi = 0.0; it = 0
                    while (zr*zr + zi*zi <= 4.0) and (it < max_iter):
                        nr = zr*zr - zi*zi + cx; zi = 2.0*zr*zi + cy; zr = nr; it += 1
                    img[r, c] = it
        return img
    return f
rows_f, cols_f = mk(0), mk(1)
_ = rows_f(100,100,50); _ = cols_f(100,100,50)
H=W=2500; MI=1000
t0=time.perf_counter(); g=rows_f(H,W,MI); tr=time.perf_counter()-t0
t0=time.perf_counter(); g2=cols_f(H,W,MI); tc=time.perf_counter()-t0
print(f"rows {tr:.3f}s cols {tc:.3f}s equal={np.array_equal(g,g2)}")
res["mandel"] = dict(rows=tr, cols=tc)
plt.figure(figsize=(8,8)); plt.imshow(g, cmap='magma', extent=[-2.0,0.5,-1.2,1.2])
plt.title(f"Mandelbrot {H}x{W} (Render: {tr:.2f}s)"); plt.axis('off')
plt.savefig('mandelbrot_output.png', dpi=300, bbox_inches='tight')
# workload profile per row (iterations) for load-imbalance Q
work = g.sum(axis=1).astype(float)
n=len(work); fr=lambda a,b: work[int(a*n):int(b*n)].sum()/work.sum()*100
res["imb"] = dict(top20=fr(0,.2), center20=fr(.4,.6), bottom20=fr(.8,1))
print(res["imb"])

@njit(parallel=True)
def heat_step(u, un, alpha=0.20):
    rows, cols = u.shape
    for i in prange(1, rows-1):
        for j in range(1, cols-1):
            un[i,j] = u[i,j] + alpha*(u[i+1,j]+u[i-1,j]+u[i,j+1]+u[i,j-1]-4.0*u[i,j])
def heat(dtype, steps=300, n=1500):
    u = np.zeros((n,n), dtype=dtype); un = np.zeros_like(u)
    u[0,:]=100; u[:,0]=100; un[0,:]=100; un[:,0]=100
    heat_step(u, un)
    s=time.perf_counter()
    for _ in range(steps):
        heat_step(u, un); u, un = un, u
    e=time.perf_counter()-s
    return e, n*n*steps/e/1e6
res["heat"] = {}
for name, dt in [("float64", np.float64), ("float32", np.float32)]:
    e, m = heat(dt); res["heat"][name] = dict(time=e, mcells=m)
    print(name, f"{e:.3f}s {m:.2f} Mcells/s")
json.dump(res, open("results.json","w"), indent=1)
