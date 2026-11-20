"""Fidelity pass 2026-11-20, third attempt (label train-c): def:train_run_11_confusion_valid on the REAL input of the
real train.run (port HEAD 4a757fb) on legacy/data (work/fz10c_real.pkl, made by fz10c_real_capture.py).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_real11_gen.py

The real logit_scored_valid is 45,000 rows x 44 columns. The step reads the column names ("default_flag" in
columns) and the two key columns only (group_by keys; the aggregate is pl.len()). The Lean input is the projection
on [default_flag (Float64), pred_logistic (Int64)] in the real column order, the 45,000 rows in the real row order,
encoded as 3 rows per base64 character (code = 2 * default_flag + pred_logistic; every value is 0 or 1, no null:
asserted) and decoded inside Lean. Asserted here: the source lines of the step run on the projection give exactly
the confusion_matrix and validation_metrics the real run produced on the full frame (and printed_confusion_validation
.csv). Lean returns [dg (tR input), dg (tR confusion_matrix), dg (tR validation_metrics)].
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import fz10c_train_gen as g  # noqa: E402  (sets the carrier def:zz_carrier_fid_2)
import compare as cmp  # noqa: E402
from suite import Suite  # noqa: E402

AL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-./"  # 64 symbols, no digit, no quote/backslash

r = pickle.loads((HERE.parent / "work" / "fz10c_real.pkl").read_bytes())
i11, o11 = r["s11"]
full = i11["logit_scored_valid"]
proj = full.select(["default_flag", "pred_logistic"])
assert proj.schema == {"default_flag": pl.Float64, "pred_logistic": pl.Int64}
d, p = proj.get_column("default_flag").to_list(), proj.get_column("pred_logistic").to_list()
assert all(v in (0.0, 1.0) for v in d) and all(v in (0, 1) for v in p)
cm, vm = g.run11(proj)
assert cmp.canon_frame(cm) == cmp.canon_frame(o11["confusion_matrix"])
assert cmp.canon_frame(vm) == cmp.canon_frame(o11["validation_metrics"])
cm_full, vm_full = g.run11(full)
assert cmp.canon_frame(cm_full) == cmp.canon_frame(cm) and cmp.canon_frame(vm_full) == cmp.canon_frame(vm)


def encode(fr: pl.DataFrame) -> tuple[str, int]:
    dd, pp = fr.get_column("default_flag").to_list(), fr.get_column("pred_logistic").to_list()
    codes = [2 * int(x) + y for x, y in zip(dd, pp)]
    n = len(codes)
    pad = codes + [0] * (-n % 3)
    groups = [pad[k] * 16 + pad[k + 1] * 4 + pad[k + 2] for k in range(0, len(pad), 3)]
    # S: a run of k all-zero groups is the decimal k; any other group is its symbol (so S has no "A")
    parts, zeros = [], 0
    for v in groups:
        if v == 0:
            zeros += 1
        else:
            parts.append((str(zeros) if zeros else "") + AL[v])
            zeros = 0
    S = "".join(parts) + (str(zeros) if zeros else "")
    # the decoder, mirrored: S gives back the groups
    st0, acc = 0, []
    for ch in S:
        if ch.isdigit():
            st0 = st0 * 10 + int(ch)
        else:
            acc += [0] * st0 + [AL.index(ch)]
            st0 = 0
    acc += [0] * st0
    assert acc == groups
    return S, n


def lets_of(S: str, n: int) -> str:
    return (
        f'let AL : List Char := "{AL}".toList; let S : String := "{S}"; '
        "let st : Nat × List Nat := S.toList.foldl (fun (st : Nat × List Nat) (c : Char) => if c.isDigit then (st.1 * 10 + (c.toNat - 48), st.2) "
        "else ((0 : Nat), AL.findIdx (fun (a : Char) => a == c) :: (List.replicate st.1 (0 : Nat) ++ st.2))) ((0 : Nat), ([] : List Nat)); "
        "let groups : List Nat := List.reverse (List.replicate st.1 (0 : Nat) ++ st.2); "
        "let codes : List Nat := (groups.flatMap "
        f"(fun (v : Nat) => [v / 16, (v / 4) % 4, v % 4])).take {n}; "
        'let fr : Pl.Frame Float := [("default_flag", Pl.Col.f64 (codes.map (fun (k : Nat) => some (if k / 2 == 1 then 1.0 else 0.0)))), '
        '("pred_logistic", Pl.Col.int (codes.map (fun (k : Nat) => some ((k % 2 : Nat) : Int))))]; '
        "let r := train_run_11_confusion_valid fr; "
    )


# The whole frame (45,000 rows) was sent once and the call timed out: the unit's Lean is superlinear in the rows
# under eval_decl (measured on synthetic frames of the same two columns: 2,000 rows 0.4 s, 12,000 rows 2.8 s,
# 24,000 rows 31 s). Every real row is therefore evaluated in one of four consecutive windows of the real frame,
# each a real input in its own right (the real rows, in the real order); the whole-frame result is not evaluated.
s = Suite("fz10c_cv_real", generator=g.GENERATOR.replace("fz10c_train_gen", "fz10c_real11_gen"))
WIN = [(0, 12000), (12000, 12000), (24000, 12000), (36000, 9000)]
for a0, ln in WIN:
    w = proj.slice(a0, ln)
    cmw, vmw = g.run11(w)
    S, n = encode(w)
    note = {"fz": "kept"}
    s.ints(lets_of(S, n), "[dg (tR fr), dg (tR r.1), dg (tR r.2)]", [
        (f"real rows {a0}..{a0 + ln - 1}: input", g.U11, cmp.digest(cmp.tokens(cmp.canon_frame(w))), note),
        (f"real rows {a0}..{a0 + ln - 1}: confusion_matrix", g.U11, cmp.digest(cmp.tokens(cmp.canon_frame(cmw))), note),
        (f"real rows {a0}..{a0 + ln - 1}: validation_metrics", g.U11, cmp.digest(cmp.tokens(cmp.canon_frame(vmw))), note)],
        table=False)
    print(a0, ln, len(S), cmw.rows(), vmw.rows())
s.write()
n = proj.height
print("rows", n, "chars of S", len(S), "printed:", list(r["printed"]))
print(cm, vm)
