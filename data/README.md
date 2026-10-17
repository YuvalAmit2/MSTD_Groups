# Data

All numbers are exact integers unless stated otherwise. $N = 2k$ is the order of $D_k$.

| File | Contents |
|---|---|
| `balanced_counts.csv` | $B(D_k)$, the number of balanced subsets of $D_k$, for $1 \le k \le 30$. The columns say how each value was computed (one process, or cluster with the number of shards and core-seconds) and which independent checks it passed. |
| `moments_dihedral.jsonl` | Output of `ratio_check/dihedral_moments.py K --m2` for $3 \le k \le 61$, one JSON object per line. Keys: `M1`, `M2`, `P` $=\sum_g i(\mathcal F_P(g))$, `Q` $=\sum_g i(\mathcal F_Q(g))$, `Bbound` $= U$ (below), plus `pair_orbits`, `indep_counts` and `seconds` (run information). Integers above $2^{53}$ are stored as strings. |
| `moments_dihedral.csv` | The same numbers as a table: `k, N, M1, M2, P, Q, U_upper_bound_for_2^N-B`. |
| `ratio_table.csv`, `ratio_table.md` | For $3 \le k \le 60$: which value was used for $2^N - B$ (exact $B$ for $k \le 30$, the bound $U$ for $k \ge 31$), the ratio $M_1^2/(M_2(2^N-B))$ to 6 decimals, and whether it exceeds $1/2$ (decided in exact arithmetic). |
| `raw/raw_shard_outputs_k18-30.tar.xz` | The output of every cluster job for $18 \le k \le 30$ (5.6 MB; 63,000 small text files). |

Here $U = \sum_{g \in D_k}\big[i(\mathcal F_P(g)) + i(\mathcal F_Q(g)) - i(\mathcal F_{PQ}(g,g))\big]$, which
satisfies $2^N - B \le U$ (proof of Lemma 5.1; equation (A.1) of the paper).

## The raw cluster outputs

```bash
python3 checks/recombine_raw_outputs.py      # unpacks into data/raw/extracted/ and re-derives k = 18..30
```

Directory layout inside the archive:

| Directory | What it holds |
|---|---|
| `out_k<K>_n<NSHARD>/shard_<s>.txt` | Shard `s` of `NSHARD` for that `k` ($18 \le k \le 29$, and the first stage of $k = 30$). |
| `out_k30_sub256/sub_<p>_<q>.txt` | $k = 30$, piece $p + 20000q$ of the 5,120,000-way split (replaces slow shard $p$). |
| `out_k30_sub2/sub2_<b>_<q>.txt` | $k = 30$, piece $b + 5120000q$ of the 1,310,720,000-way split. |
| `out_k30_recursive/gen_<g>/task_<t>.txt` | $k = 30$, generations 3–6 of the 256-way refinement. |
| `out_k30_hier/parent_<p>_child_<c>.txt` | $k = 30$, hierarchical pieces (parent cut at depth 6, child cut at depth 18). |
| `recursive_state/parents_gen<g>.txt` | The pieces still unfinished at each generation. |

Each file contains one line

```
k=<K> task <s>/<NSHARD>  partial: c_1 ... c_K  emptyT=<e> seconds=<t>
```

where `c_t` is the number of balanced subsets with $\tau \in A$ and exactly $t$ reflections found in this
piece, `e` is the number of balanced subsets with no reflections (nonzero only for piece 0), and `seconds` is
the CPU time. Over all pieces, $B(D_k) = \sum e + k\sum_t \big(\sum c_t\big)/t$. Temporary files of
interrupted jobs were removed. Of the 20 slow first-stage $k = 30$ shards, 8 also finished whole; those files
are kept, and `combine_k30_recursive.py` ignores them in favour of their replacements.
