"""fz8, second part: the 150 targeted cases of fz5 (work/fz5_hl_groups.tcases.json), the fuzzer's three
named cases, the measured example and the probes of 2026-11-18, on def:_hl_groups after the change.
Prints the Lean term (eval_decl item def:zz_carrier_e, decl pr_ints) and the expected value: the
number of cases and the digest of fz8_hl_q_gen.hs over the outputs, folded in order.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz8_hl_q_named.py
"""
import json
from pathlib import Path
from credit_risk import sas_compat as sc
W = Path(__file__).resolve().parent.parent / "work"
P = 2305843009213693951
def hs(r):
    x = len(r)
    for v in r: x = (x * 1000003 + v % P) % P
    return x
T = json.loads((W / "fz5_hl_groups.tcases.json").read_text())
cases = [(c["blocks"], c["n"], c["g"]) for c in T]
cases += [([1, 18014398509481985], 9007199254740992, 1), ([7, 5, 7, 10**20], 10**20 + 19, 2),
          ([1, 18014398509481985, 7, 1], 9007199254740993, 1),
          ([221269493858733060, 2, 10**18], 2212694938587330714, 10),
          ([5], 10**310, 10**300), ([1, 2], 10**310, 10**300), ([1, 2**64 + 2**11 + 1], 2**63 + 2048, 1),
          ([3, 4], 0, 10**400), ([3, 4, 5], -7, -10**400)]
for k in (80, 200, 1000):
    cases.append(([1, 2**k + 2**(k - 53) + 1], 2**(k - 1) + 2**(k - 53), 1))
D = 0
for bl, n, g in cases:
    D = (D * 1000003 + hs(sc._hl_groups(list(bl), n, g))) % P
def lit(x):
    if abs(x) >= 10**30 and abs(x) == 10**(len(str(abs(x))) - 1):
        return f"({'-' if x < 0 else ''}(10 : Int) ^ {len(str(abs(x))) - 1})"
    return f"({x})"
body = ", ".join(f"([{', '.join(lit(b) for b in bl)}], {lit(n)}, {lit(g)})" for bl, n, g in cases)
print(f"(let P : Int := {P}\n  let hs : List Int → Int := fun (r : List Int) => r.foldl (fun (x v : Int) => (x * 1000003 + v % P) % P) (r.length : Int)\n"
      f"  let cs : List (List Int × Int × Int) := [{body}]\n"
      f"  [(cs.length : Int), cs.foldl (fun (D : Int) (c : List Int × Int × Int) => (D * 1000003 + hs (_hl_groups (α := Float) c.1 c.2.1 c.2.2)) % P) 0])")
print("EXPECTED", [len(cases), D])
