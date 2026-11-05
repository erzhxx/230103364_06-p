# Task 15 — Energy and power under weak scaling

Let each active node draw `Pidle + Pactive` while computing (where `Pactive` is incremental dynamic power), and let wall-clock duration be T. With P nodes, total energy is
`E_P = P*(Pidle+Pactive)*T`.
For one node:
`E_1=(Pidle+Pactive)*T`.
Thus, for identical wall-clock time, `E_P/E_1=P` under the stated identical-node power assumption.

If `Pactive` instead denotes total active power rather than incremental power, write `E_P=P*Pactive*T` and `E_1=Pactive*T`; the ratio remains P. Real systems may have DVFS, idle nodes, communication power, cooling overhead, and different utilization. Gustafson's speedup is a performance metric, not an energy-efficiency guarantee. Energy per unit of useful work may improve, remain constant, or worsen depending on power and work scaling.
