/* ===========================================================================
 * Balanced subsets of the dihedral group D_k  (|D_k| = n = 2k),  k <= 31.
 * A is balanced iff |AA| = |AA^{-1}|.
 *
 *   A = {rho^a : a in R} u {tau rho^t : t in T},   R, T subseteq Z_k
 *   P = R+R,  D = R-R,  E = T-T,  M = T-R,  N = T+R      (all inside Z_k)
 *
 *   AA      = (P u E) rotations + (M u N) reflections
 *   AA^{-1} = (D u E) rotations +    M    reflections
 *   balanced  <=>  |P u E| + |M u N| = |D u E| + |M|
 *
 * Every set is a k-bit mask; a sumset is a union of cyclic shifts, and adding
 * one element to R or T updates all five masks in O(1) word operations.
 *
 * Two hereditary shortcuts collapse whole subtrees:
 *   - P u E = D u E = M = Z_k  =>  AA = AA^{-1} = G for A and all supersets
 *   - |A| >= n/2               =>  every strict superset is balanced
 * and Aut(D_k) > (tau rho^t -> tau rho^{t+v}) lets us enumerate only pairs
 * with 0 in T, undoing the weighting with
 *      #balanced (T nonempty) = k * sum_{0 in T, balanced} 1/|T|.
 * T = empty is handled by a separate 2^k pass (|R+R| vs |R-R| in Z_k).
 *
 * Build:  gcc -O3 -march=native -funroll-loops -o balanced_dihedral balanced_dihedral.c
 * Serial: ./balanced_dihedral K
 * Shard:  ./balanced_dihedral K NTASKS TASKID SPLITDEPTH     (see run_parallel.py)
 *         SPLITDEPTH ~ 6 gives millions of independent subtrees, round-robin
 *         over the tasks; every task repeats the (tiny) tree above that depth
 *         but only task 0 counts it.
 * ======================================================================== */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef unsigned int u32;
typedef unsigned long long u64;
typedef unsigned __int128 u128;

static int K, NSLOT, SPLIT = 12, NTASK = 1, TASKID = 0;
static u32 FULL;
static int kind_[64], sv_[64], sw_[64], remR_[64], remT_[64];
static u32 bit_[64];
static u64 pow2remR_[64];
static __int128 cnt[64];     /* cnt[t] = #balanced pairs, 0 in T, |T| = t   */
static u128 acc[64][64];     /* acc[remT][t] = pooled 2^remR from pruned subtrees */
static u64 prefix_ctr;

static inline u32 rl(u32 m, int s) { return ((m << s) | (m >> (K - s))) & FULL; }
#define PC __builtin_popcount

/* ---------- part (ii): T nonempty, normalised so that 0 in T ------------- */
static void rec(int idx, u32 R, u32 Rn, u32 T, u32 Tn,
                u32 P, u32 D, u32 E, u32 M, u32 Nx, int size, int t)
{
    for (int j = idx; j < NSLOT; j++) {
        u32 R2, Rn2, T2, Tn2, P2, D2, E2, M2, N2;
        const int v = sv_[j], w = sw_[j];
        int t2 = t;
        if (kind_[j] == 0) {
            R2 = R | bit_[j];  Rn2 = Rn | (1u << w);  T2 = T;  Tn2 = Tn;
            P2 = P | rl(R2, v);
            D2 = D | rl(Rn2, v) | rl(R2, w);
            E2 = E;
            M2 = M | rl(T, w);
            N2 = Nx | rl(T, v);
        } else {
            T2 = T | bit_[j];  Tn2 = Tn | (1u << w);  R2 = R;  Rn2 = Rn;
            P2 = P;  D2 = D;
            E2 = E | rl(Tn2, v) | rl(T2, w);
            M2 = M | rl(Rn, v);
            N2 = Nx | rl(R, v);
            t2 = t + 1;
        }
        const u32 PE = P2 | E2, DE = D2 | E2;
        const int own = (size + 1 > SPLIT) | (TASKID == 0); /* above the split depth: task 0 only */
        if (PE == FULL && DE == FULL && M2 == FULL) {   /* AA = AA^-1 = G, hereditary */
            if (own) acc[remT_[j]][t2] += pow2remR_[j];
            continue;
        }
        const int bal = (PC(PE) + PC(M2 | N2) == PC(DE) + PC(M2));
        if (size + 1 >= K) {                            /* |A| >= n/2: supersets balanced */
            if (own) { acc[remT_[j]][t2] += pow2remR_[j]; cnt[t2] += bal ? 0 : -1; }
            continue;
        }
        if (own) cnt[t2] += bal;
        if (j + 1 < NSLOT) {
            if (size + 1 == SPLIT) { if (prefix_ctr++ % NTASK != (u64)TASKID) continue; }
            rec(j + 1, R2, Rn2, T2, Tn2, P2, D2, E2, M2, N2, size + 1, t2);
        }
    }
}

