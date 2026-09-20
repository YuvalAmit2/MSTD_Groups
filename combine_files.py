#!/usr/bin/env python3
"""Aggregate shard outputs into the final count.

    python3 combine_files.py K NSHARD [directory-or-file]

The directory defaults to out_k<K>_n<NSHARD>, which is where both drivers put
their shard files.  Reads every 'task i/NSHARD' line under the given path, checks that each shard
0..NSHARD-1 appears exactly once, and prints the total.  Partial results are
additive, so file layout and shard order do not matter.

Two independent completeness checks: every shard id must be present, and the
weighted sum k * sum_t tot[t]/t must come out an exact integer.
"""
import sys, os, re
from fractions import Fraction

LINE = re.compile(r"k=\s*(\d+)\s+task\s+(\d+)/(\d+)\s+partial:\s*(.*?)\s*"
                  r"emptyT=(\d+)\s+seconds=([\d.]+)")


def core_seconds(x):
    """Readable fixed-point seconds, however many orders of magnitude."""
    return f"{x:,.1f}" if x < 1000 else f"{x:,.0f}"


def combine_dir(k, nshard, path):
    """Return (answer, core_seconds). Exits with a clear message if the shard
    set is incomplete or inconsistent."""
    tot = [0] * (k + 2)
    empty = 0
    secs = 0.0
    seen = {}
    files = ([path] if os.path.isfile(path)
             else [os.path.join(dp, f) for dp, _, fs in os.walk(path) for f in fs])
    for fn in files:
        with open(fn, errors="replace") as fh:
            for line in fh:
                m = LINE.search(line)
                if not m:
                    continue
                kk, tid, ns = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if kk != k or ns != nshard:
                    sys.exit(f"{fn}: shard reports k={kk} nshard={ns}, expected {k}/{nshard}. "
                             f"Mixing runs with different shard counts is not valid -- "
                             f"use a fresh output directory.")
                if tid in seen:
                    sys.exit(f"shard {tid} appears twice ({seen[tid]} and {fn})")
                seen[tid] = fn
                for i, v in enumerate(m.group(4).split()):
                    tot[i + 1] += int(v)
                empty += int(m.group(5))
                secs += float(m.group(6))
    missing = [i for i in range(nshard) if i not in seen]
    if missing:
        sys.exit(f"{len(missing)} of {nshard} shard(s) missing, e.g. {missing[:10]}.\n"
                 f"Re-run just those:  ./balanced_dihedral {k} {nshard} <id> <split>\n"
                 f"(or re-run the same run_parallel.py / sbatch command -- completed "
                 f"shards are reused.)")
    ans = k * sum(Fraction(tot[t], t) for t in range(1, k + 1)) + empty
    if ans.denominator != 1:
        sys.exit("non-integral total: the shard set is inconsistent, do not trust this run")
    return int(ans), secs


if __name__ == "__main__":
    k, nshard = int(sys.argv[1]), int(sys.argv[2])
    path = sys.argv[3] if len(sys.argv) > 3 else f"out_k{k}_n{nshard}"
    if not os.path.exists(path):
        sys.exit(f"no such directory: {path}\n"
                 f"Shard files live in out_k<K>_n<NSHARD>/ -- check that the k and "
                 f"shard count here match the ones the run was submitted with.")
    ans, secs = combine_dir(k, nshard, path)
    print(f"balanced subsets of D_{k} = {ans}")
    print(f"  k = {k}   shards = {nshard}   {core_seconds(secs)} core-seconds")
