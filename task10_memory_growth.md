# Task 10 — Memory ceiling and 3D grid dimension

Assumptions (needed because bytes per cell and the proportionality constant are not specified): 32 GB usable memory per node; one 8-byte value per grid cell; no halo, metadata, temporary arrays, or OS reserve. Total memory is `M_total=32*n_nodes GB`.

Number of cells is `N^3 <= M_total/(8 bytes)`. Using decimal GB (1 GB = 10^9 bytes):
- 64 nodes: total = 2,048 GB = 2.048e12 bytes; cells <= 2.56e11; `N <= floor((2.56e11)^(1/3)) = 6,349`.
- 512 nodes: total = 16,384 GB = 1.6384e13 bytes; cells <= 2.048e12; `N <= floor((2.048e12)^(1/3)) = 12,699`.

Because nodes increase by 8x, total capacity increases 8x and the cubic grid's linear dimension increases by `8^(1/3)=2x`. Actual solver limits will be lower when halos, multiple fields, ghost zones, and memory headroom are included. If 32 GB means per-node memory cap and each cell uses b bytes, use `N=floor((32e9*n_nodes/b)^(1/3))`.
