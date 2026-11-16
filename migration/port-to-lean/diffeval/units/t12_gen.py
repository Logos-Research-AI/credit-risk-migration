"""T12 of the update after verification (2026-11-16): metrics_run_01_roc_auc
(metrics_calculation.py:109-152) against the port as it stands.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t12_gen.py
      -> diffeval/work/t12_auc.json, .inputs.json, t12_auc.in<k>.txt (one eval_decl input each)
  eval_decl each input on def:zz_carrier_m / zz_carrier_m; outputs in work/t12_auc.out<k>.txt
  sh diffeval/work/assemble.sh t12_auc <n>; python diffeval/compare.py work/t12_auc.json work/t12_auc.out.txt

real   the REAL metrics_calculation.run on a directory holding risk_scores_validation.csv and
       risk_scores_train.csv; `roc_stats` and `auc_summary` are the locals of the run when it
       returns (profiler on the run's frame). Scenarios of the plan: the fix_* ones whole;
       real_metrics in 300-row slices of the validation file (the eval_decl input is text and
       the Lean of the ROC helpers is quadratic), edge_metrics_b rows 1-600.
       The Lean gets the frame restricted to (default_flag, pd_logistic), the columns the step reads.
slice  lines 114-152 of the source, executed on a frame. Asserted equal to the locals of the real
       run on every `real` input; then used on hand-made frames the CSV import cannot produce
       (NaN) or on which a later step of the run stops.
math.fsum: lookup table of the port's own calls (see t1_gen.py).
"""
from __future__ import annotations

import inspect
import shutil
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import t1_gen as t1  # noqa: E402  (wraps math.fsum; helpers)
import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

SCEN = t1.SCEN
WORK = HERE.parent / "work"
TMP = WORK / "tmp_t12"
ITEM, DECL = "def:zz_carrier_m", "zz_carrier_m"
U = "metrics_run_01_roc_auc"
nan = float("nan")

SRC = inspect.getsource(mc).splitlines()
assert SRC[113].strip().startswith("roc_stats = sas_compat.roc_association(") and SRC[150].strip() == ".head(min(auc_pairs.height, 1))" and SRC[151].strip() == ")", (SRC[113], SRC[150])
SLICE = compile(textwrap.dedent("\n".join(SRC[113:152])), "metrics_calculation.py:114-152", "exec")


def run_slice(valid: pl.DataFrame) -> dict:
    env = {"pl": pl, "sas_compat": sc, "logit_scored_valid": valid}
    exec(SLICE, env)
    return env


