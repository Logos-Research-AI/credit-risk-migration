"""Receipt rows of the glue-end-to-end pass (2026-11-20) from work/fz10_glue_seeds_*.jsonl and
work/fz10_glue_real.jsonl -> receipts/fuzz_2026-11-20-glue-end-to-end.tsv (columns of fuzz_2026-11-19.tsv).
  cd migration/port-to-lean && python3 diffeval/units/fz10_glue_end_to_end_receipt.py"""
import collections, json
from pathlib import Path
W = Path(__file__).resolve().parent.parent / "work"
OUT = Path(__file__).resolve().parent.parent / "receipts" / "fuzz_2026-11-20-glue-end-to-end.tsv"
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
GEN = "diffeval/units/fz10_glue_end_to_end_gen.py"
FZ = "port-translator (fidelity pass glue-end-to-end 2026-11-20)"
FAM = [(1000, 300), (5000, 150), (7000, 100), (9000, 100), (11000, 100)]
seeds = [json.loads(l) for s0, _ in FAM for l in open(W / f"fz10_glue_seeds_{s0}.jsonl")]
real = [json.loads(l) for l in open(W / "fz10_glue_real.jsonl")]
SEEDS = ", ".join(f"{a}..{a + n - 1}" for a, n in FAM) + " + legacy/data"
raised = [d for d in seeds if d.get("raised")]
rk = collections.Counter(next(d[s] for s in ("fe", "train", "predict", "metrics") if str(d[s]).startswith("raised"))[:30] for d in raised)
runs = [d for d in seeds if not d.get("raised")] + real
stops = sum(1 for d in runs if d["fe"] != "completed")
nofit = sum(1 for d in runs if d["fe"] == "completed" and d["train"] == "completed" and not d["fitted"])
fit = sum(1 for d in runs if d["fitted"])
H = "unit\tfuzzer\tseeds\tgenerated\tkept\tshare_kept\tcompared_kept\tdifferences\tnarrowings\tpython_raises_inside_precondition\tstatus\tnote\tblueprint\tgenerator"
base = (f"Python side only (real port, HEAD 4a757fb, four stages each reading the files the stage before wrote); "
        f"{len(seeds)} seeded inputs + legacy/data (150,000 rows, inputs/split_ids.csv); runs: {fit} fitted, {nofit} without fit, "
        f"{stops} where feature engineering stops (and train, predict, metrics stop after it); {len(raised)} seeded runs where a stage "
        f"raises are not compared ({dict(rk)})")
rows = []
rows.append(["pyPipeline (Lean, all fields)", FZ, "none", 0, 0, "n/a", 0, "n/a", "n/a", "n/a", "BLOCKED",
             "NOTHING COMPARED IN LEAN: def:pyPipeline is noncomputable (CreditRisk.Pipeline over the reals); eval_decl refuses (output-schema error, "
             "the refusal path of diffeval/eval_decl-errors-2026-11-18.md section 1) on every item whose cone holds a field: def:run, def:run_py_py_py, "
             "def:run_py_py, def:run_py, def:pyPipeline, def:train_run_04_score_train, def:train_run_10_score_valid, def:train_run_14_final_and_summary, "
             "def:predict_run_08_outputs, def:metrics_run_09_model_performance (probed 2026-11-20 with input \"1\"; control def:_hl_groups returns [12, 6]); "
             "the carriers def:zz_carrier* are no longer in the blueprint and none was added (rule of this pass)", BP, GEN])
def row(unit, key, cond, note):
    sel = [d for d in runs if cond(d)]
    diff = sum(1 for d in sel if d.get(key) is False)
    rows.append([unit, FZ, SEEDS, len(seeds) + len(real), len(sel), f"{len(sel) / (len(seeds) + len(real)):.3f}", len(sel), diff, 0, "n/a",
                 "PY-ONLY PASS (no Lean)" if diff == 0 else "PY-ONLY DIFF (no Lean)", note + "; " + base, BP, GEN])
row("glue G1 features (pyPipeline.features)", "G1", lambda d: True,
    "PY-WIRING, not Lean: model_features_train/validation.csv written exactly when fe completes; the ids the split draws from (credit_features.row_id) are the imported VAR1 cells (multiset of float bits), as pyPipeline passes cleaned.getF \"VAR1\" to py.split")
row("glue G2 fit (pyPipeline.fit, PyLinks 7 coefExists)", "G2", lambda d: True,
    "PY-WIRING, not Lean: model.json written exactly when both feature files exist and the stepwise has a final fit; its intercept is a float; model_coefficients.csv exists exactly when model.json does")
row("glue G3 no-fit S2 = [] (ScoreRun)", "G3", lambda d: d.get("G3") is not None,
    "PY-WIRING, not Lean: on every run without fit risk_scores_validation.csv is written with no row")
kept4 = lambda d: d.get("G4") is not None and d.get("pre04", True)
rej4 = [d for d in runs if d.get("G4") is not None and not d.get("pre04", True)]
row("glue G4 ScoreRun S1 = pyPipeline.score m F1 vs risk_scores_train.csv", "G4", kept4,
    "PY-CHAIN, not Lean: the port's own validation chain (train.py 609-635, 771-800, drop_sas_names) on the training feature file, with the same stepwise result replayed, "
    "bit for bit against the port's risk_scores_train.csv frame (names, dtypes, float bits, null vs NaN, order); real data 105,000 rows equal. "
    f"REJECTED and DIFFERENT: {len(rej4)} inputs of family 11000 (seeds {[d['case'] for d in rej4]}), each outside the last clause of def:train_run_04_score_train_precond "
    "(narrowing, RULEBOOK Convention 1: exp(-eta) finite on every training row): one training row left out of the fit (utilization_debt_interaction missing) with num_credit_lines 1e80..1e300; "
    "port pd_logistic 0.0 (polars exp overflows to inf, 1/(1+inf)), glue null (sas_exp), so credit_risk_score 850 vs null, risk_grade A vs F, recommendation Approve vs Decline, interest_rate 0.05 vs 0.2; "
    "minimal input diffeval/work/fz10_glue_G4_min (18 rows)")
row("glue G5 medians flag (PyLinks 7 mediansExist)", "G5", lambda d: True,
    "PY-WIRING, not Lean: income_medians.csv written exactly when fe completes")
row("glue G6 metrics lookups (pyPipeline.metrics)", "G6", lambda d: d.get("G6") is not None,
    "PY-WIRING, not Lean: when metrics completes, validation_summary.csv and threshold_analysis.csv are among its files")
OUT.write_text(H + "\n" + "\n".join("\t".join(str(x) for x in r) for r in rows) + "\n")
print(OUT.read_text())
