# Counting balanced subsets of dihedral groups

`balanced_dihedral.c` computes

$$B(D_k) = \#\{A \subseteq D_k : |AA| = |AA^{-1}|\}$$

for the dihedral group $D_k$ of order $N = 2k$, for $k \le 31$. It is a single-threaded C program with no
dependencies and uses under 1 MB of memory. Large $k$ is handled by cutting the search into independent
pieces ("shards") and running many copies of the program at once.

## The method

Write $D_k = \langle \rho, \tau \mid \rho^k = \tau^2 = e,\ \tau\rho\tau = \rho^{-1}\rangle$ and
$A = \{\rho^a : a \in R\} \cup \{\tau\rho^t : t \in T\}$ with $R, T \subseteq \mathbb Z_k$. With
$P = R+R$, $D = R-R$, $E = T-T$, $M = T-R$, $N = T+R$ (all in $\mathbb Z_k$),

```
AA      = { rho^x : x in P u E }  u  { tau rho^y : y in M u N }
AA^{-1} = { rho^x : x in D u E }  u  { tau rho^y : y in M }
A is balanced  <=>  |P u E| + |M u N| = |D u E| + |M|
```

Every set is a $k$-bit word, and a sumset is a union of cyclic shifts. The program does a depth-first search
over the pairs $(R, T)$. Adding one element updates $P, D, E, M, N$ with a constant number of word operations.
Three exact shortcuts avoid most of the tree:

1. If $AA = AA^{-1} = G$, the same holds for every superset of $A$, so the whole subtree is balanced and is
   counted in one step.
2. If $|A| \ge k$, every strict superset $A'$ has $|A'| > N/2$, hence $A'A' = A'A'^{-1} = G$; again the
   subtree is counted in one step.
3. The automorphisms $\rho \mapsto \rho$, $\tau \mapsto \tau\rho^v$ shift $T$. So the program only enumerates
   subsets with $\tau \in A$ (that is, $0 \in T$) and recovers the full count as
   $B = \#\{A : T = \emptyset,\ A \text{ balanced}\} + k \sum_{A \text{ balanced},\, 0 \in T} 1/|T|$.
   This is computed exactly, by keeping a separate count for each value of $|T|$.

Shortcut 1 hits most subsets for large $k$, because almost all subsets of a large group have
$AA = AA^{-1} = G$ (Miller–Vissuet). The cost grows by about a factor 3.2 per unit of $k$.

## Build

```bash
gcc -O3 -march=native -funroll-loops -o balanced_dihedral balanced_dihedral.c
```

(or `make` at the top of the repository). On a cluster, compile on a compute node, or use `-march=x86-64-v2`
if login and compute nodes differ. For ARM nodes (for example Ampere Altra) build a separate binary there.

## Running on one machine

```bash
./balanced_dihedral 18                  # one process
python3 run_parallel.py 22 8            # 8 worker processes; resumable
```

`run_parallel.py K [WORKERS] [SPLITDEPTH] [NSHARD]` writes each shard's result to `out_k<K>_n<NSHARD>/` and
skips shards that are already done. You can stop it and rerun the same command to resume.

Cost in core-seconds: the planning estimate for one 2.1 GHz Xeon core, and what the cluster runs actually
used (summed over all shards, on a mix of x86 and ARM nodes):

| k | estimate | measured | | k | estimate | measured |
|---:|---:|---:|---|---:|---:|---:|
| 18 | 25 | 66 | | 25 | 82,800 | 133,353 |
| 19 | 75 | 183 | | 26 | 277,000 | 476,533 |
| 20 | 255 | 536 | | 27 | 828,000 | 1,582,627 |
| 21 | 775 | 1,560 | | 28 | 2,740,000 | 4,891,016 |
| 22 | 2,600 | 4,945 | | 29 | 8,360,000 | 12,357,756 |
| 23 | 8,100 | 15,369 | | 30 | 28,000,000 | 47,091,403 |
| 24 | 26,600 | 49,608 | | | | |

A single machine is practical up to about $k = 24$.

## Splitting the work into shards

```
./balanced_dihedral K NSHARD SHARD SPLITDEPTH
```

runs one shard. The search tree is cut at depth `SPLITDEPTH` (6 was used throughout). The subtrees below that
depth are numbered in the order the search reaches them, and shard `s` gets the subtrees whose number is
congruent to `s` mod `NSHARD`. Shard 0 also counts everything above the cut, and the subsets with no
reflections. Shards are deterministic and independent. Each prints one line:

```
k=30 task 7700/20000  partial: c_1 c_2 ... c_k  emptyT=e seconds=s
```

