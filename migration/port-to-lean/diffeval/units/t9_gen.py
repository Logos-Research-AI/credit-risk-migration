"""port-translator-9, update 2026-11-16: differential tests of
  def:predict_run_07_predictions, def:predict_run_08_outputs (T10), def:train_run_12_risk_scores (T17).

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t9_gen.py
      -> diffeval/work/t9_predict, t9_train (.json + .inputs.json)
  eval_decl each input on def:zz_carrier_p / def:zz_carrier_t, outputs one per line in
  diffeval/work/t9_<suite>.out.txt, then diffeval/compare.py.

Expected values are what the PORT produced, never recomputed here:
  real    the locals of the real predict.run / train.run at return (profile hook), saved by
          units/t9_realrun.py (legacy/data, whole pipeline) and computed here for the scenarios
          fix_round5/test_header_age_upper, test_header_all_upper (whole pipeline) and for a train
          run on the real feature files with one model variable blanked in three rows (null pd).
          The steps are row-wise, so the Lean runs on chosen rows of the frame the port's step
          read and is compared with the same rows of the frame the port's step produced:
          `wide` = every column, a few rows; `narrow` = the columns the step reads plus row_id /
          age / default_flag, many rows (all rows next to the five grade cuts and 0.5).
  hand    the step's source lines read from the file and executed verbatim on hand-made frames
          (null, NaN, signed zeros, infinities, the cuts and their neighbours, one row, no row).
The first digest of every input is the input frame itself (guards the transcription).
"""
from __future__ import annotations
import contextlib, io, math, shutil, sys, textwrap
from pathlib import Path
import polars as pl

HERE = Path(__file__).resolve().parent
PTL = HERE.parents[1]
ROOT = PTL.parents[1]
sys.path.insert(0, str(HERE.parent))
import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402
from credit_risk import feature_engineering as fe, train as tr, predict as pr  # noqa: E402

W = PTL / "diffeval" / "work" / "t9"
SC = ROOT / "judge" / "scenarios"
nan, inf = float("nan"), float("inf")
U07, U08, U12 = "predict_run_07_predictions", "predict_run_08_outputs", "train_run_12_risk_scores"
CUTS = [0.10, 0.15, 0.25, 0.35, 0.50]
NEW = ["base_score", "score_range", "credit_risk_score", "risk_grade", "recommendation", "base_rate", "interest_rate"]
KEEP_FULL = ["row_id", "pd_logistic", "pred_logistic", "credit_risk_score", "risk_grade", "recommendation",
             "interest_rate", "age", "monthly_income", "credit_utilization", "debt_ratio", "total_late_payments",
             "num_credit_lines", "financial_health", "total_risk_flags"]

ENC = (
    "let oF := fun (s : String) => (s.splitOn \",\").map (fun (x : String) => (x.toNat?).map (fun (n : Nat) => Float.ofNat n)); "
    "let bF := fun (s : String) => (s.splitOn \",\").map (fun (x : String) => (x.toNat?).map (fun (n : Nat) => Float.ofBits n.toUInt64)); "
    "let oI := fun (s : String) => (s.splitOn \",\").map (fun (x : String) => x.toInt?); "
)


def col(s: pl.Series) -> str:
    v = s.to_list()
    k = lt.col_kind(s.dtype)
    if not v or k == "str":
        return lt.lean_col(s)
    if k == "f64":
        if all(x is None or (x == x and x >= 0 and x == int(x) and x < 2**53 and lt.bits(x) != lt.bits(-0.0)) for x in v):
            return '(Pl.Col.f64 (oF "' + ",".join("n" if x is None else str(int(x)) for x in v) + '"))'
        return '(Pl.Col.f64 (bF "' + ",".join("n" if x is None else str(lt.bits(x)) for x in v) + '"))'
    if k == "int":
        return '(Pl.Col.int (oI "' + ",".join("n" if x is None else str(x) for x in v) + '"))'
    return lt.lean_col(s)


