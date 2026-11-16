"""Locate the differing seed of fz_psi block 20500..20999 (kept class): sub-blocks of 25 seeds."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "units"))
sys.path.insert(0, str(HERE.parent))
import b4_gen as b4
import fz_psi_gen as fz

LEAN = [17877647699990448423, 10975485241940375236, 3825213843122744399, 17890298616295533889, 3330339424930150635,
        12439963182230538816, 7909476835609779905, 9576117319261535463, 16556059067888755563, 8718239540770398195,
        997039475281794701, 13096206314057924937, 4138107714777288867, 2175361267900573945, 18082340811794894988,
        6962267412262279660, 12231742892956527105, 17590973700082868124, 18366516037330374542, 15145644809375708466]
for j in range(20):
    seeds = range(20500 + 25 * j, 20500 + 25 * j + 25)
    d = [fz.one(s) for s in seeds]
    if b4.w([x[1] for x in d if x[0] == 0]) != LEAN[j]:
        print("sub-block", j, "differs; kept seeds:")
        for s, x in zip(seeds, d):
            if x[0] == 0:
                t, v, meta = fz.frames(s)
                print("  ", s, meta, x[1])
                if len(sys.argv) > 1 and int(sys.argv[1]) == s:
                    print(t["credit_risk_score"].to_list(), v["credit_risk_score"].to_list())
                    pc, ps = fz.run_slice(t, v)
                    print(pc.rows(), ps.rows())
