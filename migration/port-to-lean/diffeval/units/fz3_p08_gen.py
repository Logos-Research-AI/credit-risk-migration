"""Fuzz of the update of 2026-11-17 by a non-author: def:predict_run_08_outputs (revision e3139240...) and
def:predict_run_08_outputs_precond (revision 44a056bb...), on def:zz_carrier_p of blueprint 5365851c-....

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz3_p08_gen.py

Input of seed s, built INSIDE Lean (FR s, AN s) and mirrored here (kit.hsh / gF / gI, integer arithmetic only):
  pool NP of column names (ASCII): the 15 KEEP_FULL names in lower, UPPER, Mixed case, "AGE", "Age", "aGe",
    names that differ by a trailing space / tab / underscore / digit, extras ("x", "target", "", " "), and
    two non-ASCII names whose Python upper() is a kept name (rejected by the precondition: counted, not kept).
  column j is included when hsh(s, 300+j) % 100 < dens, dens = 15 + 10 * (hsh(s,299) % 8); "age" (j = 0) when
    hsh(s,300) % 100 < 90; non-ASCII names when hsh % 100 < 4. Included names are put in order of rank of
    hsh(s, 400+j) (ties by j): any order of any spelling, so the kept columns of keep_sas_names come in FRAME order.
  rows n = [0,1,2,3,4,7][hsh(s,301) % 6]; column kind hsh(s,200+j) % 4: f64 (gF, 40 % edge list EF: null, NaN,
    +-inf, +-0, 1, 1 +- ulp, 1e-300, 5e-324, 0.5, 1e300), int (gI), str (gI index into SP), bool (gI).
  age_name = AN[hsh(s,302) % |AN|], AN has "age" twice, AGE, Age, aGe, names of kept columns (ROW_ID, row_id,
    Pd_Logistic, interest_rate, financial_health, Monthly_Income), fresh names, "", "AGE ", "age2".
Expected: the real lines of predict.py (from `KEEP_KAGGLE =` to the `# SAS names are case-blind` comment) exec'd on the
frame (real sas_compat.keep_sas_names). Precondition pre08 written here clause by clause from the item's text:
  names distinct; every character of every name < 128; a column named exactly "age"; age_name == "age" or no column whose
  upper-cased name is in the upper-cased KEEP_FULL has the name age_name.
Seeds with pre08 false are not kept (counted, and Python's behaviour on them recorded); a kept seed on which Python
raises is a defect. One case per (kept seed, output frame): digest of tR of the frame.
"""
from __future__ import annotations

import json
import math
import re
import sys
import textwrap
from collections import Counter
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[3] / "port"))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import suite as suite_mod  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
nx = math.nextafter
nan, inf = float("nan"), float("inf")
KEEP_FULL = ["row_id", "pd_logistic", "pred_logistic", "credit_risk_score", "risk_grade", "recommendation",
             "interest_rate", "age", "monthly_income", "credit_utilization", "debt_ratio", "total_late_payments",
             "num_credit_lines", "financial_health", "total_risk_flags"]
NP = (["age"] + KEEP_FULL[:7] + KEEP_FULL[8:]
      + ["ROW_ID", "PD_LOGISTIC", "Pd_Logistic", "AGE", "Age", "aGe", "Monthly_Income", "INTEREST_RATE",
         "Total_Risk_Flags", "FINANCIAL_HEALTH", "Credit_Risk_Score", "Recommendation", "Risk_Grade",
         "row_id ", "pd_logistic\t", "age_", "age2", "row-id", "x", "target", "", " ", "interest_rate2", "Debt_ratio",
         "NUM_CREDIT_LINES", "pred_logistic_"]
      + ["row_ıd", "pd_logiſti" + "c"])  # last two non-ASCII: upper() is a kept name in Python
NASCII0 = len(NP) - 2
AN = ["age", "age", "AGE", "Age", "aGe", "ROW_ID", "row_id", "Pd_Logistic", "interest_rate", "financial_health",
      "Monthly_Income", "x", "target", "", "AGE ", "age2", "fresh_name", "AGE_", "Pred_Logistic", "id"]
EF = [None, nan, inf, -inf, 0.0, -0.0, 1.0, nx(1.0, 2), nx(1.0, 0), 1e-300, 5e-324, 0.5, 1e300, 98.0]
SP = ["", "NA", "a", "x y", "é", "0", "1e3"]