def frame_let(name: str, df: pl.DataFrame) -> str:
    return f"let {name} : Pl.Frame Float := [" + ", ".join(f"({lt.lean_str(n)}, {col(df.get_column(n))})" for n in df.columns) + "]; "


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def capture(mod, fn) -> dict:
    rec: dict = {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is mod.run.__code__:
            rec.update(frame.f_locals)
    sys.setprofile(prof)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fn()
    finally:
        sys.setprofile(None)
    return rec


def near_rows(pd: pl.Series, per_side: int, extremes: int, spread: int) -> list[int]:
    """Row indices: the per_side rows nearest below and above every cut, the extremes, a spread."""
    v = pd.to_list()
    order = sorted((i for i in range(len(v)) if v[i] is not None), key=lambda i: v[i])
    rows = {i for i in range(len(v)) if v[i] is None}
    for c in CUTS:
        below = [i for i in order if v[i] < c][-per_side:]
        above = [i for i in order if v[i] >= c][:per_side]
        rows |= set(below) | set(above)
    rows |= set(order[:extremes]) | set(order[-extremes:])
    if spread:
        rows |= {order[(k * (len(order) - 1)) // max(spread - 1, 1)] for k in range(spread)}
    return sorted(rows)


def run_slice(path: Path, a: int, b: int, first: str, last: str, env: dict) -> dict:
    lines = path.read_text().splitlines()[a - 1:b]
    assert lines[0].strip().startswith(first) and lines[-1].strip().startswith(last), (lines[0], lines[-1])
    ns = dict(env)
    exec(compile(textwrap.dedent("\n".join(lines)), f"{path.name}:{a}-{b}", "exec"), ns)  # the port's own lines
    return ns


class Group:
    """One eval input: lets + digests."""

    def __init__(self, s: Suite):
        self.s, self.lets, self.body, self.cases, self.k = s, ENC, [], [], 0

    def frame(self, df: pl.DataFrame) -> str:
        self.k += 1
        self.lets += frame_let(f"f{self.k}", df)
        return f"f{self.k}"

    def case(self, cid: str, unit: str, term: str, df: pl.DataFrame):
        self.body.append(f"dg (tR ({term}))")
        self.cases.append((cid, unit, dgf(df)))

    def flush(self):
        self.s.ints(self.lets, "[" + ", ".join(self.body) + "]", self.cases)


# ---------------------------------------------------------------- predict
def predict_cases(g: Group, tag: str, L: dict, idx: list[int], cols: list[str] | None):
    """Rows idx of the port's test_scored (columns cols, None = all) through steps 07 and 08."""
    age_name = L["age_name"]
    scored = L["test_scored"][idx]
    preds = L["test_predictions"][idx]
    kag = L["kaggle_submission"][idx]
    full = L["test_predictions_full"][idx]
    if cols is not None:
        scored = scored.select(cols)
        preds = preds.select(cols + ["pred_logistic"] + NEW)
        kag = kag.select([c for c in kag.columns if c in cols])
        keep = set(preds.columns) & set(KEEP_FULL)
        full = full.select([c for c in full.columns if (("age" if c == age_name else c) in keep)])
    f = g.frame(scored)
    g.case(f"{tag}: input test_scored", U07, f, scored)
    g.case(f"{tag}: test_predictions", U07, f"predict_run_07_predictions {f}", preds)
    g.case(f"{tag}: kaggle_submission", U08, f"(predict_run_08_outputs (predict_run_07_predictions {f}) {lt.lean_str(age_name)}).1", kag)
    g.case(f"{tag}: test_predictions_full age_name={age_name}", U08,
           f"(predict_run_08_outputs (predict_run_07_predictions {f}) {lt.lean_str(age_name)}).2", full)
    print(f"[{tag}] rows={len(idx)} cols={scored.width} age_name={age_name!r} full cols={full.columns} "
          f"grades={dict(sorted(preds.group_by('risk_grade').len().iter_rows()))} null pd={scored['pd_logistic'].null_count()}")


def pipeline(data: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        fe.run(data, out, split_ids=PTL / "inputs" / "split_ids.csv")
        tr.run(out, out)
    return capture(pr, lambda: pr.run(out, out, data_dir=data, income_medians=out / "income_medians.csv"))


HAND_PD = [None, nan, 0.0, -0.0, 5e-324, 0.1, math.nextafter(0.1, 0), math.nextafter(0.1, 1), 0.12, 0.15,
           math.nextafter(0.15, 0), math.nextafter(0.15, 1), 0.2, 0.25, math.nextafter(0.25, 0), math.nextafter(0.25, 1),
           0.3, 0.35, math.nextafter(0.35, 0), math.nextafter(0.35, 1), 0.4, 0.5, math.nextafter(0.5, 0),
           math.nextafter(0.5, 1), 0.75, 1.0, math.nextafter(1.0, 0), 1.5, -0.2, inf, -inf, 1e308, -1e308]


def hand_predict(g: Group, tag: str, scored: pl.DataFrame, age_name: str):
    ns = run_slice(ROOT / "port/credit_risk/predict.py", 398, 469, "test_predictions = test_scored.with_columns(",
                   ").rename(", {"pl": pl, "sas_compat": pr.sas_compat, "test_scored": scored, "age_name": age_name})
    f = g.frame(scored)
    g.case(f"{tag}: input test_scored", U07, f, scored)
    g.case(f"{tag}: test_predictions", U07, f"predict_run_07_predictions {f}", ns["test_predictions"])
    g.case(f"{tag}: kaggle_submission", U08, f"(predict_run_08_outputs (predict_run_07_predictions {f}) {lt.lean_str(age_name)}).1", ns["kaggle_submission"])
    g.case(f"{tag}: test_predictions_full age_name={age_name}", U08,
           f"(predict_run_08_outputs (predict_run_07_predictions {f}) {lt.lean_str(age_name)}).2", ns["test_predictions_full"])
    P = ns["test_predictions"]
    print(f"[{tag}] grades={P['risk_grade'].to_list()} pred={P['pred_logistic'].to_list()} full={ns['test_predictions_full'].columns}")


def suite_predict() -> Suite:
    s = Suite("t9_predict")
    s.item, s.decl = "def:zz_carrier_p", "zz_carrier_p"
    L = {n: pl.read_parquet(W / f"predict_{n}.parquet") for n in ("test_scored", "test_predictions", "kaggle_submission", "test_predictions_full")}
    L["age_name"] = "age"
    narrow = ["row_id", "age", "pd_logistic"]
    g = Group(s)
    predict_cases(g, "legacy/data narrow", L, near_rows(L["test_scored"]["pd_logistic"], 10, 4, 20), narrow)
    g.flush()
    g = Group(s)
    predict_cases(g, "legacy/data wide", L, [0, 101502], None)
    g.flush()
    g = Group(s)
    for sc in ("test_header_age_upper", "test_header_all_upper"):
        Ls = pipeline(SC / "fix_round5" / sc, W / f"out_{sc}")
        predict_cases(g, f"fix_round5/{sc} narrow", Ls, near_rows(Ls["test_scored"]["pd_logistic"], 3, 2, 12), narrow)
        if sc == "test_header_age_upper":
            predict_cases(g, f"fix_round5/{sc} wide", Ls, [199], None)
    g.flush()
    g = Group(s)
    n = len(HAND_PD)
    base = pl.DataFrame({"row_id": [float(i + 1) for i in range(n)], "age": [float(20 + i) for i in range(n)],
                         "k": pl.Series(list(range(n)), dtype=pl.Int64), "t": ["x"] * n,
                         "pd_logistic": pl.Series(HAND_PD, dtype=pl.Float64), "monthly_income": [1000.5] * n})
    hand_predict(g, "hand cuts", base, "AGE")
    hand_predict(g, "hand cuts, age_name unchanged", base.head(6), "age")
    for v in (1.0, 0.0, None, 0.5):
        hand_predict(g, f"hand one row pd={v}", pl.DataFrame({"age": [41.0], "pd_logistic": pl.Series([v], dtype=pl.Float64), "row_id": [7.0]}), "Age")
    hand_predict(g, "hand no row", base.clear(), "AGE")
    hand_predict(g, "hand all null", pl.DataFrame({"row_id": [1.0, 2.0], "age": [30.0, 31.0], "pd_logistic": pl.Series([None, None], dtype=pl.Float64)}), "aGe")
    g.flush()
    note = ("real predict.run (legacy/data; fix_round5/test_header_age_upper, test_header_all_upper), locals at return; the Lean "
            "runs on chosen rows of the port's test_scored and is compared with the same rows of the port's results; hand = "
            "the lines 398-469 executed verbatim")
    s.notes = {U07: note, U08: note}
    return s


# ---------------------------------------------------------------- train
def train_cases(g: Group, tag: str, L: dict, it: list[int], iv: list[int], cols: list[str] | None):
    a, b = L["logit_scored_train"][it], L["logit_scored_valid"][iv]
    ra, rb = L["risk_scores_train"][it], L["risk_scores_validation"][iv]
    if cols is not None:
        a, b = a.select(cols), b.select(cols)
        ra, rb = ra.select(cols + NEW), rb.select(cols + NEW)
    fa, fb = g.frame(a), g.frame(b)
    g.case(f"{tag}: input logit_scored_train", U12, fa, a)
    g.case(f"{tag}: input logit_scored_valid", U12, fb, b)
    g.case(f"{tag}: risk_scores_train", U12, f"(train_run_12_risk_scores {fa} {fb}).1", ra)
    g.case(f"{tag}: risk_scores_validation", U12, f"(train_run_12_risk_scores {fa} {fb}).2", rb)
    print(f"[{tag}] rows={len(it)}/{len(iv)} cols={a.width} null pd={a['pd_logistic'].null_count()}/{b['pd_logistic'].null_count()} "
          f"grades={dict(sorted(ra.group_by('risk_grade').len().iter_rows()))} / {dict(sorted(rb.group_by('risk_grade').len().iter_rows()))}")


def blanked_train_run() -> dict:
    """train.run on the real feature files with `age` (a model variable) blanked in three rows of
    each file: those rows get a null pd_logistic in the port's scored frames."""
    src, out = W / "out", W / "out_nullpd"
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("model_features_train.csv", (2, 500, 104999)), ("model_features_validation.csv", (1, 7, 44000))):
        lines = (src / name).read_text().splitlines()
        j = lines[0].split(",").index("age")
        for r in rows:
            f = lines[r].split(",")
            f[j] = ""
            lines[r] = ",".join(f)
        (out / name).write_text("\n".join(lines) + "\n")
    return capture(tr, lambda: tr.run(out, out))


def hand_train(g: Group, tag: str, a: pl.DataFrame, b: pl.DataFrame):
    ns = run_slice(ROOT / "port/credit_risk/train.py", 584, 673, "risk_scores_train = logit_scored_train.with_columns(",
                   ")  # format interest_rate", {"pl": pl, "sas_compat": tr.sas_compat, "logit_scored_train": a, "logit_scored_valid": b})
    fa, fb = g.frame(a), g.frame(b)
    g.case(f"{tag}: input logit_scored_train", U12, fa, a)
    g.case(f"{tag}: input logit_scored_valid", U12, fb, b)
    g.case(f"{tag}: risk_scores_train", U12, f"(train_run_12_risk_scores {fa} {fb}).1", ns["risk_scores_train"])
    g.case(f"{tag}: risk_scores_validation", U12, f"(train_run_12_risk_scores {fa} {fb}).2", ns["risk_scores_validation"])
    print(f"[{tag}] grades={ns['risk_scores_train']['risk_grade'].to_list()} / {ns['risk_scores_validation']['risk_grade'].to_list()}")


def suite_train() -> Suite:
    s = Suite("t9_train")
    s.item, s.decl = "def:zz_carrier_t", "zz_carrier_t"
    L = {n: pl.read_parquet(W / f"train_{n}.parquet") for n in ("logit_scored_train", "logit_scored_valid", "risk_scores_train", "risk_scores_validation")}
    narrow = ["row_id", "default_flag", "pd_logistic", "pred_logistic"]
    g = Group(s)
    train_cases(g, "real features narrow", L, near_rows(L["logit_scored_train"]["pd_logistic"], 8, 3, 16),
                near_rows(L["logit_scored_valid"]["pd_logistic"], 5, 2, 10), narrow)
    g.flush()
    g = Group(s)
    train_cases(g, "real features wide", L, [0, 104999], [44999], None)
    g.flush()
    Ln = blanked_train_run()
    nt = [i for i, v in enumerate(Ln["logit_scored_train"]["pd_logistic"].to_list()) if v is None]
    nv = [i for i, v in enumerate(Ln["logit_scored_valid"]["pd_logistic"].to_list()) if v is None]
    print("null pd rows of the blanked run:", nt, nv)
    assert nt and nv
    g = Group(s)
    train_cases(g, "real features, age blanked in 3 rows (null pd) narrow", Ln,
                sorted(set(nt) | set(near_rows(Ln["logit_scored_train"]["pd_logistic"], 2, 1, 6))),
                sorted(set(nv) | set(near_rows(Ln["logit_scored_valid"]["pd_logistic"], 2, 1, 6))), narrow)
    train_cases(g, "real features, age blanked (null pd) wide", Ln, nt[:1], nv[1:2], None)
    g.flush()
    g = Group(s)
    n = len(HAND_PD)
    a = pl.DataFrame({"row_id": [float(i + 1) for i in range(n)], "default_flag": [float(i % 2) for i in range(n)],
                      "pd_logistic": pl.Series(HAND_PD, dtype=pl.Float64), "pred_logistic": pl.Series([i % 2 for i in range(n)], dtype=pl.Int64)})
    b = a.reverse()
    hand_train(g, "hand cuts", a, b)
    one = lambda v: pl.DataFrame({"pd_logistic": pl.Series([v], dtype=pl.Float64), "default_flag": [1.0]})  # noqa: E731
    hand_train(g, "hand one row 1.0 / null", one(1.0), one(None))
    hand_train(g, "hand one row 0.0 / 0.5", one(0.0), one(0.5))
    hand_train(g, "hand no row / all null", a.clear(), pl.DataFrame({"pd_logistic": pl.Series([None, None, None], dtype=pl.Float64)}))
    g.flush()
    s.notes = {U12: "real train.run on the feature files of a real feature-engineering run (legacy/data), locals at return; a second "
                    "real run with `age` blanked in three rows of each feature file (null pd_logistic); the Lean runs on chosen rows "
                    "of the port's scored frames and is compared with the same rows of the port's results; hand = the lines 584-673 "
                    "executed verbatim"}
    return s


if __name__ == "__main__":
    which = set(sys.argv[1:]) or {"predict", "train"}
    if "predict" in which:
        suite_predict().write()
    if "train" in which:
        suite_train().write()