Here `c_t` is the number of balanced subsets with $\tau \in A$ and $|T| = t$ found by this shard, and `e` is
the number of balanced subsets with $T = \emptyset$ (nonzero only for shard 0). Then
$B = \sum e + k\sum_t (\sum c_t)/t$, summed over all shards.

```
python3 combine_files.py K NSHARD [DIRECTORY]
```

adds up the shard files. It refuses to give an answer unless every shard `0..NSHARD-1` is present exactly once
and the weighted total is an integer.

Because the numbering only depends on the search order, a shard can later be replaced by finer pieces:
shard `s` of `NSHARD` is exactly the union of shards `s + q*NSHARD` of `256*NSHARD`, $q = 0, \dots, 255$.
There is also a hierarchical mode for a piece that is a single subtree at depth 6 and so cannot be refined at
that depth:

```
./balanced_dihedral K NCHILD CHILD CHILDDEPTH NPARENT PARENT PARENTDEPTH
```

This runs piece `CHILD` of `NCHILD` (cut at depth `CHILDDEPTH`) inside shard `PARENT` of `NPARENT` (cut at
depth `PARENTDEPTH`).

## Running with Slurm

```bash
mkdir -p log
K=25 NSHARD=1000 sbatch --array=0-999%256 slurm_array.sh     # %256 = number of cores to use at once
# wait until squeue -u $USER shows nothing left, then
python3 combine_files.py 25 1000
```

Resubmitting the same `sbatch` line resumes an interrupted run, because finished shards are skipped. Shard
counts used: `NSHARD=1000` for $k \le 27$, 2000 for $k = 28$, 8000 for $k = 29$, 20000 for $k = 30$.
`ospool.sub` is an untested HTCondor equivalent.

**Validate first.** Before any production run, reproduce the known values for $k = 18, \dots, 21$
(`data/balanced_counts.csv`) with the same build and cluster setup. This was done on the cluster before the
production runs: $k = 18, \dots, 21$ as sharded runs, and $k = 18$ as a single process on its Intel, AMD and
ARM nodes.

## How $k = 30$ was split up

$k = 30$ took about 47 million core-seconds. A handful of shards contain most of the work, so the run was
refined in several stages. Every stage uses the exact sub-partition rule above, and
`combine_k30_recursive.py` checks that the final collection of pieces covers the search tree exactly once.

1. 20,000 shards at depth 6. 19,980 finished; 20 were much slower than the rest.
2. Each of those 20 was replaced by its 256 pieces of the 5,120,000-way split. All but 12 finished.
3. Each of those 12 was replaced by its 256 pieces of the 1,310,720,000-way split. All but 12 finished.
4. A controller (`cluster_scripts_umiacs/slurm_k30_recursive_controller.sh`) kept splitting the unfinished
   pieces 256 ways and cancelling each round after 60 seconds (generations 3–6, files in
   `out_k30_recursive/`). The same 12 pieces stayed unfinished every time. Each of them is a single subtree at
   depth 6, so splitting at depth 6 cannot divide it further; the other 255 children of each are empty.
5. Each of the 12 was finally split at depth 18 into 256 pieces in hierarchical mode (`out_k30_hier/`).

```bash
python3 combine_k30_recursive.py DATA_DIR      # DATA_DIR holds out_k30_* and recursive_state/
```

8 of the 20 slow original shards eventually finished on their own as well. For each of them, the sum of its
256 step-2 pieces equals the original shard's output exactly (`checks/check_k30_parents.py`), which is a
direct test of the re-splitting on real $k = 30$ data. The whole scheme is also simulated on small $k$ by
`checks/simulate_hybrid_partition.py`.

## Files

| File | Purpose |
|---|---|
| `balanced_dihedral.c` | The counter (serial, sharded and hierarchical modes). |
| `combine_files.py` | Combine shard outputs for one `K`, `NSHARD`. |
| `combine_k30_recursive.py` | Combine and check the multi-level $k = 30$ partition. |
| `run_parallel.py` | Run all shards on one machine with a process pool. |
| `slurm_array.sh` | Generic Slurm job array (one shard per task, resumable). |
| `ospool.sub` | HTCondor submit file (not used for the published values). |
| `estimate_tree_size.c` | Estimates the size of the search tree for large `k` (planning only). |
| `python/balanced_dihedral.py` | Readable Python version of the counter; can be imported from Sage. |
| `python/balanced_dihedral_cy.pyx` | Cython version of the same. |
| `cluster_scripts_umiacs/` | The scripts as run on UMIACS Nexus. Partition, account and node names are specific to that cluster, and the absolute path at the top of each was replaced by `$SLURM_SUBMIT_DIR`. They expect `balanced_dihedral`, `balanced_dihedral_arm64` (ARM build), `combine_files.py` and `combine_k30_recursive.py` in the submit directory. |
