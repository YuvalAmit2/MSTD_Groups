"""For each original k=30 shard (modulus 20000) that finished on its own AND was
also re-split into 256 level-1 subshards (modulus 5,120,000), check that the
subshards' partial vectors sum exactly to the original shard's partial vector."""
import os, re, sys
root = sys.argv[1]
LINE = re.compile(r"k=\s*(\d+)\s+task\s+(\d+)/(\d+)\s+partial:\s*(.*?)\s*emptyT=(\d+)\s+seconds=([\d.]+)")
def read(path):
    with open(path) as fh:
        m = [LINE.search(l) for l in fh]; m = [x for x in m if x]
    assert len(m) == 1, path
    m = m[0]
    return int(m.group(2)), int(m.group(3)), [int(v) for v in m.group(4).split()] + [int(m.group(5))]
N0, F = 20000, 256
parents = [0, 1, 2, 54, 55, 7700, 7701, 7702, 7720, 7754, 7755, 7773, 15010, 15400, 15401, 15402, 15420, 15454, 15455, 15473]
for p in parents:
    orig = os.path.join(root, "out_k30_n20000", f"shard_{p}.txt")
    if not os.path.exists(orig):
        continue
    t, n, ov = read(orig); assert (t, n) == (p, N0)
    acc = [0] * len(ov); missing = 0
    for q in range(F):
        f = os.path.join(root, "out_k30_sub256", f"sub_{p}_{q}.txt")
        if not os.path.exists(f):
            missing += 1; continue
        t2, n2, v = read(f); assert (t2, n2) == (p + q * N0, N0 * F)
        acc = [a + b for a, b in zip(acc, v)]
    print(f"parent {p:5d}: subshards missing={missing}  sums equal original: {acc == ov}")
