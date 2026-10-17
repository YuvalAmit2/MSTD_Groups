#!/usr/bin/env python3
"""Turn the exact moment data into the tables used in Appendix A.

    python3 ratio_check/make_tables.py [MOMENTS_JSONL] [BALANCED_CSV] [OUTDIR]

Defaults: data/moments_dihedral.jsonl, data/balanced_counts.csv, data/.

Writes
  data/moments_dihedral.csv  exact M1, M2, P, Q and the bound U >= 2^N - B, 3 <= k <= 61
  data/ratio_table.csv       the ratio M1^2 / (M2 (2^N - B)) used for each k, 3 <= k <= 60
  data/ratio_table.md        the same table in Markdown (for the README)

For 3 <= k <= 30 the exact number B of balanced subsets is used.  For
31 <= k <= 60 we use the upper bound
    2^N - B  <=  U := sum_g [ i(F_P(g)) + i(F_Q(g)) - i(F_PQ(g,g)) ]
from the proof of Lemma 5.1.  Every comparison with 1/2 is done in exact
rational arithmetic.
"""
import csv, json, os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
moments_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "moments_dihedral.jsonl")
balanced_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "balanced_counts.csv")
outdir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "data")

B = {}
with open(balanced_path) as fh:
    for row in csv.DictReader(fh):
        B[int(row["k"])] = int(row["balanced_subsets"])

rows = []
with open(moments_path) as fh:
    for line in fh:
        r = json.loads(line)
        rows.append({key: (int(v) if key not in ("seconds",) and str(v).lstrip("-").isdigit() else v)
                     for key, v in r.items()})
rows.sort(key=lambda r: r["k"])

with open(os.path.join(outdir, "moments_dihedral.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["k", "N", "M1", "M2", "P", "Q", "U_upper_bound_for_2^N-B"])
    for r in rows:
        w.writerow([r["k"], r["N"], r["M1"], r["M2"], r["P"], r["Q"], r["Bbound"]])

table = []
for r in rows:
    k, N, M1, M2 = r["k"], r["N"], r["M1"], r["M2"]
    if k > 60:
        continue
    if k <= 30:
        denom_B, source = 2 ** N - B[k], "exact B"
    else:
        denom_B, source = r["Bbound"], "upper bound U"
    assert M2 * 2 ** N >= M1 * M1                       # variance is non-negative
    if k in B:
        assert r["Bbound"] >= 2 ** N - B[k]             # U really bounds 2^N - B
    ratio = Fraction(M1 * M1, M2 * denom_B)
    table.append({"k": k, "N": N, "2^N-B used": source, "ratio": ratio, "ok": ratio > Fraction(1, 2)})

with open(os.path.join(outdir, "ratio_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["k", "N", "value_used_for_2^N-B", "ratio_M1^2/(M2*(2^N-B))", "ratio_exceeds_1/2"])
    for t in table:
        w.writerow([t["k"], t["N"], t["2^N-B used"], f"{float(t['ratio']):.6f}", t["ok"]])

with open(os.path.join(outdir, "ratio_table.md"), "w") as fh:
    fh.write("| k | N = 2k | 2^N - B | M1^2 / (M2 (2^N - B)) |\n|---:|---:|:---|---:|\n")
    for t in table:
        fh.write(f"| {t['k']} | {t['N']} | {t['2^N-B used']} | {float(t['ratio']):.4f} |\n")

bad = [t["k"] for t in table if not t["ok"]]
lo = min(table, key=lambda t: t["ratio"])
print(f"k = 3..60: ratio > 1/2 for every k: {not bad}"
      + (f"  (fails for k = {bad})" if bad else "")
      + f";  smallest ratio {float(lo['ratio']):.4f} at k = {lo['k']}")
sys.exit(1 if bad else 0)
