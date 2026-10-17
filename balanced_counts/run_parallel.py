#!/usr/bin/env python3
"""Run the D_k count on one machine, across processes, and combine the parts.

    python3 run_parallel.py K [WORKERS] [SPLITDEPTH] [NSHARD]

Each shard's output is written to out_k<K>/shard_<i>.txt as it finishes, and a
re-run skips shards that are already complete -- so an interrupted run resumes
where it stopped instead of starting over.  Delete the directory to force a
clean re-run.

The C binary is single threaded and uses under 1 MB of memory; parallelism is
just many independent processes.  NSHARD defaults to 8 * WORKERS so the pool
self-balances across heterogeneous cores.
"""
import subprocess, sys, os
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "balanced_dihedral")
sys.path.insert(0, HERE)
from combine_files import combine_dir, core_seconds


def run(job):
    k, nshard, tid, split, outdir = job
    path = os.path.join(outdir, f"shard_{tid}.txt")
    if os.path.exists(path):
        with open(path, errors="replace") as fh:
            if "partial:" in fh.read():
                return "cached"
    r = subprocess.run([BIN, str(k), str(nshard), str(tid), str(split)],
                       capture_output=True, text=True)
    if "partial:" not in r.stdout:
        raise RuntimeError(f"shard {tid} produced no result:\n{r.stdout}\n{r.stderr}")
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(r.stdout)
    os.replace(tmp, path)          # atomic: a killed write never leaves a half file
    return "ran"


if __name__ == "__main__":
    import time
    k       = int(sys.argv[1])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else os.cpu_count()
    split   = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    nshard  = int(sys.argv[4]) if len(sys.argv) > 4 else 8 * workers
    outdir  = os.path.join(os.getcwd(), f"out_k{k}_n{nshard}")
    os.makedirs(outdir, exist_ok=True)

    t0 = time.time()
    jobs = [(k, nshard, t, split, outdir) for t in range(nshard)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        states = list(ex.map(run, jobs))
    wall = time.time() - t0

    ans, secs = combine_dir(k, nshard, outdir)
    reused = states.count("cached")
    print(f"balanced subsets of D_{k} = {ans}")
    print(f"  k = {k}   workers = {workers}   shards = {nshard}"
          + (f"   ({reused} shards reused from a previous run)" if reused else ""))
    print(f"  wall time {wall:,.1f} s   {core_seconds(secs)} core-seconds")
