"""Locate differing seeds of fz7_psi / fz7_cal: input of folds over chunks of K seeds (kept class only for psi).
  python fz8m_loc.py psi S0 N K  -> prints Lean input to work/fz8m_loc.in.txt and expected folds to work/fz8m_loc.exp.json
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz8m_metrics_gen as g, b4_gen as b4
which, S0, N, K = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
DIFF = len(sys.argv) > 5
if which == "psi":
    ex = []
    for c in range(0, N, K):
        ds = []
        for s in range(S0 + c, S0 + c + K):
            cls, d, *_ = g.psi_one(s)
            if cls == 0: ds.append(d)
        ex.append(b4.w(ds))
    body = (f"(let RS := (List.range {N}).map (fun (i : Nat) => ONE ({S0} + i)); (List.range {N // K}).map (fun (c : Nat) => "
            f"W (((RS.drop (c * {K})).take {K}).filterMap (fun (p : Nat × Int) => if p.1 == 0 then some p.2 else none))))")
    lets = g.PSI_LETS
else:
    ex = []
    for c in range(0, N, K):
        ex.append(b4.w([g.cal_one(s)[1] for s in range(S0 + c, S0 + c + K)]))
    body = (f"(let RS := (List.range {N}).map (fun (i : Nat) => ONE ({S0} + i)); (List.range {N // K}).map (fun (c : Nat) => "
            f"W (((RS.drop (c * {K})).take {K}).map (fun (p : Nat × Int) => p.2))))")
    lets = g.CAL_LETS
if DIFF:
    # K = 1: embed the expected per-seed digests, return the seeds whose digest differs (kept class)
    rows = [g.psi_one(x) if which == "psi" else g.cal_one(x) for x in range(S0, S0 + N)]
    ex = [d if d is not None else 0 for _, d, *_ in rows]
    body = (f"(let EX : List Int := {ex}; let RS := (List.range {N}).map (fun (i : Nat) => (ONE ({S0} + i)).2); "
            f"((List.range {N}).filter (fun (i : Nat) => RS.getD i 0 != EX.getD i 0)).map (fun (i : Nat) => ({S0} + i : Int)))")
    ex = [0]
from suite import Suite
st = Suite("tmp"); st.item, st.decl = "def:zz_carrier_e", "zz_carrier_e"
st.ints(lets, body, [(f"c{i}", "x", e) for i, e in enumerate(ex)], gen=True)
Path(HERE.parent / "work/fz8m_loc.in.txt").write_text(st.inputs[0]["text"])
Path(HERE.parent / "work/fz8m_loc.exp.json").write_text(json.dumps({"S0": S0, "K": K, "exp": ex}))
print(len(st.inputs[0]["text"]))
