# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""
Cython version of the balanced-subset count for D_k (k <= 31).

In Sage, paste the body of this file into a  %%cython  cell (Sage ships
Cython), or compile it with pyximport / setup.py and import it.
Same algorithm and same conventions as balanced_dihedral.py -- see that file
for the derivation.
"""
from fractions import Fraction
from math import comb

cdef extern int __builtin_popcount(unsigned int) nogil

cdef int K, NSLOT
cdef unsigned int FULL
cdef unsigned int  sl_bit[64]
cdef int           sl_kind[64], sl_v[64], sl_w[64], sl_remT[64]
cdef unsigned long long sl_p2[64]
cdef long long      cnt[64]
cdef unsigned long long acc[64][64]
cdef unsigned long long NODES

cdef inline unsigned int rl(unsigned int m, int s):
    return ((m << s) | (m >> (K - s))) & FULL

cdef void rec(int idx, unsigned int R, unsigned int Rn, unsigned int T, unsigned int Tn,
              unsigned int P, unsigned int D, unsigned int E, unsigned int M, unsigned int N,
              int size, int t):
    global NODES
    cdef int j, v, w, t2, bal
    cdef unsigned int R2, Rn2, T2, Tn2, P2, D2, E2, M2, N2, PE, DE
    for j in range(idx, NSLOT):
        v = sl_v[j]; w = sl_w[j]; t2 = t
        if sl_kind[j] == 0:
            R2 = R | sl_bit[j]; Rn2 = Rn | (<unsigned int>1 << w)
            T2 = T; Tn2 = Tn
            P2 = P | rl(R2, v)
            D2 = D | rl(Rn2, v) | rl(R2, w)
            E2 = E
            M2 = M | rl(T, w)
            N2 = N | rl(T, v)
        else:
            T2 = T | sl_bit[j]; Tn2 = Tn | (<unsigned int>1 << w)
            R2 = R; Rn2 = Rn; P2 = P; D2 = D
            E2 = E | rl(Tn2, v) | rl(T2, w)
            M2 = M | rl(Rn, v)
            N2 = N | rl(R, v)
            t2 = t + 1
        NODES += 1
        PE = P2 | E2; DE = D2 | E2
        if PE == FULL and DE == FULL and M2 == FULL:
            acc[sl_remT[j]][t2] += sl_p2[j]
            continue
        bal = (__builtin_popcount(PE) + __builtin_popcount(M2 | N2)
               == __builtin_popcount(DE) + __builtin_popcount(M2))
        if size + 1 >= K:
            acc[sl_remT[j]][t2] += sl_p2[j]
            if bal == 0:
                cnt[t2] -= 1
            continue
        cnt[t2] += bal
        if j + 1 < NSLOT:
            rec(j + 1, R2, Rn2, T2, Tn2, P2, D2, E2, M2, N2, size + 1, t2)

cdef unsigned long long rot_only(int idx, unsigned int R, unsigned int Rn,
                                 unsigned int P, unsigned int D):
    global NODES
    cdef unsigned long long c = 0
    cdef int i, w
    cdef unsigned int R2, Rn2, P2, D2
    for i in range(idx, K):
        w = (K - i) % K
        R2 = R | (<unsigned int>1 << i); Rn2 = Rn | (<unsigned int>1 << w)
        P2 = P | rl(R2, i)
        D2 = D | rl(Rn2, i) | rl(R2, w)
        NODES += 1
        if P2 == FULL and D2 == FULL:
            c += <unsigned long long>1 << (K - i - 1)
            continue
        c += (__builtin_popcount(P2) == __builtin_popcount(D2))
        if i + 1 < K:
            c += rot_only(i + 1, R2, Rn2, P2, D2)
    return c

def count_balanced_dihedral(int k):
    """Number of subsets A of the dihedral group of order 2k with |AA| = |AA^{-1}|."""
    global K, NSLOT, FULL, NODES
    cdef int i, p, j, q, rr, rt, t, e
    cdef unsigned long long c
    K = k; FULL = (<unsigned int>1 << k) - 1
    p = 0
    for i in range(k):
        sl_kind[p] = 0; sl_v[p] = i; sl_w[p] = (k - i) % k; sl_bit[p] = <unsigned int>1 << i; p += 1
        if i:
            sl_kind[p] = 1; sl_v[p] = i; sl_w[p] = (k - i) % k; sl_bit[p] = <unsigned int>1 << i; p += 1
    NSLOT = p
    for j in range(NSLOT):
        rr = 0; rt = 0
        for q in range(j + 1, NSLOT):
            if sl_kind[q]: rt += 1
            else:          rr += 1
        sl_remT[j] = rt; sl_p2[j] = <unsigned long long>1 << rr
    for i in range(64):
        cnt[i] = 0
        for j in range(64):
            acc[i][j] = 0
    NODES = 0
    cnt[1] = 1
    rec(0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1)
    tot = [int(cnt[i]) for i in range(64)]
    for rt in range(k + 1):
        for t in range(1, k + 1):
            a = int(acc[rt][t])
            if a:
                for e in range(rt + 1):
                    tot[t + e] += a * comb(rt, e)
    total = k * sum(Fraction(tot[t], t) for t in range(1, k + 1))
    c = rot_only(0, 0, 0, 0, 0)
    total += 1 + int(c)
    assert total.denominator == 1
    return int(total)

def nodes():
    return int(NODES)