/* ---------- part (i): T empty, i.e. A inside the rotation subgroup ------- */
static u64 rot_only(int idx, u32 R, u32 Rn, u32 P, u32 D)
{
    u64 c = 0;
    for (int i = idx; i < K; i++) {
        u32 R2 = R | (1u << i), Rn2 = Rn | (1u << ((K - i) % K));
        u32 P2 = P | rl(R2, i), D2 = D | rl(Rn2, i) | rl(R2, (K - i) % K);
        if (P2 == FULL && D2 == FULL) { c += 1ULL << (K - i - 1); continue; }
        c += (PC(P2) == PC(D2));
        if (i + 1 < K) c += rot_only(i + 1, R2, Rn2, P2, D2);
    }
    return c;
}

int main(int argc, char **argv)
{
    K = argc > 1 ? atoi(argv[1]) : 8;
    NTASK  = argc > 2 ? atoi(argv[2]) : 1;
    TASKID = argc > 3 ? atoi(argv[3]) : 0;
    SPLIT  = argc > 4 ? atoi(argv[4]) : 12;
    if (NTASK == 1) SPLIT = 1 << 30;
    FULL = (1u << K) - 1;

    /* slot order: interleave rotations and reflections; reflection 0 is forced in */
    int p = 0;
    for (int i = 0; i < K; i++) {
        kind_[p] = 0; sv_[p] = i; sw_[p] = (K - i) % K; bit_[p] = 1u << i; p++;
        if (i) { kind_[p] = 1; sv_[p] = i; sw_[p] = (K - i) % K; bit_[p] = 1u << i; p++; }
    }
    NSLOT = p;                                     /* = 2k-1 */
    for (int j = 0; j < NSLOT; j++) {
        int rr = 0, rt = 0;
        for (int q = j + 1; q < NSLOT; q++) { if (kind_[q]) rt++; else rr++; }
        remR_[j] = rr; remT_[j] = rt; pow2remR_[j] = 1ULL << rr;
    }

    struct timespec a, b; clock_gettime(CLOCK_MONOTONIC, &a);
    memset(cnt, 0, sizeof cnt); memset(acc, 0, sizeof acc);
    /* start with T = {0}: E = {0}, everything else empty, |A| = 1 */
    if (TASKID == 0) cnt[1] += 1;                  /* A = {tau} itself is balanced */
    rec(0, 0, 0, 1u, 1u, 0, 0, 1u, 0, 0, 1, 1);
    u64 empty_T = (NTASK == 1 || TASKID == 0) ? 1 + rot_only(0, 0, 0, 0, 0) : 0;
    clock_gettime(CLOCK_MONOTONIC, &b);

    /* expand pooled subtree counts, C(remT, extra reflections) */
    static u128 C[64][64];
    for (int i = 0; i < 64; i++) { C[i][0] = 1; for (int j = 1; j <= i; j++) C[i][j] = C[i-1][j-1] + C[i-1][j]; }
    static __int128 tot[64];
    for (int t = 1; t <= K; t++) tot[t] = cnt[t];
    for (int rt = 0; rt <= K; rt++)
        for (int t = 1; t <= K; t++)
            if (acc[rt][t])
                for (int e = 0; e <= rt; e++) tot[t + e] += (__int128)(acc[rt][t] * C[rt][e]);

    /* answer = #(T empty) + k * sum_t tot[t]/t   (exact via a common denominator) */
    u128 L = 1;
    for (int t = 1; t <= K; t++) { u128 g = L, h = t; while (h) { u128 r = g % h; g = h; h = r; } L = L / g * t; }
    __int128 s = 0;
    for (int t = 1; t <= K; t++) s += tot[t] * (__int128)(L / t);
    __int128 ans = (__int128)K * s / (__int128)L + empty_T;

    double sec = (b.tv_sec-a.tv_sec) + 1e-9*(b.tv_nsec-a.tv_nsec);
    if (NTASK == 1) {
        printf("balanced subsets of D_%d = %llu\n", K, (u64)ans);
        printf("  k = %d   %.1f core-seconds\n", K, sec);
    } else {
        printf("k=%2d task %d/%d  partial: ", K, TASKID, NTASK);
        for (int t = 1; t <= K; t++) printf("%lld ", (long long)tot[t]);
        printf(" emptyT=%llu seconds=%.3f\n", empty_T, sec);
    }
    return 0;
}
