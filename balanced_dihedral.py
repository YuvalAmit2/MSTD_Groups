"""
Counting balanced subsets of the dihedral group D_k  (|D_k| = n = 2k).

A subset A of a group G is *balanced* when |AA| = |AA^{-1}|.

KEEP THIS IN A PLAIN .py FILE and import it from Sage:
Sage's preparser turns integer literals into Sage Integers, whose bitwise
operations are one to two orders of magnitude slower than machine ints.
Files imported with `from balanced_dihedral import ...` are NOT preparsed.

--------------------------------------------------------------------------
The reduction this code is built on
--------------------------------------------------------------------------
Write D_k = <rho, tau | rho^k = tau^2 = 1, tau rho tau = rho^{-1}> and split
a subset A into its rotations and its reflections:

    A = { rho^a : a in R }  u  { tau rho^t : t in T },     R, T subseteq Z_k.

From  rho^a rho^b = rho^{a+b},  rho^a (tau rho^b) = tau rho^{b-a},
      (tau rho^a) rho^b = tau rho^{a+b},  (tau rho^a)(tau rho^b) = rho^{b-a},
and (tau rho^a)^{-1} = tau rho^a, one gets, with all sums/differences taken
in Z_k,

    P = R+R,  D = R-R,  E = T-T,  M = T-R,  N = T+R

    AA      = { rho^x : x in P u E } u { tau rho^y : y in M u N }
    AA^{-1} = { rho^x : x in D u E } u { tau rho^y : y in M }

    A is balanced  <=>  |P u E| + |M u N| = |D u E| + |M|.

So the whole computation lives in Z_k and every set is a k-bit mask; sumsets
are unions of cyclic shifts, i.e. single machine words.

--------------------------------------------------------------------------
The three things that make this fast
--------------------------------------------------------------------------
1. Bitmasks.  |R| * |S| pairwise products become |R| shift-or's.
2. Incremental DFS.  Adding one element to R or T updates P, D, E, M, N with
   O(1) word operations, e.g. (R u {x}) + (R u {x}) = (R+R) u (x + (R u {x})).
3. Two subtree shortcuts, which is where the real asymptotic win is:
   (a) if P u E = D u E = M = Z_k then AA = AA^{-1} = G, and the same holds
       for *every* superset of A, so 2^rem subsets are counted at once;
   (b) |A| >= n/2 makes every strict superset balanced (backstop; rarely fires
       before (a) does).
   Cost drops from Theta(n^2 4^k) to about 3.15^k.
4. Aut(D_k) contains tau rho^t -> tau rho^{t+v}, so only pairs with 0 in T
   need enumerating:  #balanced with T nonempty = k * sum_{0 in T} 1/|T|.
   Another factor of ~2.7 (unsaturated sets have |T| ~ 0.35k on average,
   not k/2).
"""

from fractions import Fraction

__all__ = ["count_balanced_dihedral", "count_balanced_dihedral_naive",
           "dihedral_element_order_is_rotations_first"]


