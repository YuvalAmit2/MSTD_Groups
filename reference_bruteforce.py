"""Independent brute force + a transcription of the original algorithm.

Element encoding: 0..k-1  = rho^i          (rotations)
                  k..2k-1 = tau*rho^(i-k)  (reflections)
This is exactly the ordering the original code ASSUMES list(DihedralGroup(k)) has.
"""
from itertools import combinations
from math import comb

def tables(k):
    n = 2*k
    mul = [[0]*n for _ in range(n)]
    for a in range(n):
        for b in range(n):
            if a < k and b < k:      v = (a+b) % k                 # rho^a rho^b
            elif a < k and b >= k:   v = k + (b-k-a) % k           # rho^a tau rho^b = tau rho^{b-a}
            elif a >= k and b < k:   v = k + (a-k+b) % k           # tau rho^a rho^b
            else:                    v = (b-k-(a-k)) % k           # tau rho^a tau rho^b = rho^{b-a}
            mul[a][b] = v
    inv = [(-i) % k if i < k else i for i in range(n)]
    div = [[mul[a][inv[b]] for b in range(n)] for a in range(n)]
    return mul, div

def brute(k):
    """Enumerate every one of the 2^(2k) subsets, no shortcuts at all."""
    n = 2*k
    mul, div = tables(k)
    total = 0
    for m in range(1 << n):
        A = [i for i in range(n) if m >> i & 1]
        PP = {mul[x][y] for x in A for y in A}
        QQ = {div[x][y] for x in A for y in A}
        if len(PP) == len(QQ):
            total += 1
    return total

def original(k):
    """The user's algorithm, with the group built explicitly."""
    n = 2*k
    mul, div = tables(k)
    answer = sum(comb(n, j) for j in range(k+1, n+1))
    for r in range(k+1):
        for s in range(k-r+1):
            for R in combinations(range(k), r):
                RR  = {mul[a][b] for a in R for b in R}
                RRh = {div[a][b] for a in R for b in R}
                for S in combinations(range(k, n), s):
                    SS = {mul[a][b] for a in S for b in S}
                    RS = {mul[a][b] for a in R for b in S}
                    SR = {mul[a][b] for a in S for b in R}
                    if len(RR|SS|RS|SR) == len(RRh|SS|RS):
                        answer += 1
    return answer

if __name__ == "__main__":
    import sys, time
    for k in range(1, 9):
        t = time.time(); b = brute(k); tb = time.time()-t
        t = time.time(); o = original(k); to = time.time()-t
        print(f"k={k:2d} n={2*k:2d} brute={b:12d} ({tb:6.2f}s)  original={o:12d} ({to:6.2f}s)  {'OK' if b==o else 'MISMATCH'}")
        sys.stdout.flush()
