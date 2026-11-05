# Task 09 — Multi-component workload

The stated phases are 2% initial disk I/O/parameter broadcast, 6% boundary synchronization, and 92% domain computation. Under the task's simplified classification, aggregate serial/overhead fraction is
`alpha=0.02+0.06=0.08`; parallel fraction is `0.92`.

For P=512:
`S=512-0.08*511=471.12`.

For P=2,048:
`S=2048-0.08*2047=1884.24`.

This treats both I/O/broadcast and synchronization as non-scaling serial overhead. In a real application, communication may itself parallelize or vary with P, so profiling should replace this constant-alpha approximation.