def count_balanced_dihedral(k):
    """Number of subsets A of D_k (order 2k) with |AA| = |AA^{-1}|."""
    k = int(k)
    full = (1 << k) - 1
    nslot = 2 * k - 1

    # slot table: (kind, v, w, bit, remT, 2^remR); reflection 0 is forced in.
    slots = []
    for i in range(k):
        slots.append((0, i, (k - i) % k, 1 << i))
        if i:
            slots.append((1, i, (k - i) % k, 1 << i))
    tab = []
    for j in range(nslot):
        rem = slots[j + 1:]
        rt = sum(1 for s in rem if s[0])
        tab.append(slots[j] + (rt, 1 << (len(rem) - rt)))

    cnt = [0] * (2 * k + 2)          # cnt[t] : balanced pairs with 0 in T, |T| = t
    acc = [[0] * (k + 2) for _ in range(k + 2)]   # pooled saturated subtrees

    def rec(idx, R, Rn, T, Tn, P, D, E, M, N, size, t):
        for j in range(idx, nslot):
            kind, v, w, bit, remT, p2 = tab[j]
            if kind == 0:
                R2 = R | bit
                Rn2 = Rn | (1 << w)
                P2 = P | (((R2 << v) | (R2 >> (k - v))) & full)
                D2 = D | (((Rn2 << v) | (Rn2 >> (k - v))) & full) \
                       | (((R2 << w) | (R2 >> (k - w))) & full)
                E2 = E
                M2 = M | (((T << w) | (T >> (k - w))) & full)
                N2 = N | (((T << v) | (T >> (k - v))) & full)
                T2, Tn2, t2 = T, Tn, t
            else:
                T2 = T | bit
                Tn2 = Tn | (1 << w)
                E2 = E | (((Tn2 << v) | (Tn2 >> (k - v))) & full) \
                       | (((T2 << w) | (T2 >> (k - w))) & full)
                M2 = M | (((Rn << v) | (Rn >> (k - v))) & full)
                N2 = N | (((R << v) | (R >> (k - v))) & full)
                R2, Rn2, P2, D2, t2 = R, Rn, P, D, t + 1
            PE = P2 | E2
            DE = D2 | E2
            if PE == full and DE == full and M2 == full:
                acc[remT][t2] += p2                 # AA = AA^{-1} = G, hereditary
                continue
            bal = (PE.bit_count() + (M2 | N2).bit_count()
                   == DE.bit_count() + M2.bit_count())
            if size + 1 >= k:                        # |A| >= n/2
                acc[remT][t2] += p2
                if not bal:
                    cnt[t2] -= 1
                continue
            if bal:
                cnt[t2] += 1
            if j + 1 < nslot:
                rec(j + 1, R2, Rn2, T2, Tn2, P2, D2, E2, M2, N2, size + 1, t2)

    cnt[1] += 1                                      # A = {tau}
    rec(0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1)

    # expand the pooled subtrees, then undo the 1/|T| weighting
    from math import comb
    tot = list(cnt)
    for rt in range(k + 1):
        for t in range(1, k + 1):
            a = acc[rt][t]
            if a:
                for e in range(rt + 1):
                    tot[t + e] += a * comb(rt, e)
    total = sum(Fraction(tot[t], t) for t in range(1, k + 1)) * k

    # T empty: A sits inside the rotation subgroup, |R+R| vs |R-R| in Z_k
    def rot_only(idx, R, Rn, P, D):
        c = 0
        for i in range(idx, k):
            w = (k - i) % k
            R2 = R | (1 << i)
            Rn2 = Rn | (1 << w)
            P2 = P | (((R2 << i) | (R2 >> (k - i))) & full)
            D2 = D | (((Rn2 << i) | (Rn2 >> (k - i))) & full) \
                   | (((R2 << w) | (R2 >> (k - w))) & full)
            if P2 == full and D2 == full:
                c += 1 << (k - i - 1)
                continue
            if P2.bit_count() == D2.bit_count():
                c += 1
            if i + 1 < k:
                c += rot_only(i + 1, R2, Rn2, P2, D2)
        return c

    total += 1 + rot_only(0, 0, 0, 0, 0)             # the empty set, and T = {}
    assert total.denominator == 1
    return int(total)


# ---------------------------------------------------------------- checking --
def count_balanced_dihedral_naive(k):
    """O(4^k k^2) reference: every subset, multiplication tables, no shortcuts."""
    k = int(k)
    n = 2 * k
    mul = [[0] * n for _ in range(n)]
    for a in range(n):
        for b in range(n):
            if a < k and b < k:    mul[a][b] = (a + b) % k
            elif a < k:            mul[a][b] = k + (b - k - a) % k
            elif b < k:            mul[a][b] = k + (a - k + b) % k
            else:                  mul[a][b] = (b - a) % k
    inv = [(-i) % k if i < k else i for i in range(n)]
    div = [[mul[a][inv[b]] for b in range(n)] for a in range(n)]
    total = 0
    for m in range(1 << n):
        A = [i for i in range(n) if m >> i & 1]
        if len({mul[x][y] for x in A for y in A}) == len({div[x][y] for x in A for y in A}):
            total += 1
    return total


def dihedral_element_order_is_rotations_first(G, k):
    """Run this in Sage before trusting any code that assumes list(G)[:k] are
    the rotations -- the original algorithm's AA^{-1} formula is only valid
    under that assumption, and Sage does not promise it."""
    els = list(G)
    return all(els[i].order() != 2 or els[i].is_one() for i in range(k)) and \
           len({els[i] * els[j] for i in range(k) for j in range(k)}) <= k


if __name__ == "__main__":
    import sys, time
    known = {1: 4, 2: 16, 3: 46, 4: 184, 5: 684, 6: 2830, 7: 11008, 8: 46584,
             9: 192250, 10: 806396, 11: 3328472, 12: 13788886, 13: 56881972,
             14: 233244664, 15: 957162366}
    sys.setrecursionlimit(10000)
    for k in range(1, 15):
        t = time.time(); v = count_balanced_dihedral(k); dt = time.time() - t
        tag = "OK" if known.get(k) == v else "??"
        print(f"k={k:2d}  {v:14d}  {dt:8.3f}s  {tag}", flush=True)
