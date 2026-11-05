# Task 03 — The serial-fraction measurement frame

The apparent paradox comes from comparing fractions measured against different workloads.

In Amdahl's fixed-size model, `s_A` is measured for a fixed problem on one processor. The same total work is then distributed across P processors. The serial time does not shrink, while the parallel time is divided by P:
`S_A(P)=1/[s_A+(1-s_A)/P]`.
The asymptotic ceiling is `1/s_A`.

In Gustafson's model, `alpha` is the fraction of the *parallel execution time* spent in serial sections on the P-processor machine. The parallel part of the problem is allowed to grow with P. The equivalent serial execution time for the scaled workload is `alpha + P(1-alpha)`, so `S_G(P)=alpha+P(1-alpha)`.

There is no claim that a fixed serial overhead vanishes. Instead, the denominator and numerator refer to a larger workload: the serial component remains approximately fixed in elapsed time while the parallel component represents P times as much work. The serial *fraction* can consequently remain small even as the total amount of useful work grows.

The invariance is conditional. If startup, reductions, communication, synchronization, or data movement increase with P, then `alpha` is not invariant. Gustafson's law resolves the frame-of-reference mismatch; it does not repeal serial dependencies or guarantee constant overhead.
