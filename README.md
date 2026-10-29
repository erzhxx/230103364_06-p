# CS482 Parallel Computing Lab Practicum

## How to run
```
pip install numpy numba        # numba optional (dense kernel falls back to pure Python)
./run_all.sh <8-digit-student-id>
git push origin main --tags
```
Each milestone can also be run alone (`python3 src/<script>.py`); results land in `results/`.

## Findings (fill in from YOUR results/ - one paragraph)
<!-- Template - replace every <...> with your measured numbers:
Stride-1 costs <x> ns/element but stride-8 (one distinct 64-B line per read) costs <y> ns, a <y/x>x cliff;
interchanging i-j-k to i-k-j gave a <S>x speedup on N=<N>, M=<M>. With 8 counters on one cache line,
unpadded false sharing took <T8>s at P=8 vs <T1>s at P=1 (e_work_adjusted rose to <e>), while padded/privatized
stayed at e=<e'>. The stencil strong-scaling fit gives serial fraction s=<s> (S_max=<1/s>), efficiency
fell to <E>% at P=<Pmax>, weak scaling kept <E_w>%; AI=0.25 FLOP/B is below the ridge point <r>, so the kernel
is memory-bandwidth bound and scaling stalls when the memory bus saturates. -->

## Design notes
* **stride_bench**: the strided reduction runs inside NumPy's C loop (a Python loop would hide the cache effect under ~50 ns/element of interpreter overhead).
* **dense_kernel**: Numba JIT, flat row-major buffers with leading dimension N; `C[i,j]` held in a register in i-j-k so only locality differs.
* **false_sharing**: `mp.Array(..., lock=False)` (a locked array would measure mutex contention); counters aligned to a 64-byte boundary; barrier-synchronised start; clock excludes process start-up. Karp-Flatt is reported two ways because every worker does K increments (work grows with P): `e_handout` (literal formula, ideal = 1) and `e_work_adjusted` (S_P = P*T1/T_P, ideal = 0).
* **scaling_study**: Jacobi 5-point stencil, row-strip decomposition over shared `RawArray`s, 8-row blocking so temporaries stay in cache; checksum is bit-identical to the serial reference.
* **Roofline**: AI = 4 FLOP / 16 B = 0.25 (0.167 with write-allocate). Peak GFLOP/s = cores x base GHz x SIMD FLOP/cycle (from CPU flags); bandwidth = measured STREAM-scale unless `--peak-bw-gbs` is given.
