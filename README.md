# MSTD_Groups

Code and data for the paper

> Y. Amit, L. Chen, C. Housholder, J. Im, J. Khan, S. J. Miller, M. Palomares, D. Pradhan,
> **Product and quotient set dominance in finite groups.**

The only computer-assisted part of the paper is **Appendix A**. It shows that every dihedral group
$D_k$ (order $N = 2k$) with $3 \le k \le 60$ satisfies the inequality of Theorem 1.3,

$$\frac{M_1^2}{M_2\,(2^N - B)} > \frac12, \qquad M_1 > 0,$$

so that $D_k$ is product-dominant. Theorem 6.2 handles $k \ge 61$ by hand. Here $M_1$ and $M_2$ are the first
two moments (summed over all subsets) of $d(A) = |AA| - |AA^{-1}|$, and $B$ is the number of balanced subsets
($|AA| = |AA^{-1}|$).

This repository contains everything needed to check that computation:

* the program that counts balanced subsets of $D_k$, the scripts used to run it on a cluster, and the raw
  output of every cluster job (`balanced_counts/`, `data/raw/`);
* two implementations of $M_1$, $M_2$ and the bound for $2^N - B$: a SageMath notebook and a C + Python
  program (`ratio_check/`);
* tables of every computed number (`data/`);
* scripts that re-check all of it, including against brute force (`checks/`).

Everything except the cluster computation of $B(D_k)$ for $18 \le k \le 30$ can be reproduced on a laptop in
a few minutes with `make check`.

---

## Repository layout