def real_run(vtext: str, ttext: str) -> dict:
    """the locals of the real mc.run when it returns or raises"""
    shutil.rmtree(TMP, ignore_errors=True)
    (TMP / "in").mkdir(parents=True)
    (TMP / "in" / "risk_scores_validation.csv").write_text(vtext)
    (TMP / "in" / "risk_scores_train.csv").write_text(ttext)
    got: dict = {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is mc.run.__code__:
            got.update(frame.f_locals)

    sys.setprofile(prof)
    try:
        mc.run(TMP / "in", TMP / "out")
        got["_raised"] = None
    except Exception as ex:  # noqa: BLE001
        got["_raised"] = f"{type(ex).__name__}: {ex}"
    finally:
        sys.setprofile(None)
    return got


def same(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return cmp.canon_frame(a) == cmp.canon_frame(b)


LETS = (b4.FCOL
        + "let YS := fun (s : String) => (Pl.Col.f64 (s.toList.map (fun (c : Char) => if c == '1' then some (1.0 : Float) else if c == '0' then some (0.0 : Float) else none)) : Pl.Col Float); "
        + "let SK := fun (d : Float) (ks : List Nat) => (Pl.Col.f64 (ks.map (fun (k : Nat) => some (k.toFloat / d))) : Pl.Col Float); "
        + "let M := fun (y s : Pl.Col Float) => let f : Pl.Frame Float := [(\"default_flag\", y), (\"pd_logistic\", s)]; "
          "let r := metrics_run_01_roc_auc (α := Float) FS f; [dg (tR r.1), dg (tR r.2)]; ")


class Group:
    def __init__(self, st: Suite):
        self.st, self.terms, self.cases = st, [], []

    def add(self, name: str, term: str, roc: pl.DataFrame, auc: pl.DataFrame):
        self.terms.append(term)
        self.cases += [(f"{name}: roc_stats", U, cmp.canon_frame(roc)), (f"{name}: auc_summary ({auc.height} row)", U, cmp.canon_frame(auc))]

    def flush(self):
        if not self.terms:
            return
        lets = t1.fs_let(set(t1.FSUM)) + LETS
        body = "([" + ", ".join(self.terms) + "] : List (Pl.Col Float × Pl.Col Float)).flatMap (fun (d : Pl.Col Float × Pl.Col Float) => M d.1 d.2)"
        self.st.digest_body(lets, body, self.cases, gen=False)
        self.terms, self.cases = [], []
        t1.FSUM.clear()


def suite() -> Suite:
    st = Suite("t12_auc")
    st.item, st.decl = ITEM, DECL
    t1.FSUM.clear()

    def real(g: Group, name: str, vtext: str, ttext: str, dec: int):
        loc = real_run(vtext, ttext)
        assert "auc_summary" in loc and "roc_stats" in loc, (name, loc.get("_raised"))
        valid = sc.proc_import_csv(TMP / "in" / "risk_scores_validation.csv", guessingrows=20)
        env = run_slice(valid)
        assert same(env["roc_stats"], loc["roc_stats"]) and same(env["auc_summary"], loc["auc_summary"]), name
        y, s = valid.get_column("default_flag"), valid.get_column("pd_logistic")
        note = "" if loc["_raised"] is None else f" [the run stops later: {loc['_raised'][:60]}]"
        print(f"{name}: run {'completed' if loc['_raised'] is None else 'raised ' + loc['_raised'][:70]}; auc_summary {loc['auc_summary'].rows()}")
        g.add(f"real mc.run, {name}{note}", t1.enc(y, s, dec), loc["roc_stats"], loc["auc_summary"])

    def lines(p: Path, idx=None) -> str:
        ls = p.read_text().splitlines(keepends=True)
        return "".join(ls if idx is None else [ls[0]] + [ls[i + 1] for i in idx])

    # ---- the fix scenarios, whole files
    g = Group(st)
    for name in ("fix_Q26_small", "fix_Q26_ties", "fix_Q26_nodefaulter", "fix_Q23_nodefaulter", "fix_Q23_alldefaulters", "fix_Q23_tie"):
        d = SCEN / name
        real(g, f"{name} (whole)", lines(d / "risk_scores_validation.csv"), lines(d / "risk_scores_train.csv"), 4)
    g.flush()
    # ---- real_metrics slices, edge_metrics_b
    d = SCEN / "real_metrics"
    ttext = lines(d / "risk_scores_train.csv", range(700))
    for nm, idx in (("validation rows 1-300", range(300)), ("every 150th validation row (300 rows)", range(0, 45000, 150))):
        g = Group(st)
        real(g, f"real_metrics, {nm}; training rows 1-700", lines(d / "risk_scores_validation.csv", idx), ttext, 10)
        g.flush()
    d = SCEN / "edge_metrics_b"
    g = Group(st)
    real(g, "edge_metrics_b, validation rows 1-600; training whole", lines(d / "risk_scores_validation.csv", range(600)), lines(d / "risk_scores_train.csv"), 4)
    g.flush()
    # ---- hand-made frames through the slice (y kind f64; nulls, NaN, other flag values, signed zeros)
    H = {
        "null pd rows dropped": ([1., 0., 1., 0., 1.], [.3, None, .2, .2, None]),
        "all pd null (auc_pairs has no row)": ([1., 0., 1.], [None, None, None]),
        "null flags": ([None, 0., 1., None, 1., 0.], [.3, .3, .2, .2, .5, .1]),
        "all flags null": ([None, None], [.3, .2]),
        "flag values other than 0 / 1": ([2., 1., 0., -1., 1., 0., nan], [.3, .3, .2, .2, .5, .1, .4]),
        "NaN probabilities (one group, sorted last)": ([1., 0., 1., 0., 1., 0.], [nan, .3, nan, .2, .5, nan]),
        "zeros of both signs (one group)": ([1., 0., 1., 0.], [0.0, -0.0, -0.0, .1]),
        "negative zero first": ([0., 1., 1., 0.], [-0.0, 0.0, .1, -0.0]),
        "one row": ([1.], [.4]),
        "one row, pd null": ([0.], [None]),
        "one defaulter, one other": ([1., 0.], [.4, .7]),
        "all tied": ([1., 0., 1., 0., 0.], [.25] * 5),
        "near ties (exact AUC separates, ROC area ties)": ([1., 0., 1., 0.], [.5, .5 - 1e-9, .5 - 2e-9, .5 - 1e-12]),
        "unsorted with repeats": ([0., 1., 1., 0., 1., 0., 0., 1., 0.], [.7, .1, .7, .4, .4, .1, .9, .9, .4]),
        "infinite probabilities": ([1., 0., 1., 0.], [float("inf"), float("-inf"), .5, float("inf")]),
    }
    g = Group(st)
    for name, (yv, sv) in H.items():
        f = pl.DataFrame({"default_flag": pl.Series(yv, dtype=pl.Float64, nan_to_null=False), "pd_logistic": pl.Series(sv, dtype=pl.Float64, nan_to_null=False)})
        env = run_slice(f)
        print(f"hand {name}: auc_summary {env['auc_summary'].rows()}")
        g.add(f"slice :114-152, hand frame: {name}", f"({b4.col(yv)}, {b4.col(sv)})", env["roc_stats"], env["auc_summary"])
    g.flush()
    shutil.rmtree(TMP, ignore_errors=True)
    return st


if __name__ == "__main__":
    st = suite()
    st.write()
    for i, inp in enumerate(st.inputs):
        (WORK / f"t12_auc.in{i}.txt").write_text(inp["text"])
        print(i, len(inp["text"]), "chars;", sum(1 for c in st.cases if c["input"] == i), "cases")
