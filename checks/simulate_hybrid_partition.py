"""Re-create the k=30 hybrid partition scheme on a small k and check that it
reproduces the single-process count exactly.
Scheme (as used for k=30): N0 shards at split depth 6; some 'slow' shards are
replaced by 256 subshards (modulus N0*256); some of those by 256 more (N0*256^2);
remaining 'atomic' ones are split hierarchically at a deeper depth (HIER mode).
Usage: simulate_hybrid_partition.py BINARY K"""
import subprocess, sys, re
from fractions import Fraction
BIN, K = sys.argv[1], int(sys.argv[2])
LINE = re.compile(r"task\s+(\d+)/(\d+)\s+partial:\s*(.*?)\s*emptyT=(\d+)")
def run(args):
    out = subprocess.run([BIN] + [str(a) for a in args], capture_output=True, text=True, check=True).stdout
    m = LINE.search(out); vals = [int(v) for v in m.group(3).split()]
    return vals, int(m.group(4))
serial = int(re.search(r"= (\d+)", subprocess.run([BIN, str(K)], capture_output=True, text=True).stdout).group(1))
tot = [0] * K; empty = 0; runs = 0
def add(v):
    global empty, runs
    vals, e = v; runs += 1
    for i, x in enumerate(vals): tot[i] += x
    empty += e
N0, F, S = 200, 256, 6
P0 = {0, 1, 5, 17, 42}                 # replaced at level 1 (includes 0, which owns the top tree)
B1 = {0, 5 + 3 * N0, 17}               # level-1 tasks replaced again at level 2
H2 = {0, 17, 5 + 3 * N0}            # the q=0 children: same ids as their bases (the k=30 situation)
for t in range(N0):
    if t not in P0: add(run([K, N0, t, S]))
N1 = N0 * F
for p in P0:
    for q in range(F):
        t = p + q * N0
        if t not in B1: add(run([K, N1, t, S]))
N2 = N1 * F
for b in B1:
    for q in range(F):
        t = b + q * N1
        if t not in H2: add(run([K, N2, t, S]))
for h in H2:                            # HIER: parent (N2, h, depth 6), children 256 at depth 12
    for c in range(F):
        add(run([K, F, c, 12, N2, h, S]))
ans = K * sum(Fraction(tot[t - 1], t) for t in range(1, K + 1)) + empty
print(f"k={K}: serial={serial}  hybrid-partition={ans}  processes={runs}  match={ans == serial}")
# Direct check of HIER mode for one non-zero parent: its 256 hierarchical children
# must sum to the same partial vector as the parent run as a single task.
p = 17
whole = run([K, N2, p, S])
acc = [0] * K; e = 0
for c in range(F):
    v, ee = run([K, F, c, 12, N2, p, S]); acc = [a + b for a, b in zip(acc, v)]; e += ee
print(f"parent {p}: single task total={sum(whole[0])}  hierarchical sum equal: {(acc, e) == whole}")