| Path | What it is |
|---|---|
| `balanced_counts/` | C program `balanced_dihedral.c` that counts balanced subsets of $D_k$, plus the tools to split the work into independent pieces, run them (on one machine or with Slurm) and combine the results. See [`balanced_counts/README.md`](balanced_counts/README.md). |
| `balanced_counts/cluster_scripts_umiacs/` | The exact Slurm scripts used on the UMIACS Nexus cluster (kept for the record). |
| `balanced_counts/python/` | A slower, readable Python version of the same counter (not used for the published values). |
| `ratio_check/MSTD_Sage.ipynb` | SageMath notebook (the original computation) that computes $M_1$, $M_2$ and bounds for $M_2$ and $2^N-B$, and checks the inequality for $3 \le k \le 61$. |
| `ratio_check/dihedral_moments.py`, `indep.c` | C + Python implementation of the same quantities; computes $M_2$ exactly for every $k \le 61$ in about a minute. The tables in `data/` and in Appendix A come from it. |
| `ratio_check/make_tables.py` | Builds `data/ratio_table.csv` and `data/moments_dihedral.csv` from the computed moments. |
| `checks/` | Brute-force programs and consistency checks (see [What is checked](#what-is-checked)). |
| `data/` | All results as CSV files, plus `raw/raw_shard_outputs_k18-30.tar.xz` (every cluster job's output). See [`data/README.md`](data/README.md). |
| `Makefile` | `make`, `make check`, `make tables`. |

## Requirements

* A C compiler (`gcc` or `clang`; the code uses `unsigned __int128` and `__builtin_popcount`).
* Python 3.8 or newer. `make check` also needs `mpmath` (`pip install mpmath`).
* Only for the notebook: SageMath 10.x (it was run with SageMath 10.6).

## Quick start

```bash
git clone https://github.com/YuvalAmit2/MSTD_Groups.git
cd MSTD_Groups
pip install mpmath
make            # compile the C programs
make check      # run every check (about 5 minutes); ends with "All checks passed."
```

On an x86 machine, `make CFLAGS="-O3 -march=native"` gives faster binaries.

`make tables` recomputes $M_1$, $M_2$ and the bound for $2^N-B$ for $3 \le k \le 61$ from scratch (about a
minute) and rebuilds `data/moments_dihedral.csv` and `data/ratio_table.csv`.

## Results

### Balanced subsets of $D_k$

$$B(D_k) = \\#\\{A \subseteq D_k : |AA| = |AA^{-1}|\\}$$ (also in `data/balanced_counts.csv`, which records
how each value was computed and checked):

| k | B(D_k) | k | B(D_k) |
|---:|---:|---:|---:|
| 1 | 4 | 16 | 3,897,446,296 |
| 2 | 16 | 17 | 15,877,984,160 |
| 3 | 46 | 18 | 64,309,943,398 |
| 4 | 184 | 19 | 260,721,882,046 |
| 5 | 684 | 20 | 1,052,085,090,244 |
| 6 | 2,830 | 21 | 4,247,491,679,638 |
| 7 | 11,008 | 22 | 17,086,382,476,476 |
| 8 | 46,584 | 23 | 68,788,510,296,734 |
| 9 | 192,250 | 24 | 276,258,844,902,918 |
| 10 | 806,396 | 25 | 1,109,610,722,447,684 |
| 11 | 3,328,472 | 26 | 4,449,554,721,586,276 |
| 12 | 13,788,886 | 27 | 17,848,857,181,226,662 |
| 13 | 56,881,972 | 28 | 71,515,396,060,677,424 |
| 14 | 233,244,664 | 29 | 286,563,614,409,785,468 |
| 15 | 957,162,366 | 30 | 1,147,452,736,497,479,150 |

### The inequality of Theorem 1.3 for $3 \le k \le 60$

$M_1$ and $M_2$ are exact for every $k$. For $3 \le k \le 30$ the exact $B$ above is used:

| k | ratio | k | ratio | k | ratio | k | ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0.8889 | 10 | 0.5161 | 17 | 0.5721 | 24 | 0.5971 |
| 4 | 0.6154 | 11 | 0.5755 | 18 | 0.5183 | 25 | 0.6452 |
| 5 | 0.7686 | 12 | 0.5200 | 19 | 0.5843 | 26 | 0.5879 |
| 6 | 0.5778 | 13 | 0.5661 | 20 | 0.5525 | 27 | 0.6732 |
| 7 | 0.6377 | 14 | 0.5006 | 21 | 0.6073 | 28 | 0.6408 |
| 8 | 0.5517 | 15 | 0.5745 | 22 | 0.5460 | 29 | 0.6940 |
| 9 | 0.6041 | 16 | 0.5297 | 23 | 0.6210 | 30 | 0.6385 |

For $31 \le k \le 60$, $2^N - B$ is replaced by the upper bound
$U = \sum_{g} \big[i(\mathcal F_P(g)) + i(\mathcal F_Q(g)) - i(\mathcal F_{PQ}(g,g))\big] \ge 2^N - B$
(proof of Lemma 5.1, equation (A.1) of the paper):

| k | ratio | k | ratio | k | ratio | k | ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 31 | 0.5780 | 39 | 0.7434 | 47 | 0.8545 | 55 | 0.9223 |
| 32 | 0.5603 | 40 | 0.7197 | 48 | 0.8326 | 56 | 0.8999 |
| 33 | 0.6258 | 41 | 0.7740 | 49 | 0.8752 | 57 | 0.9344 |
| 34 | 0.5721 | 42 | 0.7159 | 50 | 0.8136 | 58 | 0.8737 |
| 35 | 0.6655 | 43 | 0.8041 | 51 | 0.8945 | 59 | 0.9431 |
| 36 | 0.6448 | 44 | 0.7806 | 52 | 0.8697 | 60 | 0.9219 |
| 37 | 0.7040 | 45 | 0.8335 | 53 | 0.9086 |  |  |
| 38 | 0.6486 | 46 | 0.7696 | 54 | 0.8480 |  |  |

Every ratio exceeds $1/2$ (the comparison is done in exact rational arithmetic); the smallest is $0.5006$ at
$k = 14$. In every case $M_1 > 0$. The exact integers are in `data/moments_dihedral.csv`.

With the bound $U$ the inequality fails for $k \le 28$ and $k = 30$ (it holds for $k = 29$), which is why $B$
was computed exactly up to $k = 30$.

---

## How the numbers were computed

### 1. Balanced subsets, $B(D_k)$ — `balanced_counts/`

Write $A = \{\rho^a : a \in R\} \cup \{\tau\rho^t : t \in T\}$ with $R, T \subseteq \mathbb Z_k$. Then $AA$ and
$AA^{-1}$ are determined by $R+R$, $R-R$, $T-T$, $T-R$ and $T+R$ in $\mathbb Z_k$, and $A$ is balanced iff
$|(R+R)\cup(T-T)| + |(T-R)\cup(T+R)| = |(R-R)\cup(T-T)| + |T-R|$. The program enumerates pairs $(R, T)$ by a
depth-first search on $k$-bit words, with three exact shortcuts. It can cut the search tree into any number of
independent pieces ("shards"), so large $k$ can be spread over many single-core jobs.

* $k \le 17$: one process (seconds). Commands: `balanced_counts/balanced_dihedral K`.
* $18 \le k \le 30$: on the UMIACS Nexus cluster, about 18,500 core-hours in total (13,100 for $k = 30$). The
  output of every job is in `data/raw/`.

The full instructions for re-running, on one machine or with Slurm, and the story of how $k = 30$ was split up
are in [`balanced_counts/README.md`](balanced_counts/README.md).

### 2. $M_1$, $M_2$ and the bound for $2^N - B$ — `ratio_check/`

By Lemmas 3.5 and 4.3 of the paper, $M_1$ and $M_2$ are signed sums of numbers of independent sets $i(\cdot)$
of the forbiddance graphs $\mathcal F_P(g)$, $\mathcal F_Q(g)$, $\mathcal F_{PP}(g,h)$, $\mathcal F_{QQ}(g,h)$,
$\mathcal F_{PQ}(g,h)$. Both implementations

* sum over one representative of each orbit of $\mathrm{Aut}(D_k)$ on $D_k$ and on $D_k \times D_k$,
  weighted by orbit size;
* count independent sets exactly by branch-and-reduce: split into connected components, use Fibonacci /
  Lucas numbers for paths / cycles, otherwise branch on a vertex of maximum degree, with memoization.

They were written separately.

**SageMath notebook** (`ratio_check/MSTD_Sage.ipynb`, the original computation). Open it in SageMath 10.x and
run all cells. It has three loops:

| Cells | $k$ | $M_1$ | $M_2$ | $2^N - B$ |
|---|---|---|---|---|
| 1st loop | 3–30 | exact | exact | exact (from `dihedral_bals`, i.e. `data/balanced_counts.csv`) |
| 2nd loop | 31–52 | exact | exact | upper bound `bal_bound` $= U$ |
| 3rd loop | 53–61 | exact | upper bound `var_bound` | upper bound $U$ |

Note on the 3rd loop: `var_bound` is $P + Q + 2N(N-1)\,19^{N/6}$. The coefficient 2 requires
$i(\mathcal F_{PP}(g,h)) \le 19^{N/6}$, which holds for $k \ge 30$ because $(9/7)\,7^{N/4} \le 19^{N/6}$ for
$N \ge 59$; Lemma 6.1 as stated gives only the coefficient $16/7$, with which $k = 53, 54$ would fail. The
paper's Appendix A therefore uses the exact $M_2$ (from the C + Python program) for all $k \le 60$, and the
notebook's 3rd loop is not needed for the proof. Its final cell (for $k = 2$) raises `ZeroDivisionError`
because every subset of $D_2$ is balanced; this is expected.

**C + Python** (`ratio_check/dihedral_moments.py`, `ratio_check/indep.c`; no Sage needed):

```bash
make ratio_check/libindep.so
python3 ratio_check/dihedral_moments.py 40 --m2      # one k; prints M1, M2, P, Q, Bbound as JSON
make tables                                          # all k = 3..61, then rebuild data/*.csv
```

Every ratio the notebook prints ($3 \le k \le 61$, in each case with the same choice of exact values and
bounds) is reproduced by this program to 4 decimal places.

### What is checked

`make check` runs the following, stopping at the first failure:

1. The balanced-subset counter against two brute-force programs that enumerate all $2^N$ subsets with no
   shortcuts (`checks/brute_dihedral.c`, $k \le 12$; `checks/reference_bruteforce.py`, $k \le 8$, which
   uses an explicit multiplication table). `checks/brute_dihedral.c` was also run for $k \le 16$.
2. The counter as one process for $13 \le k \le 18$, against `data/balanced_counts.csv`.
3. The splitting scheme that was used for $k = 30$ (shards, re-split shards, hierarchical split), simulated on
   $k = 16$: the pieces must add up to the one-process count (`checks/simulate_hybrid_partition.py`).
4. All cluster results, $18 \le k \le 30$, re-derived from the raw job outputs, with completeness checks
   (every piece present exactly once, integral total). For $k = 30$ it also checks that the 8 shards that
   finished both whole and re-split into 256 pieces agree exactly (`checks/recombine_raw_outputs.py`).
5. The independent-set formulas for $M_1$ and $M_2$ against brute force over all subsets, $3 \le k \le 10$
   (`checks/brute_moments.c`, `checks/compare_moments_bruteforce.py`; also run for $k \le 13$).
6. The ratio table, in exact arithmetic (`ratio_check/make_tables.py`).
7. The numerical inequalities used in Sections 3–6 of the paper: the constants ($7^{1/4} < 1.68$, …), the
   thresholds $k \ge 61$ / $k \ge 62$ in Theorem 6.2, and $N \ge 171$ in Theorem 6.6
   (`checks/paper_thresholds.py`).

In addition, every ratio printed by the notebook ($3 \le k \le 61$) was reproduced by the C + Python program.

---

## Citing

If you use this code or data, please cite the paper and this archive (see `CITATION.cff`; the Zenodo DOI is
on the repository's front page).

## License

MIT License; see `LICENSE`.

## Acknowledgments

This work was done at the 2026 SMALL REU (NSF grant DMS-2341670). The cluster computations were run by
Atrey Desai on the UMIACS Nexus cluster at the University of Maryland.
