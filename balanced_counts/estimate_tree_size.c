/* Fraction of subsets of D_k that are "unsaturated" (AA != G or AA^{-1} != G).
 * The pruned DFS must visit every unsaturated subset, so #nodes >= #unsaturated;
 * this gives a cheap way to extrapolate the search-tree size to large k.
 * Exact full enumeration for small k, Monte-Carlo for large k. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
typedef unsigned int u32; typedef unsigned long long u64;
static int K; static u32 FULL;
static inline u32 rl(u32 m,int s){return ((m<<s)|(m>>(K-s)))&FULL;}

static int unsat(u32 R,u32 T){
    u32 P=0,D=0,E=0,M=0,Nx=0, Rn=0,Tn=0;
    for(int i=0;i<K;i++){ if(R>>i&1) Rn|=1u<<((K-i)%K); if(T>>i&1) Tn|=1u<<((K-i)%K); }
    for(int i=0;i<K;i++) if(R>>i&1){ P|=rl(R,i); D|=rl(Rn,i); M|=rl(T,(K-i)%K); Nx|=rl(T,i);}
    for(int i=0;i<K;i++) if(T>>i&1)  E|=rl(Tn,i);
    return !((P|E)==FULL && (D|E)==FULL && M==FULL);
}
static u64 rs=88172645463325252ULL;
static inline u64 rnd(void){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}

int main(int argc,char**argv){
    int k0=atoi(argv[1]),k1=atoi(argv[2]); u64 samples= argc>3?strtoull(argv[3],0,10):0;
    for(K=k0;K<=k1;K++){
        FULL=(1u<<K)-1;
        if(!samples){
            u64 c=0; for(u32 R=0;R<=FULL;R++) for(u32 T=0;T<=FULL;T++) c+=unsat(R,T);
            printf("k=%2d exact unsaturated=%llu  frac=%.6g   4^k=%.4g\n",K,c,(double)c/((double)FULL+1)/((double)FULL+1),(double)(FULL+1.0)*(FULL+1.0));
        } else {
            u64 c=0; for(u64 s=0;s<samples;s++){ u32 R=rnd()&FULL,T=rnd()&FULL; c+=unsat(R,T);}
            double p=(double)c/samples;
            printf("k=%2d MC unsaturated frac=%.6g (+-%.2g)  => count=%.4g\n",K,p,
                   1.96*sqrt(p*(1-p)/samples), p*(double)(FULL+1.0)*(FULL+1.0));
        }
        fflush(stdout);
    }
    return 0;
}
