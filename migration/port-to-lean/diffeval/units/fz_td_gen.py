"""Fuzz of task T-D (update 2026-11-17) by port-translator-7, who reviewed the units and did not write them:
  def:train_run_13_roc                credit_risk/train.py:702-718   suite fz_td13
  def:train_run_14_final_and_summary  credit_risk/train.py:725-819   suite fz_td14
  def:train_run_15_printed_roc        credit_risk/train.py:823-842   suite fz_td15
on blueprint 5365851c-5549-44b7-9207-4bd4c422031d, carrier def:zz_carrier_t / zz_carrier_t.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_td_gen.py
  (eval_decl each input of work/<suite>.inputs.json; python3 diffeval/fuzz_collect.py 7 <suite>; compare.py;
   uv run --project ../../port python diffeval/fuzz_receipt.py fz_td13 fz_td14 fz_td15)

Every input is built INSIDE Lean from its seed (kit.GEN) and mirrored here (kit.gF / gI / hsh). Expected:
the source lines of the step executed verbatim (td_gen.run_slice), write_sas_csv recording (name, frame).

Step 13. Frames as in fz_train_05_13_gen (columns of fz_t1_gen: outcome Float64 from {0, 1, null, NaN,
  -0.0, 2, 0.5} / Int64 with nulls / Boolean / Null dtype; probability on a grid with offsets, edges,
  random, Int64, Boolean, Null dtype; rows 0..40; the two columns alone or with a third one, three
  orders); training frame from seed s, validation frame from s + 500000. fsum = CPython's algorithm as a
  Lean `let` (fz_t1_gen.FS_LET, its mirror asserted equal to math.fsum on every call). One value per
  seed: the fold of roc_train, roc_valid and roc_valid_created.
  Precondition in Python: both frames have the two columns (always), roc_association_precond on each
  (fz_t1_gen.pre_roc), and the validation outcome is Float64 or Int64. Seeds with columns of unequal
  length (not a pl.DataFrame) and seeds whose validation outcome is Boolean or Null dtype (the
  precondition rejects, Python raises NotImplementedError: asserted) are dropped.
Step 14. model_coefficients: two text columns; training / validation metrics: the four Float64 columns
  and, by seed, a further column (`shared` Float64, `Valid_AUC` Float64, `zz` Int64, `shared` text);
  scored sets: three layouts mixing kept and other columns, interest_rate Float64 or Int64, 0-3 rows;
  ROC frames: 0-3 rows, label right / from a pool with null, statistics from the pool E (null, 0, 1,
  0.5, 0.25, -0.0, 1e-5, 0.99995, 123456.789, -3.5, NaN, +inf); roc_valid_created by seed; today =
  the text cell TODAY. One value per seed: the digest of the list of (file name, table).
  Precondition in Python: ROCModel is text and Area exists in both ROC frames (always); the merge
  precondition on the four frames as the unit builds them: no two same-named columns Float64 with
  text (rejected: `shared` Float64 in one metrics frame and text in the other; Python returns).
Step 15. confusion matrices: four columns, 0-3 rows; ROC frames as above; in one seed of twelve TauA
  of roc_valid is Int64 (rejected by "seven Float64 statistics"; Python returns). sas_d8 = the real
  function as a table over the pool. Third class: rejected by the label clause alone (narrowing of
  2026-11-17: an exported ROC frame with rows has a label that is not null); Python returns there
  and the Lean is expected to differ (that difference is why the clause exists).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import td_gen as td  # noqa: E402  (sets the carrier to def:zz_carrier_t)
import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import fz_t1_gen as t1  # noqa: E402  (puts the checked math.fsum in place)
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
WORK = td.WORK
U13, U14, U15 = td.U13, td.U14, td.U15
w, h = b4.w, t1.h
nan, inf = float("nan"), float("inf")

# ------------------------------------------------------------------ step 13
D, CH = 500000, 25
S13, N13, PER = 50000, 2900, 58


def equal_len(s: int) -> bool:
    return h(s, 1003) % 25 != 0


def frame13(s: int) -> pl.DataFrame:
    y, p = t1.y_col(s).alias("default_flag"), t1.s_col(s).alias("pd_logistic")
    x = pl.Series("x", kit.gI(s, t1.nn(s), 0, 5, 0), dtype=pl.Int64)
    k = h(s, 1010) % 3
    return pl.DataFrame([y, p] if k == 0 else [p, x, y] if k == 1 else [x, y, p])


FR = ("let FR := fun (s : Nat) => (match h s 1010 % 3 with "
      '| 0 => [("default_flag", YC s), ("pd_logistic", SC s)] '
      '| 1 => [("pd_logistic", SC s), ("x", Pl.Col.int (gI s (nn s) 0 5 0)), ("default_flag", YC s)] '
      '| _ => [("x", Pl.Col.int (gI s (nn s) 0 5 0)), ("default_flag", YC s), ("pd_logistic", SC s)] : Pl.Frame Float); '
      f"let OK := fun (s : Nat) => h s 1003 % 25 != 0 && h (s + {D}) 1003 % 25 != 0 && h (s + {D}) 1001 % 10 < 8; ")


def pre13(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    frames = all(len(set(f.columns)) == f.width and {"default_flag", "pd_logistic"} <= set(f.columns) for f in (a, b))
    roc = all(t1.pre_roc(f["default_flag"], f["pd_logistic"]) for f in (a, b))
    return frames and roc and b.schema["default_flag"] in (pl.Float64, pl.Int64)


def suite13():
    st = Suite("fz_td13")
    val, created, dropped_len, dropped_dtype, raises = {}, 0, 0, 0, []
    for s in range(S13, S13 + N13):
        if not (equal_len(s) and equal_len(s + D)):
            dropped_len += 1
            continue
        a, b = frame13(s), frame13(s + D)
        ok = pre13(a, b)
        try:
            ns, _, _ = td.run_slice("s13", {"risk_scores_train": a, "risk_scores_validation": b})
        except Exception as ex:  # noqa: BLE001
            if ok:
                raises.append(s)
                print("13 raises inside the precondition", s, type(ex).__name__, ex)
            else:
                assert isinstance(ex, NotImplementedError) and b.schema["default_flag"] in (pl.Boolean, pl.Null), (s, ex)
                dropped_dtype += 1
            continue
        assert ok, ("rejected and Python returns: a class this generator does not send", s)
        created += int(ns["roc_valid_created"])
        val[s] = w(b4.frame_tok(ns["roc_train"]) + b4.frame_tok(ns["roc_valid"]) + [int(ns["roc_valid_created"])])
    assert not raises, raises[:5]
    kept = sorted(val)
    assert all((h(s + D, 1001) % 10 < 8) for s in kept)
    lets = (t1.BASE + t1.COLS + b4.OF + b4.TS + b4.TCOL + FR + t1.FS_LET
            + "let tf := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2); "
            + f"let R := fun (s : Nat) => let r := train_run_13_roc (α := Float) FS (FR s) (FR (s + {D})); "
              "W (tf r.1 ++ tf r.2.1 ++ [if r.2.2 then 1 else 0]); ")
    nch = N13 // CH
    for k0 in range(0, nch, PER):
        n = min(PER, nch - k0)
        cases = []
        for i in range(k0, k0 + n):
            c = [s for s in kept if S13 + CH * i <= s < S13 + CH * (i + 1)]
            cases.append((f"13 seeds {S13 + CH * i}..{S13 + CH * (i + 1) - 1}", U13, w([val[s] for s in c]), {"fz": "kept", "covers": len(c)}))
        body = f"(List.range {n}).map (fun (i : Nat) => W (((List.range' ({S13 + CH * k0} + {CH} * i) {CH}).filter OK).map R))"
        st.ints(lets, body, cases, gen=True, use_kit=False)
    note = (f"{t1.POOLS}; frames: the two columns alone or with a third Int64 column, three orders; validation frame from seed + {D}; "
            f"one case = 25 seeds; roc_valid_created true on {created} kept inputs, false on {len(kept) - created}; dropped: {dropped_len} "
            f"with columns of unequal length, {dropped_dtype} with a Boolean or Null-dtype validation outcome (precondition rejects, Python raises)")
    return st, {U13: {"seeds": f"{S13}..{S13 + N13 - 1}", "generated": N13, "kept": len(kept),
                      "python_raises_inside_precondition": raises, "note": note}}


# ------------------------------------------------------------------ steps 14 and 15
E = [None, 0.0, 1.0, 0.5, 0.25, -0.0, 1e-5, 0.99995, 123456.789, -3.5, nan, inf]
SP = ["Training Set", "Validation Set", "x", None]
RC = ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]
HTS = [1, 1, 1, 0, 2, 3]
S14, S15, BLOCK, NBLOCK = 300000, 400000, 600, 4


def H(s: int, k: int, m: int) -> int:
    return kit.hsh(s, k) % m


def FC(name, s, n):
    return pl.Series(name, kit.gF(s, n, 100, 0, E), dtype=pl.Float64, nan_to_null=False)


def IC(name, s, n):
    return pl.Series(name, kit.gI(s, n, 20, 7, 3), dtype=pl.Int64)


def TC(name, s, n):
    return pl.Series(name, [None if k is None else SP[k] for k in kit.gI(s, n, 0, len(SP), 0)], dtype=pl.String)


def HT(s, k):
    return HTS[H(s, k, 6)]


def ROC(a: int, lab: str, ti: bool) -> pl.DataFrame:
    n = HT(a, 9102)
    cols = [TC("ROCModel", a, n) if H(a, 9101, 3) == 0 else pl.Series("ROCModel", [lab] * n, dtype=pl.String)]
    for j, c in enumerate(RC):
        cols.append(IC(c, a * 16 + 1 + j, n) if (ti and j == 6) else FC(c, a * 16 + 1 + j, n))
    return pl.DataFrame(cols)


def MET(a: int, pre: str) -> pl.DataFrame:
    n = HT(a, 9131)
    cols = [FC(f"{pre}_{c}", a * 16 + j, n) for j, c in enumerate(["precision", "recall", "f1_score", "accuracy"])]
    x = H(a, 9111, 5)
    if x == 1:
        cols.append(FC("shared", a * 16 + 4, n))
    elif x == 2:
        cols.append(FC("Valid_AUC", a * 16 + 4, n))
    elif x == 3:
        cols.append(IC("zz", a * 16 + 4, n))
    elif x == 4:
        cols.append(TC("shared", a * 16 + 4, n))
    return pl.DataFrame(cols)


RS_LAYOUT = [
    [("row_id", "F"), ("default_flag", "F"), ("pd_logistic", "F"), ("risk_grade", "T"), ("interest_rate", "F"), ("age", "I")],
    [("zzz", "I"), ("interest_rate", "F"), ("recommendation", "T"), ("row_id", "I"), ("credit_risk_score", "F")],
    [("num_credit_lines", "F"), ("debt_ratio", "F"), ("x", "T"), ("interest_rate", "I"), ("monthly_income", "F"),
     ("total_late_payments", "I"), ("credit_utilization", "F")],
]
MK = {"F": FC, "I": IC, "T": TC}


def RS(a: int) -> pl.DataFrame:
    n = H(a, 9133, 4)
    return pl.DataFrame([MK[k](c, a * 16 + j, n) for j, (c, k) in enumerate(RS_LAYOUT[H(a, 9121, 3)])])


def MC(a: int) -> pl.DataFrame:
    n = HT(a, 9141)
    return pl.DataFrame([TC("Variable", a * 16, n), TC("Estimate", a * 16 + 1, n)])


def CM(a: int) -> pl.DataFrame:
    n = HT(a, 9151)
    return pl.DataFrame([FC("default_flag", a * 16, n), IC("pred_logistic", a * 16 + 1, n), IC("COUNT", a * 16 + 2, n),
                         FC("PERCENT", a * 16 + 3, n)])


def env14(s: int) -> dict:
    return {"model_coefficients": MC(s * 8 + 7), "training_metrics": MET(s * 8 + 3, "train"), "validation_metrics": MET(s * 8 + 4, "valid"),
            "risk_scores_train": RS(s * 8 + 5), "risk_scores_validation": RS(s * 8 + 6),
            "roc_train": ROC(s * 8 + 1, "Training Set", False), "roc_valid": ROC(s * 8 + 2, "Validation Set", False),
            "roc_valid_created": H(s, 9100, 2) == 0}


def env15(s: int) -> dict:
    return {"confusion_matrix_train": CM(s * 8 + 3), "confusion_matrix": CM(s * 8 + 4),
            "roc_train": ROC(s * 8 + 1, "Training Set", False), "roc_valid": ROC(s * 8 + 2, "Validation Set", H(s, 9103, 12) == 0),
            "roc_valid_created": H(s, 9100, 2) == 0}


def pre14(e: dict) -> bool:
    """def:train_run_14_final_and_summary_precond: ROCModel text and Area present in both ROC frames;
    merge_one_to_one_precond on the four frames the unit builds: no two same-named columns of an
    excluded pair of dtypes (Date with anything but Date / Null; Float64 with text)."""
    for f in (e["roc_train"], e["roc_valid"]):
        if f.schema.get("ROCModel") != pl.String or "Area" not in f.columns:
            return False
    frames = [{"Train_AUC": e["roc_train"].schema["Area"]}, {"Valid_AUC": e["roc_valid"].schema["Area"]},
              dict(e["training_metrics"].schema), dict(e["validation_metrics"].schema)]

    def excluded(a, b):
        if a == pl.Date:
            return b not in (pl.Date, pl.Null)
        return a == pl.Float64 and b == pl.String

    return not any(excluded(f[c], g[c]) for f in frames for g in frames for c in f if c in g)


def pre15(e: dict) -> bool:
    """def:train_run_15_printed_roc_precond: ROCModel text and the seven statistics Float64 in both frames;
    and (narrowing of 2026-11-17) roc_train, if it has rows, has a label that is not null, and so has
    roc_valid when roc_valid_created is true."""
    return pre15_dtypes(e) and labelled(e["roc_train"]) and (not e["roc_valid_created"] or labelled(e["roc_valid"]))


def labelled(f: pl.DataFrame) -> bool:
    return f.height == 0 or f["ROCModel"].null_count() < f.height


def pre15_dtypes(e: dict) -> bool:
    return all(f.schema.get("ROCModel") == pl.String and all(f.schema.get(c) == pl.Float64 for c in RC)
               for f in (e["roc_train"], e["roc_valid"]))


def out_digest(writes) -> int:
    toks = [len(writes)]
    for name, df in writes:
        if "training_date" in df.columns:
            df = df.with_columns(training_date=pl.lit("TODAY", dtype=pl.String))
        toks += cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df))
    return cmp.digest(toks)


EL = "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in E) + "]"
SPL = "[" + ", ".join("none" if x is None else f"some {lt.lean_str(x)}" for x in SP) + "]"
COMMON = (
    b4.W
    + f"let E : List (Option Float) := {EL}; let SP : List (Option String) := {SPL}; "
    + "let H := fun (s k m : Nat) => (hsh s k).toNat % m; "
    + "let FC := fun (s n : Nat) => (Pl.Col.f64 (gF s n 100 0 E) : Pl.Col Float); "
    + "let IC := fun (s n : Nat) => (Pl.Col.int (gI s n 20 7 3) : Pl.Col Float); "
    + "let TC := fun (s n : Nat) => (Pl.Col.str ((gI s n 0 4 0).map (fun (o : Option Int) => (match o with | some k => SP.getD k.toNat none | none => none : Option String))) : Pl.Col Float); "
    + f"let HT := fun (s k : Nat) => ({HTS} : List Nat).getD (H s k 6) 1; "
    + f"let RC : List String := {json.dumps(RC)}; "
    + "let ROC := fun (a : Nat) (lab : String) (ti : Bool) => let n := HT a 9102; "
      "((\"ROCModel\", if H a 9101 3 == 0 then TC a n else Pl.Col.str (List.replicate n (some lab))) :: "
      "(List.range 7).map (fun (j : Nat) => (RC.getD j \"\", if ti && j == 6 then IC (a * 16 + 1 + j) n else FC (a * 16 + 1 + j) n)) : Pl.Frame Float); "
    + "let OUT := fun (o : List (String × Tabular.Table Float)) => dg (o.length.toUInt64 :: o.flatMap (fun (p : String × Tabular.Table Float) => tS p.1 ++ tA p.2)); "
)
LAY = "match H a 9121 3 with " + " ".join(
    f"| {'_' if i == 2 else i} => [" + ", ".join(f"({lt.lean_str(c)}, {'FC' if k == 'F' else 'IC' if k == 'I' else 'TC'} (a * 16 + {j}) n)"
                                                 for j, (c, k) in enumerate(lay)) + "]" for i, lay in enumerate(RS_LAYOUT))
LETS14 = (
    COMMON
    + "let MET := fun (a : Nat) (pre : String) => let n := HT a 9131; "
      "([(pre ++ \"_precision\", FC (a * 16) n), (pre ++ \"_recall\", FC (a * 16 + 1) n), (pre ++ \"_f1_score\", FC (a * 16 + 2) n), (pre ++ \"_accuracy\", FC (a * 16 + 3) n)] ++ "
      "(match H a 9111 5 with | 1 => [(\"shared\", FC (a * 16 + 4) n)] | 2 => [(\"Valid_AUC\", FC (a * 16 + 4) n)] | 3 => [(\"zz\", IC (a * 16 + 4) n)] "
      "| 4 => [(\"shared\", TC (a * 16 + 4) n)] | _ => []) : Pl.Frame Float); "
    + f"let RS := fun (a : Nat) => let n := H a 9133 4; ({LAY} : Pl.Frame Float); "
    + "let MC := fun (a : Nat) => let n := HT a 9141; ([(\"Variable\", TC (a * 16) n), (\"Estimate\", TC (a * 16 + 1) n)] : Pl.Frame Float); "
    + "let ONE := fun (s : Nat) => let xt := H (s * 8 + 3) 9111 5; let xv := H (s * 8 + 4) 9111 5; "
      "let o := train_run_14_final_and_summary (Tabular.Cell.str (some \"TODAY\")) (MC (s * 8 + 7)) (MET (s * 8 + 3) \"train\") (MET (s * 8 + 4) \"valid\") "
      "(RS (s * 8 + 5)) (RS (s * 8 + 6)) (ROC (s * 8 + 1) \"Training Set\" false) (ROC (s * 8 + 2) \"Validation Set\" false) (H s 9100 2 == 0); "
      "((if (xt == 1 && xv == 4) || (xt == 4 && xv == 1) then 1 else 0 : Nat), OUT o); "
)
D8 = {}
for _v in [x for x in E if x is not None] + [float(k) for k in range(-3, 4)]:
    D8[cmp.fbits(_v)] = sc.sas_d8(_v)
LETS15 = (
    COMMON
    + "let D : List (UInt64 × String) := [" + ", ".join(f"({k}, {lt.lean_str(t)})" for k, t in D8.items()) + "]; "
    + f"let d8 := fun (o : Option Float) => (match o with | none => {lt.lean_str(sc.sas_d8(None))} | some x => (D.lookup x.toBits).getD \"?MISSING\"); "
    + "let CM := fun (a : Nat) => let n := HT a 9151; ([(\"default_flag\", FC (a * 16) n), (\"pred_logistic\", IC (a * 16 + 1) n), "
      "(\"COUNT\", IC (a * 16 + 2) n), (\"PERCENT\", FC (a * 16 + 3) n)] : Pl.Frame Float); "
    + "let ONE := fun (s : Nat) => let ti := H s 9103 12 == 0; "
      "let o := train_run_15_printed_roc d8 (CM (s * 8 + 3)) (CM (s * 8 + 4)) (ROC (s * 8 + 1) \"Training Set\" false) (ROC (s * 8 + 2) \"Validation Set\" ti) (H s 9100 2 == 0); "
      "let nl := fun (fr : Pl.Frame Float) => (match fr.lookup \"ROCModel\" with | some (.str v) => v.length > 0 && v.all (fun (x : Option String) => x.isNone) | _ => false : Bool); "
      "((if ti then 1 else if nl (ROC (s * 8 + 1) \"Training Set\" false) || (H s 9100 2 == 0 && nl (ROC (s * 8 + 2) \"Validation Set\" false)) then 2 else 0 : Nat), OUT o); "
)


def all_null_label(e: dict) -> bool:
    """rejected by the label clause alone (the dtype clauses hold)"""
    return pre15_dtypes(e) and not pre15(e)


def suite_files(name: str, unit: str, key: str, S0: int, env, pre, lets: str, what_rejected: str, pools: str, sub=None):
    st = Suite(name)
    gen = kept = rej = 0
    raises_in, raises_out, false_n, sub_n = [], [], 0, 0
    for b in range(NBLOCK):
        s0 = S0 + b * BLOCK
        dig = {0: [], 1: [], 2: []}
        for s in range(s0, s0 + BLOCK):
            e = env(s)
            ok = pre(e)
            gen += 1
            try:
                _, writes, _ = td.run_slice(key, e)
            except Exception as ex:  # noqa: BLE001
                (raises_in if ok else raises_out).append(s)
                print(unit, "raises", s, ok, type(ex).__name__, str(ex)[:100])
                continue
            dig[0 if ok else 2 if (sub is not None and sub(e)) else 1].append(out_digest(writes))
            false_n += int(ok and not e["roc_valid_created"])
        kept += len(dig[0])
        rej += len(dig[1])
        sub_n += len(dig[2])
        skip = [s for s in raises_in + raises_out if s0 <= s < s0 + BLOCK]
        body = (f"(let X : List Nat := {skip}; let RS_ := ((List.range' {s0} {BLOCK}).filter (fun (s : Nat) => !X.contains s)).map ONE; "
                f"{[0, 1, 2] if sub is not None else [0, 1]}.map (fun (c : Nat) => W ((RS_.filter (fun (p : Nat × Int) => p.1 == c)).map (fun (p : Nat × Int) => p.2))))")
        rng = f"seeds {s0}..{s0 + BLOCK - 1}"
        st.ints(lets, body, [
            (f"{rng}: kept ({len(dig[0])} inputs)", unit, w(dig[0]), {"fz": "kept", "covers": len(dig[0])}),
            (f"{rng}: rejected, {what_rejected} ({len(dig[1])} inputs)", unit, w(dig[1]), {"fz": "rejected", "covers": len(dig[1])}),
        ] + ([(f"{rng}: rejected, an exported ROC frame with rows whose labels are all null ({len(dig[2])} inputs)", unit, w(dig[2]),
               {"fz": "rejected", "covers": len(dig[2])})] if sub is not None else []), gen=True, table=True)
    note = (f"one case = the fold over the seeds of one class in a block of {BLOCK} seeds of the digest of the list of (file name, table); "
            f"{pools}; roc_valid_created false on {false_n} kept inputs; rejected inputs on which Python returns: {rej} ({what_rejected}); "
            f"Python raises outside the precondition (dropped): {len(raises_out)}"
            + (f"; rejected by the label clause (an exported ROC frame with rows, all labels null; Python returns, Lean differs: the reason for the clause): {sub_n}" if sub is not None else ""))
    return st, {unit: {"seeds": f"{S0}..{S0 + NBLOCK * BLOCK - 1}", "generated": gen, "kept": kept,
                       "python_raises_inside_precondition": raises_in, "note": note}}


def main():
    pools14 = ("pools: ROC frames of 0-3 rows, label right or from {Training Set, Validation Set, x, null}, statistics from {null, 0, 1, 0.5, "
               "0.25, -0.0, 1e-5, 0.99995, 123456.789, -3.5, NaN, +inf}; metrics frames of 0-3 rows with a further column (shared Float64 / "
               "Valid_AUC Float64 / zz Int64 / shared text); scored sets of 0-3 rows in three layouts, interest_rate Float64 or Int64; "
               "model_coefficients two text columns of 0-3 rows")
    pools15 = ("pools: confusion matrices of four columns and 0-3 rows; ROC frames of 0-3 rows, label right or from a pool with null, "
               "statistics from {null, 0, 1, 0.5, 0.25, -0.0, 1e-5, 0.99995, 123456.789, -3.5, NaN, +inf}; sas_d8 the real function as a table")
    built = [suite13(),
             suite_files("fz_td14", U14, "s14", S14, env14, pre14, LETS14, "a column `shared` Float64 in one metrics frame and text in the other", pools14),
             suite_files("fz_td15", U15, "s15", S15, env15, pre15, LETS15, "TauA of roc_valid is Int64", pools15, sub=all_null_label)]
    for st, units in built:
        st.write()
        for i, inp in enumerate(st.inputs):
            (WORK / f"{st.name}.in{i}.txt").write_text(inp["text"])
        (WORK / f"{st.name}.fuzz.json").write_text(json.dumps({"fuzzer": "port-translator-7", "generator": "diffeval/units/fz_td_gen.py",
                                                              "blueprint": BLUEPRINT, "units": units}))
        for u, d in units.items():
            print(st.name, u, "generated", d["generated"], "kept", d["kept"], f"({d['kept'] / d['generated']:.3f})",
                  "raises inside:", d["python_raises_inside_precondition"][:8], "| input chars", [len(i["text"]) for i in st.inputs])
            print("   ", d["note"][-260:])


if __name__ == "__main__":
    main()
