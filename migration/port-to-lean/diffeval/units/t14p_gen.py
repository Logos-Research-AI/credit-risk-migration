"""Update 2026-11-17: def:train_run_14_final_and_summary_precond, the clauses on the export formats
(RULEBOOK 2.7 G30), by port-translator-8. Blueprint 5365851c-5549-44b7-9207-4bd4c422031d.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t14p_gen.py
      -> diffeval/work/t14p_formats.json and .inputs.json
  eval_decl the input on def:zz_carrier_t / zz_carrier_t; python3 diffeval/fuzz_collect.py 8 t14p_formats;
  then diffeval/compare.py on work/t14p_formats.json and work/t14p_formats.out.txt, and
  diffeval/receipts.py units t14p_formats

One case = one set of the seven frames of step 14. Python: lines 725-819 of credit_risk/train.py
read from the file and executed with the module's globals and the REAL sas_compat.write_sas_csv
(writing into a temporary folder), with roc_valid_created true and false (the two must agree).
Expected 1 when the Python raises "ValueError: format ..." of sas_compat.py:645-650, 0 when it
returns five files; any other exception stops the generator.
Lean: the three new clauses of the precondition, written here as Booleans on the same frames
(a Prop cannot be evaluated): for risk_scores_train and risk_scores_validation a column
interest_rate that is not `.str`; for each of the ten "8.4" keys a column of
merge_one_to_one [roc_train.filter(..).select(Train_AUC), roc_valid.filter(..).select(Valid_AUC),
training_metrics, validation_metrics] that is not `.str` (the merge written as in the precondition
and the unit). The Lean integer is 1 when a clause fails, 0 when all hold. A second integer per
case is the digest of the six input frames, so both sides hold the same frames.
Cases: base; interest_rate of each scored set absent / text / Int64 / Null dtype / Float64 with
nulls; each of the eight metric columns absent / text; Area of each ROC frame text; a later merged
frame bringing a text Train_AUC; an earlier frame's text valid_recall replaced by a later numeric
one; a text training_date and an unformatted text column in a metrics frame; frames with no row.
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")
from suite import Suite  # noqa: E402

from credit_risk import train  # noqa: E402

UNIT = "train_run_14_final_and_summary_precond"
A, B = 725, 819
src = "".join(Path(train.__file__).read_text().splitlines(keepends=True)[A - 1:B])
assert src.lstrip().startswith("risk_scores_train_clean = risk_scores_train") and src.rstrip().endswith('"model_coefficients.csv", formats={})'), "line numbers moved"
CODE = compile(textwrap.dedent(src), f"train.py:{A}-{B}", "exec")
TM = ["train_precision", "train_recall", "train_f1_score", "train_accuracy"]
VM = ["valid_precision", "valid_recall", "valid_f1_score", "valid_accuracy"]
NAMES = ["risk_scores_train", "risk_scores_validation", "roc_train", "roc_valid", "training_metrics", "validation_metrics"]


def base() -> dict:
    rs = pl.DataFrame({"row_id": [1.0, 2.0], "default_flag": [0.0, 1.0], "pd_logistic": [0.25, 0.75], "interest_rate": [0.05, 0.12]})

    def roc(name):
        return pl.DataFrame({"ROCModel": [name], "Area": [0.75]})
    return {"risk_scores_train": rs, "risk_scores_validation": rs.head(1), "roc_train": roc("Training Set"),
            "roc_valid": roc("Validation Set"), "training_metrics": pl.DataFrame({k: [0.5] for k in TM}),
            "validation_metrics": pl.DataFrame({k: [0.25] for k in VM})}


def py(env: dict) -> int:
    out = []
    for created in (True, False):
        ns = dict(vars(train))
        ns.update(env)
        ns["model_coefficients"] = pl.DataFrame({"Variable": ["Intercept"], "Estimate": ["-1.0"]})
        ns["roc_valid_created"] = created
        with tempfile.TemporaryDirectory() as d:
            ns["output_dir"] = Path(d)
            try:
                exec(CODE, ns)
                assert len(list(Path(d).iterdir())) == 5
                out.append(0)
            except ValueError as e:
                assert str(e).startswith("format "), e
                out.append(1)
    assert out[0] == out[1]
    return out[0]


def text(df, c):
    return df.with_columns(pl.col(c).cast(pl.String))


def mod(fr, f):
    return lambda e: {**e, fr: f(e[fr])}


cases = [("base", lambda e: e)]
for fr in ("risk_scores_train", "risk_scores_validation"):
    cases += [
        (f"{fr}: interest_rate absent", mod(fr, lambda d: d.drop("interest_rate"))),
        (f"{fr}: interest_rate text", mod(fr, lambda d: text(d, "interest_rate"))),
        (f"{fr}: interest_rate Int64", mod(fr, lambda d: d.with_columns(pl.col("interest_rate").cast(pl.Int64)))),
        (f"{fr}: interest_rate Null dtype", mod(fr, lambda d: d.with_columns(interest_rate=pl.lit(None)))),
        (f"{fr}: interest_rate Float64 all null", mod(fr, lambda d: d.with_columns(interest_rate=pl.lit(None, dtype=pl.Float64)))),
        (f"{fr}: no row", mod(fr, lambda d: d.clear())),
        (f"{fr}: no row and interest_rate text", mod(fr, lambda d: text(d, "interest_rate").clear())),
    ]
for fr, keys in (("training_metrics", TM), ("validation_metrics", VM)):
    for k in keys:
        cases += [(f"{fr}: {k} absent", mod(fr, lambda d, k=k: d.drop(k))), (f"{fr}: {k} text", mod(fr, lambda d, k=k: text(d, k)))]
cases += [
    ("roc_train: Area text", mod("roc_train", lambda d: text(d, "Area"))),
    ("roc_valid: Area text", mod("roc_valid", lambda d: text(d, "Area"))),
    ("roc_train: Area Int64", mod("roc_train", lambda d: d.with_columns(pl.col("Area").cast(pl.Int64)))),
    ("validation_metrics brings a text Train_AUC", mod("validation_metrics", lambda d: d.with_columns(Train_AUC=pl.lit("x")))),
    ("training_metrics brings a text Valid_AUC", mod("training_metrics", lambda d: d.with_columns(Valid_AUC=pl.lit("x")))),
    ("training_metrics brings a numeric Train_AUC", mod("training_metrics", lambda d: d.with_columns(Train_AUC=pl.lit(0.5)))),
    ("training_metrics holds a text valid_recall, replaced by validation_metrics", mod("training_metrics", lambda d: d.with_columns(valid_recall=pl.lit("x")))),
    ("validation_metrics holds a text train_recall (replaces the numeric one)", mod("validation_metrics", lambda d: d.with_columns(train_recall=pl.lit("x")))),
    ("training_metrics: a text training_date and an unformatted text column", mod("training_metrics", lambda d: d.with_columns(training_date=pl.lit("x"), note=pl.lit("x")))),
    ("training_metrics and validation_metrics: no row", lambda e: {**e, "training_metrics": e["training_metrics"].clear(), "validation_metrics": e["validation_metrics"].clear()}),
    ("training_metrics: train_f1_score Null dtype", mod("training_metrics", lambda d: d.with_columns(train_f1_score=pl.lit(None)))),
]

LETS = (
    "let ok := fun (c : Option (Pl.Col Float)) => (match c with | some (.str _) => false | none => false | _ => true : Bool); "
    'let K := ["Train_AUC", "Valid_AUC", "train_precision", "train_recall", "train_f1_score", "train_accuracy", "valid_precision", "valid_recall", "valid_f1_score", "valid_accuracy"]; '
    "let chk := fun (rst rsv rt rv tm vm : Pl.Frame Float) => "
    'let m := merge_one_to_one [(rt.filter ((Pl.col "ROCModel").eq (Pl.litS "Training Set"))).select [("Train_AUC", Pl.col "Area")], '
    '(rv.filter ((Pl.col "ROCModel").eq (Pl.litS "Validation Set"))).select [("Valid_AUC", Pl.col "Area")], tm, vm]; '
    '[(if ok (rst.lookup "interest_rate") && ok (rsv.lookup "interest_rate") && List.all K (fun (k : String) => ok (m.lookup k)) then 0 else 1 : Int), '
    "dg (tR rst ++ tR rsv ++ tR rt ++ tR rv ++ tR tm ++ tR vm)]; "
)


def main() -> None:
    s = Suite("t14p_formats", generator="port-to-lean/diffeval/units/t14p_gen.py")
    raised = 0
    per = 9
    for k0 in range(0, len(cases), per):
        names: dict[str, str] = {}   # frame literal -> let name (frames shared by the cases are written once)
        terms, cs = [], []
        for name, f in cases[k0:k0 + per]:
            e = f(base())
            exp = py(e)
            raised += exp
            toks = []
            for n in NAMES:
                toks += cmp.tokens(cmp.canon_frame(e[n]))
            refs = [names.setdefault(lt.lean_frame_items(e[n]), f"f{len(names)}") for n in NAMES]
            terms.append("chk " + " ".join(refs))
            cs += [(f"{name}: " + ("Python raises" if exp else "Python returns"), UNIT, exp), (f"{name} / inputs", UNIT + " (input)", cmp.digest(toks))]
        frames = "".join(f"let {v} : Pl.Frame Float := {k}; " for k, v in names.items())
        s.ints(LETS + frames, " ++ ".join(terms), cs, table=False)
    s.notes = {UNIT: f"2026-11-17, blueprint 5365851c-5549-44b7-9207-4bd4c422031d: the three format clauses (G30) as Booleans on {len(cases)} "
                     f"sets of frames against lines 725-819 of train.py with the real write_sas_csv, roc_valid_created true and false: "
                     f"the Python raises on {raised} and returns on {len(cases) - raised}; interest_rate absent / text / Int64 / Null / null, "
                     f"each metric absent / text, Area text, later merged frames replacing a column, frames with no row"}
    s.write()
    print(len(cases), "cases,", raised, "raise;", [len(i["text"]) for i in s.inputs])


if __name__ == "__main__":
    main()
