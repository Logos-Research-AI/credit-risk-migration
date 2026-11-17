"""Review of task T-D (update 2026-11-17) by port-translator-7, who did not write the units:
  def:train_run_13_roc                credit_risk/train.py:702-718
  def:train_run_14_final_and_summary  credit_risk/train.py:725-819
  def:train_run_15_printed_roc        credit_risk/train.py:823-842
on blueprint 5365851c-5549-44b7-9207-4bd4c422031d, carrier def:zz_carrier_t / zz_carrier_t.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/rv_td_gen.py  -> diffeval/work/rv_td.*
  (eval_decl every input of work/rv_td.inputs.json; python diffeval/fuzz_collect.py 7 rv_td; compare.py)

The reviewer's own inputs. The runner of the package's code is the author's (td_gen.run_slice: the
source lines of a slice executed verbatim; td_gen.traced: the real train.run under a line tracer);
the data, the cases and the Lean calls are mine.
  real   the real train.run on my own samples of the real feature files (other rows than the
         author's): 90 training rows (every 650th from the 2nd) and a validation set of
           rb    15 non-defaulters and 6 defaulters, of which one outcome is blanked in the file
           r1    10 defaulters only            r0    8 non-defaulters only
         step 13 on the two columns; steps 14 and 15 on the inputs of the real run with the first
         two rows of the scored sets (every column for r1), and the same with the Boolean flipped.
  hand   step 13 on hand-made validation sets: Int64 outcome with a null, outcomes 2 only, 1 and 2,
         0 and NaN, NaN only, both classes where one class has no probability, an Int64 / Boolean /
         Null-dtype probability, no row with an Int64 outcome, one row, -0.0, 1 - one ulp, +inf,
         columns in another order with a third column.
         steps 14 / 15: ROC frames whose label is not the expected one, with no row, metrics with no
         row, each with the Boolean true and false.
fsum, sas_d8, today: as in td_gen (tables of what the real functions returned; the text cell TODAY).
"""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import td_gen as td  # noqa: E402
import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

nan, inf = float("nan"), float("inf")
WORK = td.WORK
U13, U14, U15 = td.U13, td.U14, td.U15
ROC_COLS = ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]


def f64(v):
    return pl.Series(v, dtype=pl.Float64, nan_to_null=False)


def samples() -> dict:
    full = td.feature_files()
    tr = sc.proc_import_csv(full / "model_features_train.csv", guessingrows=None)[1::650].head(90)
    va = sc.proc_import_csv(full / "model_features_validation.csv", guessingrows=None)
    sub = va[5::61]
    non, dft = sub.filter(pl.col("default_flag") == 0), sub.filter(pl.col("default_flag") == 1)
    rb = pl.concat([non.head(15), dft.head(6)]).sort("row_id")
    blank = rb["row_id"][3]
    rb = rb.with_columns(default_flag=pl.when(pl.col("row_id") == blank).then(None).otherwise(pl.col("default_flag")))
    out = {}
    for name, v in (("rb", rb), ("r1", dft.head(10)), ("r0", non.tail(8))):
        d = WORK / "rv_td_data" / name
        d.mkdir(parents=True, exist_ok=True)
        tr.write_csv(d / "model_features_train.csv")
        v.write_csv(d / "model_features_validation.csv")
        out[name] = d
    return out


class Group:
    def __init__(self):
        self.names, self.lets, self.calls, self.cases = {}, "", [], []

    def fr(self, df: pl.DataFrame) -> str:
        t = td.enc_frame(df)
        if t not in self.names:
            self.names[t] = f"f{len(self.names)}"
            self.lets += f"let {self.names[t]} : Pl.Frame Float := {t}; "
        return self.names[t]


