"""Update 2026-11-17: def:train_run_15_printed_roc_precond, the narrowing on ROC labels that are
all null (RULEBOOK section 6), by port-translator-8. Blueprint 5365851c-5549-44b7-9207-4bd4c422031d.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t15p_gen.py
      -> diffeval/work/t15p_labels.json and .inputs.json
  eval_decl each input on def:zz_carrier_t / zz_carrier_t; python3 diffeval/fuzz_collect.py 8 t15p_labels;
  then diffeval/compare.py on work/t15p_labels.json and work/t15p_labels.out.txt, and
  diffeval/receipts.py units t15p

The inputs are those of port-translator-7's fuzz of step 15 (diffeval/units/fz_td_gen.py: the same
seeds 400000 to 402399, the same frames built from the seed on both sides, the same sas_d8 table),
but one seed at a time instead of folded by class. Python: lines 823-842 of credit_risk/train.py
through td_gen.run_slice (the real code, the real write_sas_csv recorded).
The new clause as a Boolean (a Prop cannot be evaluated):
    cl = nn roc_train && (!roc_valid_created || nn roc_valid)
    nn fr = fr has no row, or some ROCModel label is not null
Per seed the Lean returns
  - a code: 4 TauA Int64 (rejected by the precondition as it was), 1 roc_train fails nn,
    2 roc_valid fails nn, 8 roc_valid_created, 16 the clause holds; computed on the Lean frames and
    compared with the same code computed on the polars frames;
  - when the clause holds: the digest of the unit's output, compared with the digest of the files
    Python writes (the unit and Python agree inside the narrowed precondition);
  - when the clause fails: 1 when the digest of the unit's output differs from Python's digest
    (handed to the Lean as a literal), else 0; expected 1 (every excluded input is a real difference).
So the suite passes exactly when the clause excludes all the differing inputs and no agreeing one.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import fz_td_gen as fz  # noqa: E402  (carrier def:zz_carrier_t; frames, pools and digests of the fuzz)
import td_gen as td  # noqa: E402
from suite import Suite  # noqa: E402

UNIT = "train_run_15_printed_roc_precond"
S0, BLOCK, NBLOCK = fz.S15, 400, 6
PRE = fz.LETS15[:fz.LETS15.index("let ONE := ")]
NN = ('let nn := fun (fr : Pl.Frame Float) => (match fr.lookup "ROCModel" with '
      "| some (.str v) => v.isEmpty || v.any (fun (x : Option String) => x.isSome) | _ => true : Bool); ")
ONE = (
    "let ONE := fun (s : Nat) => let ti := H s 9103 12 == 0; let cr := H s 9100 2 == 0; "
    'let rt := ROC (s * 8 + 1) "Training Set" false; let rv := ROC (s * 8 + 2) "Validation Set" ti; '
    "let cl := nn rt && (!cr || nn rv); "
    "let code : Int := (if ti then 4 else 0) + (if nn rt then 0 else 1) + (if nn rv then 0 else 2) + (if cr then 8 else 0) + (if cl then 16 else 0); "
    "(if ti then [code] else let d : Int := OUT (train_run_15_printed_roc d8 (CM (s * 8 + 3)) (CM (s * 8 + 4)) rt rv cr); "
    "if cl then [code, d] else [code, (if d == (P.lookup s).getD 0 then 0 else 1)] : List Int); "
)


def nn(f) -> bool:
    return f.height == 0 or f["ROCModel"].null_count() < f.height


def main() -> None:
    st = Suite("t15p_labels", generator="port-to-lean/diffeval/units/t15p_gen.py")
    n = {"rejected": 0, "inside": 0, "excluded": 0, "valid null, not created (inside)": 0, "class of the fuzz": 0}
    for b in range(NBLOCK):
        s0 = S0 + b * BLOCK
        cases, lit = [], []
        for s in range(s0, s0 + BLOCK):
            e = fz.env15(s)
            ti, cr = not fz.pre15(e), bool(e["roc_valid_created"])
            a, v = nn(e["roc_train"]), nn(e["roc_valid"])
            cl = a and (not cr or v)
            code = (4 if ti else 0) + (0 if a else 1) + (0 if v else 2) + (8 if cr else 0) + (16 if cl else 0)
            cases.append((f"seed {s}: classes", UNIT + " (classes)", code))
            if ti:
                n["rejected"] += 1
                continue
            _, writes, _ = td.run_slice("s15", e)
            d = fz.out_digest(writes)
            n["class of the fuzz"] += int(fz.all_null_label(e))
            if cl:
                n["inside"] += 1
                n["valid null, not created (inside)"] += int(not v)
                cases.append((f"seed {s}: inside, unit = Python", UNIT, d))
            else:
                n["excluded"] += 1
                lit.append(f"({s}, {d})")
                cases.append((f"seed {s}: excluded, unit differs from Python", UNIT + " (excluded inputs differ)", 1))
        body = f"(let P : List (Nat × Int) := [{', '.join(lit)}]; {ONE}(List.range' {s0} {BLOCK}).flatMap ONE)"
        st.ints(PRE + NN, body, cases, gen=True, table=True)
    st.notes = {UNIT: f"2026-11-17, blueprint 5365851c-5549-44b7-9207-4bd4c422031d: the narrowing clause (a ROC frame the step exports that has "
                      f"rows has a label that is not null) as a Boolean on the {NBLOCK * BLOCK} seeds of the fuzz fz_td15, one seed at a time, against "
                      f"lines 823-842 of train.py: {n['rejected']} rejected before (TauA Int64); {n['inside']} inside, unit = Python on each "
                      f"({n['valid null, not created (inside)']} of them with roc_valid all null and roc_valid_created false: no file, no difference); "
                      f"{n['excluded']} excluded, the unit differs from Python on each. The fuzz's class 'a ROC frame with rows whose labels are "
                      f"all null' holds {n['class of the fuzz']} inputs"}
    st.write()
    print(n, [len(i["text"]) for i in st.inputs])


if __name__ == "__main__":
    main()
