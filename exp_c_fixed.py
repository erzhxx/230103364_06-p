import time
from multiprocessing import Pool


def private_worker(iterations):
    local_sum = 0
    for _ in range(iterations):
        local_sum += 1
    return local_sum


def run_privatized(p, total_increments=20_000_000):
    increments_per_worker = total_increments // p
    tasks = [increments_per_worker] * p

    start = time.perf_counter()
    with Pool(processes=p) as pool:
        results = pool.map(private_worker, tasks)

    total = sum(results)
    runtime = time.perf_counter() - start
    assert total == total_increments, f"Total mismatch: {total} != {total_increments}"
    return runtime


def calculate_metrics(runtimes):
    t1 = runtimes[1]
    for p in (2, 4):
        tp = runtimes[p]
        speedup = t1 / tp
        e = ((p * tp / t1) - 1.0) / (p - 1.0)
        print(f"P={p} | Speedup={speedup:.2f}x | Karp-Flatt e={e:.3f}")


if __name__ == "__main__":
    runtimes = {}
    for p in (1, 2, 4):
        runtimes[p] = run_privatized(p)
        print(f"P={p} | Runtime={runtimes[p]:.3f}s")
    calculate_metrics(runtimes)