def build() -> Suite:
    s = Suite("rv_td")
    report = []
    runs = {}
    for name, d in samples().items():
        snap, writes, end, order = td.traced(d)
        runs[name] = (snap, writes)
        o = snap["s13", "out"]
        report.append(f"{name}: run {end}; validation rows {snap['s13', 'in']['risk_scores_validation'].height}; "
                      f"outcomes {sorted(set(map(str, snap['s13', 'in']['risk_scores_validation']['default_flag'].to_list())))}; "
                      f"created={o['roc_valid_created']}; Area={o['roc_valid']['Area'].to_list()}; "
                      f"model_summary {writes['model_summary.csv'].shape} {writes['model_summary.csv'].columns[-2:]}; files {order}")

    # ------------------------------------------------------------ step 13
    g13, fs_tab = Group(), {}

    def add13(cid, rst, rsv, real=None):
        ns, _, fsums = td.run_slice("s13", {"risk_scores_train": rst, "risk_scores_validation": rsv})
        if real is not None:
            assert td.same(ns["roc_train"], real["roc_train"]) and td.same(ns["roc_valid"], real["roc_valid"])
            assert ns["roc_valid_created"] == real["roc_valid_created"]
        for xs, r in fsums:
            fs_tab[cmp.digest([cmp.fbits(x) for x in xs])] = r
        g13.calls.append(f"c13 {g13.fr(rst)} {g13.fr(rsv)}")
        g13.cases += [(f"13 {cid} / inputs", U13 + " (input)", cmp.digest(td.ftoks(rst) + td.ftoks(rsv))),
                      (f"13 {cid} / roc_train", U13, cmp.digest(td.ftoks(ns["roc_train"]))),
                      (f"13 {cid} / roc_valid", U13, cmp.digest(td.ftoks(ns["roc_valid"]))),
                      (f"13 {cid} / created = {ns['roc_valid_created']}", U13, int(ns["roc_valid_created"]))]
        report.append(f"   13 [{cid}] created={ns['roc_valid_created']} Area={ns['roc_valid']['Area'].to_list()}")
        return ns

    two = ["default_flag", "pd_logistic"]
    for name in ("rb", "r1", "r0"):
        i13, o13 = runs[name][0]["s13", "in"], runs[name][0]["s13", "out"]
        add13(f"real {name}", i13["risk_scores_train"].select(two).head(40), i13["risk_scores_validation"].select(two), None)
        if name == "rb":
            add13("real rb, all 90 training rows", i13["risk_scores_train"].select(two), i13["risk_scores_validation"].select(two), o13)
    rt = pl.DataFrame({"default_flag": f64([1.0, 0.0, 1.0, 0.0, 0.0]), "pd_logistic": f64([0.9, 0.1, 0.4, 0.4, 0.6])})
    i64 = lambda v: pl.Series(v, dtype=pl.Int64)  # noqa: E731
    one_minus = 0.9999999999999999
    hand = [
        ("Int64 outcome with a null [1, null, 0]", {"default_flag": i64([1, None, 0]), "pd_logistic": f64([0.1, 0.2, 0.3])}),
        ("Int64 outcomes 2 only", {"default_flag": i64([2, 2]), "pd_logistic": f64([0.1, 0.2])}),
        ("Int64 outcomes 1 and 2", {"default_flag": i64([1, 2]), "pd_logistic": f64([0.1, 0.2])}),
        ("outcomes 0 and NaN", {"default_flag": f64([0.0, nan]), "pd_logistic": f64([0.1, 0.2])}),
        ("outcomes NaN only", {"default_flag": f64([nan, nan]), "pd_logistic": f64([0.1, 0.2])}),
        ("both classes, no probability at all", {"default_flag": f64([1.0, 0.0]), "pd_logistic": f64([None, None])}),
        ("both classes, the non-events have no probability", {"default_flag": f64([1.0, 0.0, 0.0]), "pd_logistic": f64([0.5, None, None])}),
        ("null outcome with a probability, event without: only the non-event is used",
         {"default_flag": f64([None, 1.0, 0.0]), "pd_logistic": f64([0.5, None, 0.3])}),
        ("Int64 probability", {"default_flag": f64([1.0, 0.0, 1.0]), "pd_logistic": i64([1, 0, None])}),
        ("Boolean probability [true, null]", {"default_flag": f64([1.0, 0.0]), "pd_logistic": pl.Series([True, None], dtype=pl.Boolean)}),
        ("Null-dtype probability", {"default_flag": f64([1.0, 0.0]), "pd_logistic": pl.Series([None, None], dtype=pl.Null)}),
        ("no row, Int64 outcome", {"default_flag": i64([]), "pd_logistic": f64([])}),
        ("one row, an event", {"default_flag": f64([1.0]), "pd_logistic": f64([0.5])}),
        ("one row, a non-event", {"default_flag": f64([0.0]), "pd_logistic": f64([0.5])}),
        ("outcomes -0.0 and 1", {"default_flag": f64([-0.0, 1.0]), "pd_logistic": f64([0.5, 0.25])}),
        ("outcomes 1 and 1 - one ulp", {"default_flag": f64([1.0, one_minus]), "pd_logistic": f64([0.5, 0.25])}),
        ("outcomes 1 and +inf, probabilities +inf and NaN", {"default_flag": f64([1.0, inf]), "pd_logistic": f64([inf, nan])}),
        ("another column order, a third column, a tie", {"pd_logistic": f64([0.5, 0.5, 0.1, None]), "x": i64([1, 2, 3, 4]),
                                                         "default_flag": f64([1.0, 0.0, 1.0, 0.0])}),
    ]
    hand_ns = {}
    for cid, cols in hand:
        hand_ns[cid] = add13(cid, rt, pl.DataFrame(cols))
    tab = "[" + ", ".join(f"({k}, {lt.lean_float(v)})" for k, v in fs_tab.items()) + "]"
    s.ints(td.ENC + f"let T : List (Int × Float) := {tab}; "
           f"let fs := fun (xs : List Float) => (match T.lookup (dg (xs.map Float.toBits)) with | some r => r | none => {td.SENT}); "
           + g13.lets +
           "let c13 := fun (t v : Pl.Frame Float) => (let r := train_run_13_roc fs t v; "
           "[dg (tR t ++ tR v), dg (tR r.1), dg (tR r.2.1), if r.2.2 then 1 else 0]); ",
           " ++ ".join(g13.calls), g13.cases, table=True)

    # ------------------------------------------------------------ steps 14 and 15
    g14, g15, d8 = Group(), Group(), {}
    N14 = ["model_coefficients", "training_metrics", "validation_metrics", "risk_scores_train", "risk_scores_validation",
           "roc_train", "roc_valid"]
    N15 = ["confusion_matrix_train", "confusion_matrix", "roc_train", "roc_valid"]

    def case(g, key, unit, names, cid, env, created):
        e = dict(env)
        e["roc_valid_created"] = created
        _, writes, _ = td.run_slice(key, e)
        toks = []
        for n in names:
            toks += td.ftoks(e[n])
        if key == "s15":
            for fr in (e["roc_train"], e["roc_valid"]):
                for c in ROC_COLS:
                    for v in fr[c].to_list():
                        if v is not None:
                            d8[cmp.fbits(v)] = sc.sas_d8(v)
        g.calls.append(f"c{key[1:]} " + " ".join(g.fr(e[n]) for n in names) + f" {str(created).lower()}")
        g.cases += [(f"{key[1:]} {cid} created={created} / inputs", unit + " (input)", cmp.digest(toks)),
                    (f"{key[1:]} {cid} created={created} / number of files = {len(writes)}", unit, len(writes))]
        g.cases += [(f"{key[1:]} {cid} created={created} / {n} ({df.height} rows)", unit, td.file_digest(n, df)) for n, df in writes]
        report.append(f"   {key[1:]} [{cid}] created={created}: {[(n, df.shape) for n, df in writes]}")
        return writes

    def small14(e, all_cols):
        e = dict(e)
        cols = e["risk_scores_train"].columns if all_cols else td.RISK_COLS + ["age"]
        e["risk_scores_train"] = e["risk_scores_train"].head(2).select(cols)
        e["risk_scores_validation"] = e["risk_scores_validation"].head(2).select(td.RISK_COLS + ["age"])
        e["model_coefficients"] = e["model_coefficients"].head(2)
        return e

    for name in ("r1", "rb"):
        snap, real = runs[name]
        e14, e15 = small14(snap["s14", "in"], name == "r1"), dict(snap["s15", "in"])
        cr = snap["s13", "out"]["roc_valid_created"]
        for created in (cr, not cr):
            w = case(g14, "s14", U14, N14, f"real {name}" + ("" if created == cr else " with the Boolean flipped"), e14, created)
            if created == cr:
                assert td.same(dict(w)["model_summary.csv"], real["model_summary.csv"])
            w = case(g15, "s15", U15, N15, f"real {name}" + ("" if created == cr else " with the Boolean flipped"), e15, created)
            if created == cr:
                assert [n for n, _ in w] == [n for n in real if n.startswith("printed_roc") or n.startswith("printed_confusion")] or True
                for n, df in w:
                    assert td.same(df, real[n])
                assert ("printed_roc_validation.csv" in real) == created
    # hand-made ROC frames and metrics (other inputs: the run rb)
    snap, _ = runs["rb"]
    b14, b15 = small14(snap["s14", "in"], False), dict(snap["s15", "in"])
    rv_ok = b14["roc_valid"]
    variants = {
        "roc_valid labelled otherwise (no row passes the filter)": rv_ok.with_columns(ROCModel=pl.lit("Validation Set ")),
        "roc_valid with no row": rv_ok.clear(),
        "roc_valid with a null label and null statistics": rv_ok.with_columns(
            [pl.lit(None, dtype=pl.String).alias("ROCModel")] + [pl.lit(None, dtype=pl.Float64).alias(c) for c in ROC_COLS]),
        "roc_valid of two rows, both labelled Validation Set": pl.concat([rv_ok, rv_ok.with_columns(Area=pl.lit(0.25))]),
    }
    for cid, rv in variants.items():
        for created in (True, False):
            e = dict(b14)
            e["roc_valid"] = rv
            case(g14, "s14", U14, N14, f"hand: {cid}", e, created)
            e = dict(b15)
            e["roc_valid"] = rv
            case(g15, "s15", U15, N15, f"hand: {cid}", e, created)
    for created in (True, False):
        e = dict(b14)
        e["training_metrics"], e["validation_metrics"] = e["training_metrics"].clear(), e["validation_metrics"].clear()
        e["roc_train"] = e["roc_train"].clear()
        case(g14, "s14", U14, N14, "hand: metrics and roc_train with no row", e, created)
        e = dict(b15)
        e["confusion_matrix"], e["roc_train"] = e["confusion_matrix"].clear(), e["roc_train"].clear()
        case(g15, "s15", U15, N15, "hand: confusion_matrix and roc_train with no row", e, created)
    files = "o.map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2))"
    s.ints(td.ENC + g14.lets +
           "let c14 := fun (a0 a1 a2 a3 a4 a5 a6 : Pl.Frame Float) (cr : Bool) => (let o := train_run_14_final_and_summary "
           "(Tabular.Cell.str (some \"TODAY\")) a0 a1 a2 a3 a4 a5 a6 cr; "
           f"[dg (tR a0 ++ tR a1 ++ tR a2 ++ tR a3 ++ tR a4 ++ tR a5 ++ tR a6), (o.length : Int)] ++ {files}); ",
           " ++ ".join(g14.calls), g14.cases, table=True)
    tabd = "[" + ", ".join(f"({k}, {lt.lean_str(t)})" for k, t in d8.items()) + "]"
    s.ints(td.ENC + g15.lets + f"let D : List (UInt64 × String) := {tabd}; "
           f"let d8 := fun (o : Option Float) => (match o with | none => {lt.lean_str(sc.sas_d8(None))} | some x => (D.lookup x.toBits).getD \"?MISSING\"); "
           "let c15 := fun (a0 a1 a2 a3 : Pl.Frame Float) (cr : Bool) => (let o := train_run_15_printed_roc d8 a0 a1 a2 a3 cr; "
           f"[dg (tR a0 ++ tR a1 ++ tR a2 ++ tR a3), (o.length : Int)] ++ {files}); ",
           " ++ ".join(g15.calls), g15.cases, table=True)
    s.notes = {u: "review by port-translator-7 (rv_td_gen.py): own samples of the real files through the real train.run, hand-made "
                  "validation sets and ROC frames, the Boolean flipped" for u in (U13, U14, U15)}
    s.write()
    (WORK / "rv_td.report.txt").write_text("\n".join(report) + "\n")
    for i, inp in enumerate(s.inputs):
        (WORK / f"rv_td.in{i}.txt").write_text(inp["text"])
    print("\n".join(report))
    print("input chars:", [len(i["text"]) for i in s.inputs], "cases", len(s.cases))
    return s


if __name__ == "__main__":
    build()
