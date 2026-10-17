#!/usr/bin/env python3
"""Check the independent-set formulas for M1 and M2 (Lemmas 3.5 and 4.3), as
implemented in ratio_check/dihedral_moments.py, against brute force over all
4^k subsets of D_k (checks/brute_moments).

    python3 checks/compare_moments_bruteforce.py [KMIN] [KMAX]     (default 3 10)
"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kmin, kmax = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (3, 10)
ok = True
for k in range(kmin, kmax + 1):
    b = json.loads(subprocess.run([os.path.join(ROOT, "checks", "brute_moments"), str(k)],
                                  capture_output=True, text=True, check=True).stdout)
    m = json.loads(subprocess.run([sys.executable, os.path.join(ROOT, "ratio_check", "dihedral_moments.py"), str(k), "--m2"],
                                  capture_output=True, text=True, check=True).stdout)
    good = int(m["M1"]) == b["M1"] and int(m["M2"]) == b["M2"]
    ok &= good
    print(f"   k={k}: M1={b['M1']} M2={b['M2']}  brute force and independent-set formulas agree: {good}")
sys.exit(0 if ok else 1)
