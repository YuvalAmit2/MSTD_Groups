#!/usr/bin/env python3
"""Re-derive B(D_k), 18 <= k <= 30, from the raw cluster shard outputs and
compare with data/balanced_counts.csv.

    python3 checks/recombine_raw_outputs.py

Unpacks data/raw/raw_shard_outputs_k18-30.tar.xz into data/raw/extracted/
(once), then
  * k = 18..29: balanced_counts/combine_files.py (every shard present exactly
    once, integral weighted total);
  * k = 30:     balanced_counts/combine_k30_recursive.py (the multi-level
    re-split partition, see balanced_counts/README.md);
  * k = 30:     checks/check_k30_parents.py (shards that finished both whole and
    re-split agree exactly).
"""
import csv, os, subprocess, sys, tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
EXTRACTED = os.path.join(RAW, "extracted")
sys.path.insert(0, os.path.join(ROOT, "balanced_counts"))
from combine_files import combine_dir  # noqa: E402

if not os.path.isdir(EXTRACTED):
    print("unpacking raw shard outputs ...", flush=True)
    with tarfile.open(os.path.join(RAW, "raw_shard_outputs_k18-30.tar.xz")) as tf:
        if hasattr(tarfile, "data_filter"):
            tf.extractall(EXTRACTED, filter="data")
        else:
            tf.extractall(EXTRACTED)

expected = {}
with open(os.path.join(ROOT, "data", "balanced_counts.csv")) as fh:
    for row in csv.DictReader(fh):
        expected[int(row["k"])] = int(row["balanced_subsets"])

ok = True
nshard = {k: 1000 for k in range(18, 28)}
nshard.update({28: 2000, 29: 8000})
for k in range(18, 30):
    ans, secs = combine_dir(k, nshard[k], os.path.join(EXTRACTED, f"out_k{k}_n{nshard[k]}"))
    good = ans == expected[k]
    ok &= good
    print(f"k={k}: {ans}  ({nshard[k]} shards, {secs:,.0f} core-seconds)  matches table: {good}")

out = subprocess.run([sys.executable, os.path.join(ROOT, "balanced_counts", "combine_k30_recursive.py"), EXTRACTED],
                     capture_output=True, text=True)
print(out.stdout.strip() or out.stderr.strip())
ans30 = int(out.stdout.split("=")[1].split()[0]) if "balanced subsets of D_30" in out.stdout else None
good = ans30 == expected[30]
ok &= good
print(f"k=30 matches table: {good}")

out = subprocess.run([sys.executable, os.path.join(ROOT, "checks", "check_k30_parents.py"), EXTRACTED],
                     capture_output=True, text=True)
print(out.stdout.strip())
ok &= out.returncode == 0 and "False" not in out.stdout

print("ALL OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