def lean_str(s):
    return json.dumps(s, ensure_ascii=False)


def lf(x):
    return "none" if x is None else f"(some (Float.ofBits {cmp.fbits(x)}))" if False else None


def fbits(x):
    import struct
    return 0x7FF8000000000000 if x != x else struct.unpack("<Q", struct.pack("<d", x))[0]


LEAN_EF = "[" + ", ".join("none" if x is None else f"(some (Float.ofBits {fbits(x)}))" for x in EF) + "]"
LETS = (
    f"let NP : List String := [{', '.join(lean_str(x) for x in NP)}]; "
    f"let AN : List String := [{', '.join(lean_str(x) for x in AN)}]; "
    f"let EF : List (Option Float) := {LEAN_EF}; "
    f"let SP : List String := [{', '.join(lean_str(x) for x in SP)}]; "
    "let NA0 : Nat := %d; " % NASCII0
    + "let mkcol := fun (s j n : Nat) => let kd := (hsh s (200 + j)) % 4; "
    "(if kd = 0 then Pl.Col.f64 (gF (s * 64 + j) n 40 3 EF) else if kd = 1 then Pl.Col.int (gI (s * 64 + j) n 15 20 10) "
    f"else if kd = 2 then Pl.Col.str ((gI (s * 64 + j) n 15 {len(SP)} 0).map (fun (o : Option Int) => o.map (fun (i : Int) => SP.getD i.toNat \"\"))) "
    "else Pl.Col.bool ((gI (s * 64 + j) n 15 2 0).map (fun (o : Option Int) => o.map (fun (i : Int) => decide (i = 1))))  : Pl.Col Float); "
    "let FR := fun (s : Nat) => "
    "let dens : UInt64 := 15 + 10 * (hsh s 299 % 8); "
    "let n : Nat := [0, 1, 2, 3, 4, 7].getD ((hsh s 301 % 6).toNat) 0; "
    "let inc := fun (j : Nat) => if j = 0 then decide (hsh s 300 % 100 < 90) else if j ≥ NA0 then decide (hsh s (300 + j) % 100 < 4) else decide (hsh s (300 + j) % 100 < dens); "
    "let key := fun (j : Nat) => hsh s (400 + j); "
    "let incl : List Nat := (List.range NP.length).filter inc; "
    "let rank := fun (j : Nat) => (incl.filter (fun (k : Nat) => decide (key k < key j) || (key k == key j && decide (k < j)))).length; "
    "let order : List Nat := (List.range incl.length).filterMap (fun (r : Nat) => incl.find? (fun (j : Nat) => rank j == r)); "
    "(order.map (fun (j : Nat) => (NP.getD j \"\", mkcol s j n)) : Pl.Frame Float); "
    "let ANS := fun (s : Nat) => AN.getD ((hsh s 302 % AN.length.toUInt64).toNat) \"age\"; "
)


def mk(s: int):
    dens = 15 + 10 * (kit.hsh(s, 299) % 8)
    n = [0, 1, 2, 3, 4, 7][kit.hsh(s, 301) % 6]

    def inc(j):
        h = kit.hsh(s, 300 + j) % 100
        return h < 90 if j == 0 else h < 4 if j >= NASCII0 else h < dens

    incl = [j for j in range(len(NP)) if inc(j)]
    key = lambda j: kit.hsh(s, 400 + j)  # noqa: E731
    order = sorted(incl, key=lambda j: (key(j), j))
    series = []
    for j in order:
        kd = kit.hsh(s, 200 + j) % 4
        if kd == 0:
            v = kit.gF(s * 64 + j, n, 40, 3, EF)
            ser = pl.Series(NP[j], [None if x is None else x for x in v], dtype=pl.Float64, strict=False)
        elif kd == 1:
            ser = pl.Series(NP[j], kit.gI(s * 64 + j, n, 15, 20, 10), dtype=pl.Int64)
        elif kd == 2:
            v = kit.gI(s * 64 + j, n, 15, len(SP), 0)
            ser = pl.Series(NP[j], [None if i is None else SP[i] for i in v], dtype=pl.String)
        else:
            v = kit.gI(s * 64 + j, n, 15, 2, 0)
            ser = pl.Series(NP[j], [None if i is None else i == 1 for i in v], dtype=pl.Boolean)
        series.append(ser)
    df = pl.DataFrame(series) if series else pl.DataFrame()
    return df, AN[kit.hsh(s, 302) % len(AN)]


