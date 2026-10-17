/* Count independent sets of a simple undirected graph on n <= 127 vertices.
 * Vertex sets are 128-bit masks.  Branch-and-reduce: split into connected
 * components; a connected graph of maximum degree <= 2 is a path (F_{m+2}
 * independent sets) or a cycle (Lucas L_m); otherwise branch on a vertex of
 * maximum degree.  Results are memoised on the vertex mask.  Counts are exact
 * (unsigned 128-bit; i(G) <= 2^n < 2^127).
 *   build: gcc -O3 -march=native -shared -fPIC -o libindep.so indep.c       */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned __int128 u128;
typedef uint64_t u64;
static u128 adj[128];
static u128 fib[132], luc[132];
typedef struct { u128 key, val; } entry;
static entry *tab = 0;
static uint32_t *gen = 0, curgen = 1;                 /* entry i is live iff gen[i] == curgen */
static const size_t CAP = (size_t)1 << 22;           /* 4M entries = 128 MB */
static size_t used = 0;

static inline int pc(u128 x) { return __builtin_popcountll((u64)x) + __builtin_popcountll((u64)(x >> 64)); }
static inline int ctz(u128 x) { u64 lo = (u64)x; return lo ? __builtin_ctzll(lo) : 64 + __builtin_ctzll((u64)(x >> 64)); }
static inline size_t hsh(u128 k) { u64 a = (u64)k, b = (u64)(k >> 64); a ^= b * 0x9E3779B97F4A7C15ULL; a ^= a >> 31; a *= 0xBF58476D1CE4E5B9ULL; a ^= a >> 29; return (size_t)a & (CAP - 1); }
static void clear_tab(void) { if (++curgen == 0) { memset(gen, 0, CAP * sizeof *gen); curgen = 1; } used = 0; }
static int get(u128 k, u128 *v) { size_t i = hsh(k); while (gen[i] == curgen) { if (tab[i].key == k) { *v = tab[i].val; return 1; } i = (i + 1) & (CAP - 1); } return 0; }
static void put(u128 k, u128 v) { if (used > CAP * 7 / 10) clear_tab(); size_t i = hsh(k); while (gen[i] == curgen) { if (tab[i].key == k) return; i = (i + 1) & (CAP - 1); } gen[i] = curgen; tab[i].key = k; tab[i].val = v; used++; }

static u128 count(u128 S) {
    if (!S) return 1;
    u128 comp = (u128)1 << ctz(S), fr = comp;
    while (fr) { u128 nb = 0; for (u128 f = fr; f; f &= f - 1) nb |= adj[ctz(f)]; nb &= S & ~comp; comp |= nb; fr = nb; }
    if (comp != S) return count(comp) * count(S & ~comp);
    u128 r; if (get(S, &r)) return r;
    int maxd = -1, mind = 1 << 30, v = -1;
    for (u128 f = S; f; f &= f - 1) { int u = ctz(f), d = pc(adj[u] & S); if (d > maxd) { maxd = d; v = u; } if (d < mind) mind = d; }
    if (maxd <= 2) { int m = pc(S); r = (mind == 2) ? luc[m] : fib[m + 2]; }
    else { u128 b = (u128)1 << v; r = count(S & ~b) + count(S & ~(b | adj[v])); }
    put(S, r); return r;
}

/* adj_lo/adj_hi: n words each; active_lo/hi: vertices to keep (self-looped
 * vertices must already be removed by the caller); result in out[0..1]. */
int count_indep(int n, const u64 *adj_lo, const u64 *adj_hi, u64 active_lo, u64 active_hi, u64 *out) {
    if (n > 127) return -1;
    if (!tab) { tab = malloc(CAP * sizeof(entry)); gen = calloc(CAP, sizeof *gen); if (!tab || !gen) return -2;
        fib[0] = 0; fib[1] = 1; for (int i = 2; i < 132; i++) fib[i] = fib[i-1] + fib[i-2];
        luc[0] = 2; luc[1] = 1; for (int i = 2; i < 132; i++) luc[i] = luc[i-1] + luc[i-2]; }
    clear_tab();
    for (int i = 0; i < n; i++) adj[i] = ((u128)adj_hi[i] << 64) | adj_lo[i];
    u128 S = ((u128)active_hi << 64) | active_lo;
    for (int i = 0; i < n; i++) adj[i] &= S;
    u128 r = count(S);
    out[0] = (u64)r; out[1] = (u64)(r >> 64);
    return 0;
}
