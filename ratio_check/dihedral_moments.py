"""Independent (non-Sage) computation of the quantities in Theorem 1.3 for the
dihedral group D_k of order N = 2k:
    M1 = sum_g [i(F_Q(g)) - i(F_P(g))]                          (Lemma 3.5)
    M2 = sum_{g,h} [i(F_PP) + i(F_QQ) - 2 i(F_PQ)]             (Lemma 4.3)  [optional, expensive]
    P  = sum_g i(F_P(g)),  Q = sum_g i(F_Q(g))
    Bbound = sum_g [i(F_P(g)) + i(F_Q(g)) - i(F_PQ(g,g))] >= 2^N - B   (proof of Lemma 5.1)
Sums over G (resp. G x G) are reduced to orbit representatives of Aut(D_k)
(k >= 3), which acts by rho^a -> rho^{ua}, tau rho^t -> tau rho^{ut+v}.
Independent sets are counted exactly by libindep.so (indep.c).

Usage: python3 dihedral_moments.py K [--m2] [--lib PATH]   -> one JSON line on stdout
"""
import ctypes, json, math, os, sys, time

def load_lib(path):
    lib = ctypes.CDLL(path)
    U64P = ctypes.POINTER(ctypes.c_uint64)
    lib.count_indep.argtypes = [ctypes.c_int, U64P, U64P, ctypes.c_uint64, ctypes.c_uint64, U64P]
    lib.count_indep.restype = ctypes.c_int
    return lib

class Dihedral:
    """Elements 0..k-1 are rho^a; k..2k-1 are tau rho^t.  rho^a tau = tau rho^{-a}."""
    def __init__(self, k):
        self.k, self.n = k, 2 * k
        n = self.n
        def mul(a, b):
            if a < k and b < k:   return (a + b) % k
            if a < k:             return k + (b - k - a) % k
            if b < k:             return k + (a - k + b) % k
            return (b - a) % k
        self.mul = [[mul(a, b) for b in range(n)] for a in range(n)]
        self.inv = [(-a) % k if a < k else a for a in range(n)]
        units = [u for u in range(1, k) if math.gcd(u, k) == 1] if k > 1 else [0]
        self.auts = [tuple([(u * a) % k for a in range(k)] + [k + (u * t + v) % k for t in range(k)])
                     for u in units for v in range(k)]
        for s in self.auts:                      # sanity: every map is an automorphism
            assert all(s[self.mul[a][b]] == self.mul[s[a]][s[b]] for a in range(0, n, max(1, n // 7)) for b in range(n))

    def orbits(self, r):
        """Orbit representatives of Aut(D_k) on G^r (r = 1 or 2), with orbit sizes."""
        n, seen, reps = self.n, set(), []
        tuples = [(g,) for g in range(n)] if r == 1 else [(g, h) for g in range(n) for h in range(n)]
        for t in tuples:
            if t in seen:
                continue
            orb = {tuple(s[x] for x in t) for s in self.auts}
            seen |= orb
            reps.append((t, len(orb)))
        assert sum(sz for _, sz in reps) == n ** r
        return reps

class Graph:
    def __init__(self, D):
        self.D, self.adj, self.loops = D, [0] * D.n, 0
    def _edge(self, x, y):
        if x == y: self.loops |= 1 << x
        else:      self.adj[x] |= 1 << y; self.adj[y] |= 1 << x
    def add_P(self, g):                          # x -- y whenever xy = g
        D = self.D
        for x in range(D.n): self._edge(x, D.mul[D.inv[x]][g])
        return self
    def add_Q(self, h):                          # x -- y whenever x y^{-1} = h
        D = self.D
        for x in range(D.n): self._edge(x, D.mul[D.inv[h]][x])
        return self

class Counter:
    def __init__(self, lib):
        self.lib, self.calls = lib, 0
    def __call__(self, G):
        n = G.D.n
        M = (1 << 64) - 1
        lo = (ctypes.c_uint64 * n)(*[a & M for a in G.adj])
        hi = (ctypes.c_uint64 * n)(*[a >> 64 for a in G.adj])
        active = ((1 << n) - 1) & ~G.loops
        out = (ctypes.c_uint64 * 2)()
        rc = self.lib.count_indep(n, lo, hi, active & M, active >> 64, out)
        assert rc == 0, rc
        self.calls += 1
        return out[0] | (out[1] << 64)

def compute(k, do_m2, libpath):
    t0 = time.time()
    D, cnt = Dihedral(k), Counter(load_lib(libpath))
    res = {"k": k, "N": 2 * k}
    M1 = P = Q = Bb = 0
    for (g,), sz in D.orbits(1):
        iP, iQ = cnt(Graph(D).add_P(g)), cnt(Graph(D).add_Q(g))
        iPQ = cnt(Graph(D).add_P(g).add_Q(g))
        M1 += sz * (iQ - iP); P += sz * iP; Q += sz * iQ; Bb += sz * (iP + iQ - iPQ)
    res.update(M1=M1, P=P, Q=Q, Bbound=Bb)
    if do_m2:
        reps = D.orbits(2)
        M2 = 0
        for (g, h), sz in reps:
            iPP = cnt(Graph(D).add_P(g).add_P(h))
            iQQ = cnt(Graph(D).add_Q(g).add_Q(h))
            iPQ = cnt(Graph(D).add_P(g).add_Q(h))
            M2 += sz * (iPP + iQQ - 2 * iPQ)
        res.update(M2=M2, pair_orbits=len(reps))
    res["seconds"] = round(time.time() - t0, 2)
    res["indep_counts"] = cnt.calls
    return res

if __name__ == "__main__":
    k = int(sys.argv[1])
    lib = sys.argv[sys.argv.index("--lib") + 1] if "--lib" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "libindep.so")
    r = compute(k, "--m2" in sys.argv, lib)
    print(json.dumps({key: (str(v) if isinstance(v, int) and abs(v) > 2**53 else v) for key, v in r.items()}))
