/* Brute-force M1 = sum_A d(A), M2 = sum_A d(A)^2 and B = #{d(A)=0} over all 4^k
 * subsets A of D_k, with d(A) = |AA| - |AA^{-1}|.  Same element-by-element
 * left multiplication as brute_dihedral.c.  Usage: brute_moments K  (k <= 14) */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned int u32; typedef unsigned long long u64; typedef long long i64;
static int K; static u32 FULL;
static inline u32 sh(u32 m, int s) { s %= K; if (s < 0) s += K; if (!s) return m; return ((m << s) | (m >> (K - s))) & FULL; }
static u32 neg(u32 m) { u32 r = 0; for (int i = 0; i < K; i++) if (m >> i & 1) r |= 1u << ((K - i) % K); return r; }
int main(int argc, char **argv) {
    K = atoi(argv[1]); FULL = (1u << K) - 1;
    i64 S1 = 0; u64 S2 = 0, B = 0;
    for (u64 RR = 0; RR <= FULL; RR++) {
        u32 R = (u32)RR, Rinv = neg(R);
        for (u64 TT = 0; TT <= FULL; TT++) {
            u32 T = (u32)TT, PR = 0, PT = 0, QR = 0, QT = 0;
            for (int a = 0; a < K; a++) if (R >> a & 1) { PR |= sh(R, a); PT |= sh(T, -a); QR |= sh(Rinv, a); QT |= sh(T, -a); }
            for (int s = 0; s < K; s++) if (T >> s & 1) { PT |= sh(R, s); PR |= sh(T, -s); QT |= sh(Rinv, s); QR |= sh(T, -s); }
            int d = __builtin_popcount(PR) + __builtin_popcount(PT) - __builtin_popcount(QR) - __builtin_popcount(QT);
            S1 += d; S2 += (u64)(d * d); B += (d == 0);
        }
    }
    printf("{\"k\": %d, \"M1\": %lld, \"M2\": %llu, \"B\": %llu}\n", K, S1, S2, B);
    return 0;
}