UP = {x.upper() for x in KEEP_FULL}


def pre08(df, age_name):
    names = df.columns
    return (len(set(names)) == len(names)
            and all(ord(c) < 128 for nm in names for c in nm)
            and "age" in names
            and (age_name == "age" or all(not (nm.upper() in UP) or nm != age_name for nm in names)))


SRC = (HERE.parents[3] / "port" / "credit_risk" / "predict.py").read_text().splitlines()
_a = next(i for i, l in enumerate(SRC) if "KEEP_KAGGLE =" in l)
_b = next(i for i, l in enumerate(SRC) if i > _a and "# SAS names are case-blind" in l)
CODE = textwrap.dedent("\n".join(SRC[_a:_b + 1]))


def real(df, age_name):
    ns = {"sas_compat": sas_compat, "test_predictions": df, "age_name": age_name}
    exec(CODE, ns)  # noqa: S102
    return ns["kaggle_submission"], ns["test_predictions_full"]


def toks(df):
    return cmp.tokens(cmp.canon_frame(df))


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 2100
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 350
    stats = Counter()
    kept = []
    rejected_py = {"raised": 0, "ran": 0}
    defects = []
    ranpy = []
    s = first
    while len(kept) < want:
        df, an = mk(s)
        ok = pre08(df, an)
        stats["generated"] += 1
        try:
            a, b = real(df, an)
            err = None
        except Exception as e:  # noqa: BLE001
            a = b = None
            err = f"{type(e).__name__}: {e}"
        if ok:
            if err:
                defects.append((s, err))
            else:
                kept.append((s, a, b, df, an))
        else:
            rejected_py["raised" if err else "ran"] += 1
            if not err:
                ranpy.append(s)
        s += 1
    print("generated", stats["generated"], "kept", len(kept), "rejected", rejected_py, "defects", defects[:5])
    st = Suite("fz3_p08")
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_p", "zz_carrier_p")
    st.item, st.decl = "def:zz_carrier_p", "zz_carrier_p"
    cov = Counter()
    for k in range(0, len(kept), per):
        part = kept[k:k + per]
        seeds = [p[0] for p in part]
        cases = []
        for sd, a, b, df, an in part:
            cases.append((f"seed{sd}/kaggle", "predict_run_08_outputs", cmp.digest(toks(a)), {"fz": "kept"}))
            cases.append((f"seed{sd}/full", "predict_run_08_outputs", cmp.digest(toks(b)), {"fz": "kept"}))
            cov["rows0"] += df.height == 0
            cov["rows1"] += df.height == 1
            cov["age_name==age"] += an == "age"
            cov["age_name_fresh_or_other"] += an != "age"
            cov["has_upper_kept_nonexact"] += any(c.upper() in UP and c not in KEEP_FULL for c in df.columns)
            cov["full_ne_kaggle_cols"] += a.columns != b.columns
            cov["renamed_age_name_in_full"] += an != "age" and an in b.columns
            cov["kaggle_empty"] += a.width == 0
            cov["kaggle_one_col"] += a.width == 1
            cov["kaggle_order_reversed_vs_list"] += a.columns == ["pd_logistic", "row_id"]
        lst = "[" + ", ".join(map(str, seeds)) + "]"
        body = ("(" + lst + ".flatMap (fun (s : Nat) => let r := predict_run_08_outputs (α := Float) (FR s) (ANS s); "
                "[dg (tR r.1), dg (tR r.2)]))")
        st.ints(LETS, body, cases, gen=True, use_kit=True)
    st.write()
    (suite_mod.WORK / "fz3_p08.fuzz.json").write_text(json.dumps({
        "generator": "diffeval/units/fz3_p08_gen.py", "blueprint": BLUEPRINT,
        "units": {"predict_run_08_outputs": {"seeds": f"{first}..{s - 1}", "generated": stats["generated"],
                                              "kept": len(kept), "rejected_by_precondition": stats["generated"] - len(kept) - len(defects),
                                              "python_raises_inside_precondition": defects,
                                              "python_ran_on_rejected": rejected_py, "coverage": dict(cov)}}}, indent=1))
    print(dict(cov))


if __name__ == "__main__":
    main()
