import time
from multiprocessing import Process, Value, Lock


def contended_worker(shared_counter, lock, iterations):
    for _ in range(iterations):
        with lock:
            shared_counter.value += 1


def run_contended(p, total_increments=2_000_000):
    # Dividing evenly ensures exactly total_increments for P in {1, 2, 4}.
    increments_per_worker = total_increments // p
    counter = Value("i", 0)
    lock = Lock()
    processes = [
        Process(
            target=contended_worker,
            args=(counter, lock, increments_per_worker)
        )
        for _ in range(p)
    ]

    start = time.perf_counter()
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    runtime = time.perf_counter() - start

    assert counter.value == total_increments, (
        f"Counter mismatch: {counter.value} != {total_increments}"
    )
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
        runtimes[p] = run_contended(p)
        print(f"P={p} | Runtime={runtimes[p]:.3f}s")
    calculate_metrics(runtimes)
