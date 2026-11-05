# Task 17 — 3D 7-point stencil surface-to-volume ratio

For a cubic subdomain of side length n, interior updates scale as volume `O(n^3)` and face exchange scales as surface `O(n^2)`. The communication/computation ratio is therefore `O(n^2)/O(n^3)=O(1/n)`.

Under weak scaling, each processor keeps a fixed local subdomain dimension n. If P processors are added and the global domain volume grows proportionally to P, the global cubic dimension grows as `P^(1/3)`, but the local surface-to-volume ratio per processor remains approximately constant. It does **not** automatically improve with P under fixed local domain size.

If instead a single global domain is enlarged while processor count stays fixed, n grows and the ratio improves as 1/n. In distributed weak scaling, communication per processor remains proportional to local face area and computation to local volume; halo exchange, network contention, and synchronization may still degrade wall-clock performance.
