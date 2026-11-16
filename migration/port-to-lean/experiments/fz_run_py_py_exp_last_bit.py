"""Fuzz 2026-11-16, def:run_py_py: the three differing seeds are the last bit of exp.

Seeds 30930, 31316, 31393 of diffeval/units/fz_run_py_py_gen.py. The Lean evaluator's Float.exp on
the arguments below (eval_decl on def:zz_carrier_p, first hand) differs from polars / math.exp by
one unit in the last place. Here: the port's two output frames with pd_logistic recomputed from the
Lean's exp value on those rows (and credit_risk_score = base_score + score_range * (1 - pd) after
it); their digest is compared with the digest the Lean returned for the seed.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/fz_run_py_py_exp_last_bit.py
"""
import struct, sys, tempfile
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "diffeval" / "units")); sys.path.insert(0, str(HERE.parent / "diffeval"))
import b4_gen as b4
import fz_run_py_py_gen as g

fb = lambda b: struct.unpack("<d", struct.pack("<Q", b))[0]
bt = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]
# argument bits -> (python exp bits, Lean Float.exp bits)
EXP = {4617621881895628534: (4641058840064317067, 4641058840064317066),
       4638368729957408022: (5407219528248307389, 5407219528248307390),
       4627839011295874457: (4771756984989006923, 4771756984989006922)}
LEAN = {30930: 17394828593469107001, 31316: 9740495638350836890, 31393: 14327422387733817827}
base = Path(tempfile.mkdtemp())
for s, lean in LEAN.items():
    rec = g.pyrun(s, base / str(s))
    logit = rec["locals"]["test_scored_temp"]["predicted_logit"].to_list()
    files = []
    for name, df in rec["files"]:
        pd = df["pd_logistic"].to_list()
        new = []
        for x, p in zip(logit, pd):
            k = None if x is None else bt(-x)
            if k in EXP:
                assert bt(1 / (1 + fb(EXP[k][0]))) == bt(p)          # the port's value comes from Python's exp
                p = 1 / (1 + fb(EXP[k][1]))
            new.append(p)
        df = df.with_columns(pl.Series("pd_logistic", new, dtype=pl.Float64))
        if "credit_risk_score" in df.columns:
            df = df.with_columns(credit_risk_score=600.0 + 250.0 * (1 - pl.col("pd_logistic")))
        files.append((name, df))
    got = b4.w([1] + [g.file_digest(f, df) for f, df in files])
    print(s, "python", g.expected(rec), "python with the Lean's exp", got, "Lean", lean, "EQUAL" if got == lean else "DIFFERENT")

# ---- the check step of the fuzz receipt: write "all_differences_are_recorded_limit" into
# work/fz_run_py_py.fuzz.json only when (a) the differing seeds of the per-seed suite are exactly the
# seeds above, (b) the differing blocks of the main suite are exactly the blocks holding them, and
# (c) the recomputation above gave the Lean's digest on every one of them.
import json, re
W = HERE.parent / "diffeval" / "work"
ok_all = True
for s, lean in LEAN.items():
    rec = g.pyrun(s, base / (str(s) + "b"))
    logit = rec["locals"]["test_scored_temp"]["predicted_logit"].to_list()
    files = []
    for name, df in rec["files"]:
        new = [p if (x is None or bt(-x) not in EXP) else 1 / (1 + fb(EXP[bt(-x)][1])) for x, p in zip(logit, df["pd_logistic"].to_list())]
        df = df.with_columns(pl.Series("pd_logistic", new, dtype=pl.Float64))
        if "credit_risk_score" in df.columns:
            df = df.with_columns(credit_risk_score=600.0 + 250.0 * (1 - pl.col("pd_logistic")))
        files.append((name, df))
    ok_all &= b4.w([1] + [g.file_digest(f, df) for f, df in files]) == lean
bis = json.loads((W / "fz_run_py_py_bisect.result.json").read_text())
bis_fail = sorted(int(re.search(r"seed (\d+)", r["id"]).group(1)) for r in bis if r["status"] != "PASS")
bis_lean = {int(re.search(r"seed (\d+)", r["id"]).group(1)): r["diffs"][0][2] for r in bis if r["status"] != "PASS"}
main = json.loads((W / "fz_run_py_py.result.json").read_text())
main_fail = sorted(int(re.search(r"seeds of (\d+)", r["id"]).group(1)) for r in main if r["status"] != "PASS")
blocks = sorted(g.SEED0 + g.CH * ((s - g.SEED0) // g.CH) for s in LEAN)
cond = ok_all and bis_fail == sorted(LEAN) and bis_lean == LEAN and main_fail == blocks
print("differing seeds (per-seed suite):", bis_fail, "| differing blocks (main suite):", main_fail, "| all explained:", cond)
p = W / "fz_run_py_py.fuzz.json"
d = json.loads(p.read_text())
u = d["units"]["run_py_py"]
if cond:
    u["all_differences_are_recorded_limit"] = ("last bit of exp (RULEBOOK 6, outside the model): seeds 30930, 31316, 31393; the port's frames recomputed with the "
                                               "Lean evaluator's Float.exp value give the Lean's digest on each (experiments/fz_run_py_py_exp_last_bit.py)")
else:
    u.pop("all_differences_are_recorded_limit", None)
p.write_text(json.dumps(d, indent=1))
