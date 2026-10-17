"""Check the numerical claims the paper leaves to the reader ("one can check").
All comparisons are done with mpmath at 60 significant digits."""
from mpmath import mp, mpf, sqrt, log, power
mp.dps = 60

# --- constants used in Sections 3-6 ---------------------------------------
c = {
 "7^(1/4) < 1.68":            power(7, mpf(1)/4) < mpf("1.68"),
 "19^(1/6) < 1.68":           power(19, mpf(1)/6) < mpf("1.68"),
 "3^(1/4)*7^(1/8) < 1.68":    power(3, mpf(1)/4) * power(7, mpf(1)/8) < mpf("1.68"),
 "1.68 < sqrt(3)":            mpf("1.68") < sqrt(3),
 "7^(1/4) < sqrt(3)":         power(7, mpf(1)/4) < sqrt(3),
 "7^(1/4) < 19^(1/6)":        power(7, mpf(1)/4) < power(19, mpf(1)/6),
 "7^(-1/4)+7^(-1/2) < 1":     power(7, mpf(-1)/4) + power(7, mpf(-1)/2) < 1,
 "2*7^(-1/4) > 1":            2 * power(7, mpf(-1)/4) > 1,
 "sqrt(2) < 7^(3/8)":         sqrt(2) < power(7, mpf(3)/8),
}
for name, ok in c.items():
    print(f"{'OK ' if ok else 'FAIL'} {name}")

# --- Theorem 6.2: explicit threshold for dihedral groups --------------------
def dihedral_lhs(k):
    k = mpf(k); a = power(3, k); b = power(mpf("1.68"), 2 * k); d = mpf(32) / 7 * k * (2 * k - 1) * power(19, k / 3)
    if int(k) % 2 == 0:
        num = ((k - 1) * a - (2 * k - 2) * b) ** 2; U = (k + 3) * a + (3 * k - 3) * b
    else:
        num = ((k - 1) * a - (2 * k - 1) * b) ** 2; U = (k + 1) * a + (3 * k - 1) * b
    return num / (U * (U + d))
bad_even = [k for k in range(4, 4001, 2) if dihedral_lhs(k) <= mpf(1) / 2]
bad_odd = [k for k in range(3, 4001, 2) if dihedral_lhs(k) <= mpf(1) / 2]
print(f"(6.14) even k: largest k <= 4000 with LHS <= 1/2: {max(bad_even)}  -> holds for all even k in [{max(bad_even)+2}, 4000]")
print(f"(6.15) odd  k: largest k <= 4000 with LHS <= 1/2: {max(bad_odd)}  -> holds for all odd  k in [{max(bad_odd)+2}, 4000]")
print(f"   LHS at k=60,61,62: {float(dihedral_lhs(60)):.5f} {float(dihedral_lhs(61)):.5f} {float(dihedral_lhs(62)):.5f};  at k=4000: {float(dihedral_lhs(4000)):.8f}")

# --- Lemma 6.1 sharpening: (9/7) 7^{N/4} <= 19^{N/6} iff N >= N0 ------------
N0 = log(mpf(9) / 7) / (log(19) / 6 - log(7) / 4)
print(f"(9/7)*7^(N/4) <= 19^(N/6)  iff  N >= {float(N0):.3f}  (so for all D_k with k >= 30)")

# --- Theorem 6.6 (abelian groups): h(N) > 0 for N >= 171 ---------------------
def h(N):
    N = mpf(N)
    u = mpf(1) / 6 + 2 * power(mpf(7) / 9, N / 4)
    v = 2 * (N - 1) * (power(mpf(19) / 27, N / 6) + power(mpf(7) / 9, N / 4))
    return u * u - 6 * u + 1 - v * (1 + u)
mp.dps = 400   # differences of h are below 1e-60 for large N
neg = [N for N in range(12, 5001) if h(N) <= 0]
inc = all(h(N + 1) > h(N) for N in range(12, 5000))
print(f"h(N) <= 0 for N in [12, 5000] exactly when N <= {max(neg)};  h increasing on [12, 5000]: {inc};  h(170)={float(h(170)):.5f}, h(171)={float(h(171)):.5f}")
# M1 < 0 step in Theorem 6.6: N (7/9)^{N/4} - 3 < 0 for N >= 171
print(f"N*(7/9)^(N/4) < 3 for all N in [171, 5000]: {all(N * power(mpf(7)/9, mpf(N)/4) < 3 for N in range(171, 5001))}")
