/* Independent brute-force count of balanced subsets of D_k (|D_k| = 2k).
 * No pruning, no symmetry reduction, no sumset decomposition: for every subset
 * A = (R rotations, T reflections) we form AA = U_{x in A} xA and
 * AA^{-1} = U_{x in A} xA^{-1} by left multiplication, element by element.
 * Convention: rot a = rho^a, ref t = tau rho^t, rho^a tau = tau rho^{-a}:
 *   rot a * rot b = rot(a+b)      rot a * ref b = ref(b-a)
 *   ref s * rot b = ref(s+b)      ref s * ref b = rot(b-s)
 * Usage: brute_dihedral K [RSTART RSTEP]   (iterate R = RSTART, RSTART+RSTEP, ...)
 */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned int u32; typedef unsigned long long u64;
static int K; static u32 FULL;
static inline u32 sh(u32 m, int s) { s %= K; if (s < 0) s += K; if (!s) return m; return ((m << s) | (m >> (K - s))) & FULL; }
static u32 neg(u32 m) { u32 r = 0; for (int i = 0; i < K; i++) if (m >> i & 1) r |= 1u << ((K - i) % K); return r; }
int main(int argc, char **argv) {
    K = atoi(argv[1]); FULL = (K == 32) ? 0xffffffffu : ((1u << K) - 1);
    u64 r0 = argc > 2 ? strtoull(argv[2], 0, 10) : 0, rs = argc > 3 ? strtoull(argv[3], 0, 10) : 1;
    u64 count = 0;
    for (u64 RR = r0; RR <= FULL; RR += rs) {
        u32 R = (u32)RR, Rinv = neg(R);
        for (u64 TT = 0; TT <= FULL; TT++) {
            u32 T = (u32)TT;
            u32 PR = 0, PT = 0, QR = 0, QT = 0;           /* AA and AA^{-1}, split rot/ref */
            for (int a = 0; a < K; a++) if (R >> a & 1) {  /* x = rot a */
                PR |= sh(R, a);    PT |= sh(T, -a);         /* x*A        */
                QR |= sh(Rinv, a); QT |= sh(T, -a);         /* x*A^{-1}   */
            }
            for (int s = 0; s < K; s++) if (T >> s & 1) {  /* x = ref s */
                PT |= sh(R, s);    PR |= sh(T, -s);
                QT |= sh(Rinv, s); QR |= sh(T, -s);
            }
            if (__builtin_popcount(PR) + __builtin_popcount(PT) ==
                __builtin_popcount(QR) + __builtin_popcount(QT)) count++;
        }
    }
    printf("k=%d rstart=%llu rstep=%llu balanced=%llu\n", K, r0, rs, count);
    return 0;
}
