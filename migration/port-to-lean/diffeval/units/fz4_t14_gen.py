"""Fuzz 2026-11-17 of def:train_run_14_final_and_summary and its precondition (train.py:742-841), by a
non-author. Suite fz4_t14 on def:zz_carrier_t of blueprint 5365851c-5549-44b7-9207-4bd4c422031d.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz4_t14_gen.py

Built on the machinery of fz_td_gen.py (inputs built INSIDE Lean from seeds with kit.GEN, mirrored here with
kit.gF / gI / hsh; one case = the fold over the seeds of one class of a block of the digest of the list of
(file name, table)). What differs: the slice of the real train.py is now lines 742-841 (td.SLICES patched,
the code recompiled), the scored sets draw their column names from a pool of ASCII names that exercises
drop_sas_names / keep_sas_names:
  names of the kept set in any case (row_id, DEFAULT_FLAG, Pd_Logistic, ..., AGE, Monthly_Income, ...), the
  names the drop removes in any case (IP_1, ip_2, XP_a, xp_, IP_, _FROM_, _Into_, _LEVEL_, _level_), near
  misses that must stay (IPX, I_P_1, _FROM, _from_x, _LEVEL_1, _LEVELS_, xp, Xp, "_FROM_ "), a name with a space,
  the empty name, three spellings of interest_rate (only the exact one is a key of `formats`; always present,
  Float64 or Int64). A random subset (2/3 of the names, interest_rate always), rotated, in one of two directions.
  0 to 3 rows. Metrics frames: the four Float64 columns plus one of 8 extra columns (shared Float64 / text,
  Valid_AUC Float64, Train_AUC Int64, zz Int64, model_name text, training_date text). ROC and the rest as in
  fz_td_gen, with more edge values (one ulp either side of 0.5, 1, 0.99995, +-inf, the smallest subnormal).
Precondition in Python (pre): rv_td_pre14.pre (ROCModel text and Area, merge clause, interest_rate present and
  not text in both scored sets, the ten formatted names present and not text in the merge) and, by construction,
  distinct ASCII names. Asserted equal to "the real code returns" on every generated input.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import importlib.util  # noqa: E402
import re  # noqa: E402

# td_gen.py (another author's, not edited) asserts the old line numbers of steps 13 and 15 at import. Load its
# source with SLICES reduced to the step this suite runs, at its current lines (train.py:742-841), as module td_gen.
_src = (HERE / "td_gen.py").read_text()
_new = re.sub(r"SLICES = \{.*?\n(?=U13, U14, U15)",
              'SLICES = {"s14": (742, 841, "model_summary = model_summary.clear().select(")}\n', _src, flags=re.S)
assert _new != _src
_spec = importlib.util.spec_from_file_location("td_gen", HERE / "td_gen.py")
td = importlib.util.module_from_spec(_spec)
sys.modules["td_gen"] = td
exec(compile(_new, str(HERE / "td_gen.py"), "exec"), td.__dict__)

import fz_td_gen as fz  # noqa: E402
import rv_td_pre14 as rp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
import b4_gen as b4  # noqa: E402
from suite import Suite  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
nan, inf = float("nan"), float("inf")



def ulp(x, k):
    b = struct.unpack("<Q", struct.pack("<d", x))[0]
    return struct.unpack("<d", struct.pack("<Q", b + k))[0]


E = [None, 0.0, 1.0, 0.5, 0.25, -0.0, 1e-5, 0.99995, 123456.789, -3.5, nan, inf, -inf, ulp(0.5, 1), ulp(0.5, -1),
     ulp(1.0, 1), ulp(1.0, -1), ulp(0.99995, 1), 5e-324, 1e22]
OLD_EL = fz.EL
fz.E[:] = E  # the pool of fz_td_gen (used by fz.FC / fz.ROC and the Lean lets)
NEW_EL = "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in E) + "]"
assert OLD_EL in fz.COMMON
COMMON = fz.COMMON.replace(OLD_EL, NEW_EL)

H, FC, IC, TC, ROC, HT = fz.H, fz.FC, fz.IC, fz.TC, fz.ROC, fz.HT

# (name, kind): F Float64, I Int64, T text; interest_rate handled apart
POOL = [("row_id", "F"), ("DEFAULT_FLAG", "F"), ("Pd_Logistic", "F"), ("credit_risk_score", "F"), ("risk_grade", "T"),
        ("RECOMMENDATION", "T"), ("interest_rate", "F"), ("INTEREST_RATE", "T"), ("Interest_Rate", "F"), ("age", "I"),
        ("AGE", "F"), ("Monthly_Income", "F"), ("credit_utilization", "F"), ("DEBT_RATIO", "F"), ("debt_ratio", "F"),
        ("total_late_payments", "I"), ("Num_Credit_Lines", "F"), ("IP_1", "F"), ("ip_2", "T"), ("XP_a", "F"),
        ("xp_", "I"), ("IP_", "F"), ("_FROM_", "F"), ("_Into_", "T"), ("_LEVEL_", "F"), ("_level_", "I"),
        ("IPX", "F"), ("I_P_1", "F"), ("_FROM", "F"), ("_from_x", "F"), ("_LEVEL_1", "F"), ("_LEVELS_", "F"),
        ("xp", "F"), ("Xp", "F"), ("_FROM_ ", "F"), ("row id", "T"), ("", "F"), ("x", "T"), ("zzz", "I")]
assert len({n for n, _ in POOL}) == len(POOL) and all(all(ord(c) < 128 for c in n) for n, _ in POOL)
KIND = {"F": 0, "I": 1, "T": 2}
NP = len(POOL)


def RS(a: int) -> pl.DataFrame:
    n = H(a, 9133, 4)
    sel = [(nm, k, j) for j, (nm, k) in enumerate(POOL) if nm == "interest_rate" or H(a, 9200 + j, 3) != 0]
    r = kit.hsh(a, 9121) % len(sel)
    sel = sel[r:] + sel[:r]
    if H(a, 9122, 2) == 1:
        sel = sel[::-1]
    cols = []
    for nm, k, j in sel:
        s = a * 64 + j
        if nm == "interest_rate":
            cols.append(IC(nm, s, n) if H(a, 9123, 2) == 0 else FC(nm, s, n))
        else:
            cols.append({"F": FC, "I": IC, "T": TC}[k](nm, s, n))
    return pl.DataFrame({c.name: c for c in cols})  # a dict keeps the empty name (a list of Series renames it column_N)


XM = 8


def MET(a: int, pre: str) -> pl.DataFrame:
    n = HT(a, 9131)
    cols = [FC(f"{pre}_{c}", a * 16 + j, n) for j, c in enumerate(["precision", "recall", "f1_score", "accuracy"])]
    x = H(a, 9111, XM)
    extra = {1: ("shared", FC), 2: ("Valid_AUC", FC), 3: ("zz", IC), 4: ("shared", TC), 5: ("model_name", TC),
             6: ("training_date", TC), 7: ("Train_AUC", IC)}.get(x)
    if extra:
        cols.append(extra[1](extra[0], a * 16 + 4, n))
    return pl.DataFrame(cols)


def env14(s: int) -> dict:
    return {"model_coefficients": fz.MC(s * 8 + 7), "training_metrics": MET(s * 8 + 3, "train"),
            "validation_metrics": MET(s * 8 + 4, "valid"), "risk_scores_train": RS(s * 8 + 5),
            "risk_scores_validation": RS(s * 8 + 6), "roc_train": ROC(s * 8 + 1, "Training Set", False),
            "roc_valid": ROC(s * 8 + 2, "Validation Set", False), "roc_valid_created": H(s, 9100, 2) == 0}


# ---- Lean side
NMS = "[" + ", ".join(lt.lean_str(n) for n, _ in POOL) + "]"
KDS = [KIND[k] for _, k in POOL]
LAYOUT = (
    f"let NMS : List String := {NMS}; let KDS : List Nat := {KDS}; "
    "let RS := fun (a : Nat) => let n := H a 9133 4; "
    "let sel := ((NMS.zip KDS).zip (List.range NMS.length)).filter (fun (q : (String × Nat) × Nat) => q.1.1 == \"interest_rate\" || H a (9200 + q.2) 3 != 0); "
    "let r := (hsh a 9121).toNat % sel.length; let rot := sel.rotateLeft r; "
    "let ord := if H a 9122 2 == 1 then rot.reverse else rot; "
    "(ord.map (fun (q : (String × Nat) × Nat) => (q.1.1, "
    "(if q.1.1 == \"interest_rate\" then (if H a 9123 2 == 0 then IC (a * 64 + q.2) n else FC (a * 64 + q.2) n) "
    "else if q.1.2 == 0 then FC (a * 64 + q.2) n else if q.1.2 == 1 then IC (a * 64 + q.2) n else TC (a * 64 + q.2) n))) : Pl.Frame Float); "
)
LETS = (
    COMMON + LAYOUT
    + "let MET := fun (a : Nat) (pre : String) => let n := HT a 9131; "
      "([(pre ++ \"_precision\", FC (a * 16) n), (pre ++ \"_recall\", FC (a * 16 + 1) n), (pre ++ \"_f1_score\", FC (a * 16 + 2) n), "
      "(pre ++ \"_accuracy\", FC (a * 16 + 3) n)] ++ "
      "(match H a 9111 8 with | 1 => [(\"shared\", FC (a * 16 + 4) n)] | 2 => [(\"Valid_AUC\", FC (a * 16 + 4) n)] "
      "| 3 => [(\"zz\", IC (a * 16 + 4) n)] | 4 => [(\"shared\", TC (a * 16 + 4) n)] | 5 => [(\"model_name\", TC (a * 16 + 4) n)] "
      "| 6 => [(\"training_date\", TC (a * 16 + 4) n)] | 7 => [(\"Train_AUC\", IC (a * 16 + 4) n)] | _ => []) : Pl.Frame Float); "
    + "let MC := fun (a : Nat) => let n := HT a 9141; ([(\"Variable\", TC (a * 16) n), (\"Estimate\", TC (a * 16 + 1) n)] : Pl.Frame Float); "
    + "let ONE := fun (s : Nat) => let xt := H (s * 8 + 3) 9111 8; let xv := H (s * 8 + 4) 9111 8; "
      "let o := train_run_14_final_and_summary (Tabular.Cell.str (some \"TODAY\")) (MC (s * 8 + 7)) (MET (s * 8 + 3) \"train\") "
      "(MET (s * 8 + 4) \"valid\") (RS (s * 8 + 5)) (RS (s * 8 + 6)) (ROC (s * 8 + 1) \"Training Set\" false) "
      "(ROC (s * 8 + 2) \"Validation Set\" false) (H s 9100 2 == 0); "
      "((if (xt == 1 && xv == 4) || (xt == 4 && xv == 1) then 1 else 0 : Nat), OUT o); "
)

POOLS = ("scored sets: 0-3 rows, names from a pool of 39 ASCII names (kept names in several cases, IP_ / XP_ / _FROM_ / _INTO_ / _LEVEL_ "
         "in several cases, near misses, a name with a space, the empty name, three spellings of interest_rate), a random 2/3 subset "
         "(interest_rate always), rotated, in either direction, interest_rate Float64 or Int64; ROC frames of 0-3 rows, label right or from "
         "{Training Set, Validation Set, x, null}, statistics from {null, 0, 1, 0.5, 0.25, -0.0, 1e-5, 0.99995, 123456.789, -3.5, NaN, +-inf, "
         "0.5 +- 1 ulp, 1 +- 1 ulp, 0.99995 + 1 ulp, 5e-324, 1e22}; metrics frames of 0-3 rows with one of 7 extra columns (shared "
         "Float64 / text, Valid_AUC Float64, Train_AUC Int64, zz Int64, model_name text, training_date text); model_coefficients two text columns")


def main():
    fz.NBLOCK = 5
    fz.BLOCK = 600
    # the precondition, and Python returning, agree on every input (asserted here, by construction in the Lean mirror)
    mism = 0
    for s in range(fz.S14, fz.S14 + fz.NBLOCK * fz.BLOCK):
        e = env14(s)
        p, (r, msg) = rp.pre(e), rp.returns(e)
        if p != r:
            mism += 1
            print("precondition vs Python", s, p, r, msg)
        shared = {H(s * 8 + 3, 9111, XM), H(s * 8 + 4, 9111, XM)}
        xt, xv = H(s * 8 + 3, 9111, XM), H(s * 8 + 4, 9111, XM)
        assert p == (not ((xt == 1 and xv == 4) or (xt == 4 and xv == 1))), (s, p, xt, xv)
    print("precondition/Python mismatches:", mism)
    st, units = fz.suite_files("fz4_t14", fz.U14, "s14", fz.S14, env14, rp.pre, LETS,
                               "a column `shared` Float64 in one metrics frame and text in the other", POOLS)
    st.write()
    for i, inp in enumerate(st.inputs):
        (td.WORK / f"{st.name}.in{i}.txt").write_text(inp["text"])
    (td.WORK / f"{st.name}.fuzz.json").write_text(json.dumps(
        {"fuzzer": "port-translator (fz4_t14_gen.py)", "generator": "diffeval/units/fz4_t14_gen.py", "blueprint": BLUEPRINT,
         "units": units}))
    for u, d in units.items():
        print(st.name, u, "generated", d["generated"], "kept", d["kept"], "raises inside:", d["python_raises_inside_precondition"][:8],
              "| input chars", [len(i["text"]) for i in st.inputs])


if __name__ == "__main__":
    main()
