"""Update after verification, task T15: differential test of
  def:metrics_run_06_psi   credit_risk/metrics_calculation.py:325-401

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t15_gen.py
      -> diffeval/work/t15_psi.json, t15_psi.inputs.json
  (eval_decl each input on def:zz_carrier_m / zz_carrier_m, save diffeval/work/t15_psi.out.txt)
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/t15_psi.json diffeval/work/t15_psi.out.txt

Python side (the code of the package, never a re-implementation):
  real   the REAL metrics_calculation.run on a temp directory holding the two score files of a
         scenario of judge/scenarios (whole files, or their first rows when the file is too long to
         type into an eval_decl call); the locals of `run` are copied when it returns:
         logit_scored_train, logit_scored_valid (inputs of the slice), psi_calculation, psi_summary;
  slice  the source lines 325-401, read from the file at run time (verbatim, dedented) and executed
         with the module's globals. It is run (1) on the two frames of the real run restricted to
         the column the slice reads (credit_risk_score): asserted equal to the real run's results;
         (2) on hand-made frames (nulls, NaN, ties on a cut, 0 to 12 rows).
Lean side: metrics_run_06_psi on the two frames with the column credit_risk_score; the digest of
each input frame is compared with the digest of the Python frame first (same input bit for bit).
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KIT_ROOT = HERE.parents[1]            # migration/port-to-lean
SCEN = KIT_ROOT.parents[1] / "judge" / "scenarios"
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_m", "zz_carrier_m")

import compare as cmp  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402

U = "metrics_run_06_psi"
A, B, MUST = 325, 401, "psi_cuts = ["
nan = float("nan")


def slice_source() -> str:
    lines = Path(mc.__file__).read_text().splitlines(keepends=True)
    src = "".join(lines[A - 1:B])
    assert MUST in src and "psi_summary = psi_summary.with_columns(" in src, "line numbers moved?"
    assert lines[A - 1].lstrip().startswith("# metrics_calculation.sas:332-346 psi_cuts"), lines[A - 1]
    assert lines[B - 1].strip() == ")" and lines[B].strip() == "", (lines[B - 1], lines[B])
    return textwrap.dedent(src)


def run_slice(t: pl.DataFrame, v: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    ns = dict(vars(mc))
    ns.update({"logit_scored_train": t, "logit_scored_valid": v})
    exec(compile(slice_source(), f"{mc.__file__}:{A}-{B}", "exec"), ns)  # noqa: S102
    return ns["psi_calculation"], ns["psi_summary"]


def real_run(ttext: str, vtext: str) -> dict:
    rec: dict = {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is mc.run.__code__:
            rec.update(frame.f_locals)

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        (ind / "risk_scores_train.csv").write_text(ttext)
        (ind / "risk_scores_validation.csv").write_text(vtext)
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mc.run(ind, outd)
        finally:
            sys.setprofile(None)
        rec["_printed"] = (outd / "printed_psi_calculation.csv").read_text()
    return rec


def head(path: Path, n: int | None) -> str:
    lines = path.read_text().splitlines(keepends=True)
    return "".join(lines if n is None else lines[:n + 1])


def same(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return cmp.canon_frame(a) == cmp.canon_frame(b)


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


# ---------------------------------------------------------------- columns as short Lean terms
PARTS = {
    # FD d v: k / 10^d; -1 = null, -2 = NaN
    "FD": "let FD := fun (d : Nat) (v : List Int) => (Pl.Col.f64 (v.map (fun (k : Int) => if k == -1 then none else "
          "if k == -2 then some (0.0 / 0.0) else some (Float.ofScientific k.toNat true d))) : Pl.Col Float); ",
    # FQ s: three digits ddd per value, value = (2400 + ddd) / 4
    "FQ": "let FQ := fun (s : String) => (let a := s.toList.toArray; let d := fun (i : Nat) => (a[i]!).toNat - 48; "
          "Pl.Col.f64 ((List.range (a.size / 3)).map (fun (i : Nat) => "
          "some (Float.ofNat (2400 + d (3 * i) * 100 + d (3 * i + 1) * 10 + d (3 * i + 2)) / 4.0))) : Pl.Col Float); ",
    # GT n: 625 + 0.002 i, i < n ; GV n: 825.0 then 625 + 0.002 (n - i), 1 <= i < n  (fix2/q25_tiny_psi; the
    # validation frame reaches the slice sorted by pd_logistic)
    # FR runs: (k, count) runs, value = (2400 + k) / 4
    "FR": "let FR := fun (r : List (Nat × Nat)) => (Pl.Col.f64 (r.flatMap (fun (p : Nat × Nat) => "
          "List.replicate p.2 (some (Float.ofNat (2400 + p.1) / 4.0)))) : Pl.Col Float); ",
    "GT": "let GT := fun (n : Nat) => (Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofScientific (625000 + 2 * i) true 3))) : Pl.Col Float); ",
    "GV": "let GV := fun (n : Nat) => (Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (if i == 0 then 825.0 else "
          "Float.ofScientific (625000 + 2 * (n - i)) true 3))) : Pl.Col Float); ",
}
TAIL = ("let S := fun (c : Pl.Col Float) => ([(\"credit_risk_score\", c)] : Pl.Frame Float); "
        "let psi := fun (t v : Pl.Frame Float) => (let r := metrics_run_06_psi t v; [dg (tR t), dg (tR v), dg (tR r.1), dg (tR r.2)]); ")


def lets_for(call: str) -> str:
    return "".join(text for name, text in PARTS.items() if f"({name} " in call) + TAIL


def enc_fd(s: pl.Series, d: int) -> str:
    out = []
    for x in s.to_list():
        if x is None:
            out.append("-1")
        elif x != x:
            out.append("-2")
        else:
            k = round(x * 10**d)
            assert k >= 0 and float(f"{k}e-{d}") == x and (x != 0 or str(x) == "0.0"), x
            out.append(str(k))
    return f"(FD {d} [{', '.join(out)}])"


def enc_fq(s: pl.Series) -> str:
    out = []
    for x in s.to_list():
        k = x * 4 - 2400
        assert k == int(k) and 0 <= k < 1000, x
        out.append(f"{int(k):03d}")
    return f'(FQ "{"".join(out)}")'


def enc_fr(s: pl.Series) -> str:
    runs: list[list[int]] = []
    for x in s.to_list():
        k = x * 4 - 2400
        assert k == int(k) and 0 <= k < 1000, x
        if runs and runs[-1][0] == int(k):
            runs[-1][1] += 1
        else:
            runs.append([int(k), 1])
    return "(FR [" + ", ".join(f"({k}, {c})" for k, c in runs) + "])"


def cases(name: str, t: pl.DataFrame, v: pl.DataFrame, pc: pl.DataFrame, ps: pl.DataFrame) -> list[tuple]:
    print(f"[{name}] train {t.height} valid {v.height}; train_pct {pc['train_pct'].to_list()} valid_pct {pc['valid_pct'].to_list()} "
          f"components null {pc['psi_component'].null_count()} PSI {ps.item(0, 'PSI')!r} {ps.item(0, 'PSI_interpretation')}")
    return [(f"{name}: input logit_scored_train", U, dgf(t)), (f"{name}: input logit_scored_valid", U, dgf(v)),
            (f"{name}: psi_calculation", U, dgf(pc)), (f"{name}: psi_summary", U, dgf(ps))]


# (scenario directory, rows kept of train / validation or None for the whole file, encoder)
REAL = [
    ("fix_Q25", None, None, "fd0"),
    ("fix_G43", None, None, "fd0"),
    ("real_metrics", 150, 60, "fd8"),
    ("fix2/q25_tiny_psi", 10000, 10000, "gen"),
    ("edge_metrics_a", 300, 120, "fq"),
    ("edge_metrics_b", 300, 120, "frq"),
    ("edge_metrics_c", 300, 120, "fq"),
]


def f(vals) -> pl.DataFrame:
    return pl.DataFrame({"credit_risk_score": pl.Series("credit_risk_score", vals, dtype=pl.Float64)})


# hand-made: (name, training scores, validation scores)
HAND = [
    ("1 / 1 equal", [700.0], [700.0]),
    ("1 / 1 validation above", [700.0], [701.0]),
    ("1 / 1 validation below", [700.0], [699.0]),
    ("2 / 3", [650.0, 800.0], [640.0, 650.0, 800.5]),
    ("3 / 2 ties on every cut", [700.0, 700.0, 700.0], [700.0, 700.5]),
    ("9 / 4", [float(600 + 10 * i) for i in range(9)], [600.0, 605.0, 680.0, 900.0]),
    ("10 / 10 same scores, other order", [float(600 + 10 * i) for i in range(10)], [float(600 + 10 * ((7 * i) % 10)) for i in range(10)]),
    ("11 / 5 unsorted training", [float(600 + 10 * ((4 * i) % 11)) for i in range(11)], [610.0, 610.0, 655.0, 700.0, 700.5]),
    ("12 / 1", [float(600 + 5 * i) for i in range(12)], [627.5]),
    ("training nulls: first cuts are null", [None, None, None, 650.0, 700.0, 710.0, 720.0, 730.0, 740.0, 750.0], [None, 640.0, 650.0, 735.0, 800.0]),
    ("training all null", [None, None, None], [None, 700.0]),
    ("validation all null", [600.0, 650.0, 700.0, 750.0, 800.0], [None, None]),
    ("NaN in both sets", [600.0, nan, 650.0, 700.0, nan, 750.0, 800.0, 810.0, 820.0, 830.0], [nan, 600.0, 825.0, None]),
    ("training all NaN", [nan, nan], [nan, 5.0, None]),
    ("one distinct training value, many rows", [725.0] * 23, [724.0, 725.0, 726.0]),
    ("two distinct training values 7 + 13", [600.0] * 7 + [800.0] * 13, [600.0, 700.0, 800.0, 801.0]),
    ("zero scores", [0.0, 0.0, 1.0, 2.0], [0.0, 0.5, 3.0]),
    ("0 / 3 (training without rows: outside the precondition, the code is defined)", [], [600.0, 700.0, 800.0]),
    ("3 / 0 (validation without rows: outside the precondition, the code is defined)", [600.0, 700.0, 800.0], []),
    ("0 / 0 (outside the precondition, the code is defined)", [], []),
]


def build() -> Suite:
    s = Suite("t15_psi")
    for d, nt, nv, how in REAL:
        ttext, vtext = head(SCEN / d / "risk_scores_train.csv", nt), head(SCEN / d / "risk_scores_validation.csv", nv)
        rec = real_run(ttext, vtext)
        tf, vf = rec["logit_scored_train"], rec["logit_scored_valid"]
        pc, ps = rec["psi_calculation"], rec["psi_summary"]
        t, v = tf.select("credit_risk_score"), vf.select("credit_risk_score")
        assert t.schema["credit_risk_score"] == pl.Float64 and v.schema["credit_risk_score"] == pl.Float64
        pc1, ps1 = run_slice(t, v)   # the slice on the column it reads = the real run on the whole frames
        assert same(pc1, pc) and same(ps1, ps), d
        pc2, ps2 = run_slice(tf, vf)
        assert same(pc2, pc) and same(ps2, ps), d
        name = f"real mc.run, {d}" + ("" if nt is None else f" [first {nt} / {nv} rows]")
        tc, vc = t["credit_risk_score"], v["credit_risk_score"]
        if how == "fd0":
            call = f"psi (S {enc_fd(tc, 0)}) (S {enc_fd(vc, 0)})"
        elif how == "fd8":
            call = f"psi (S {enc_fd(tc, 8)}) (S {enc_fd(vc, 8)})"
        elif how == "frq":
            call = f"psi (S {enc_fr(tc)}) (S {enc_fq(vc)})"
        elif how == "fq":
            call = f"psi (S {enc_fq(tc)}) (S {enc_fq(vc)})"
        else:
            assert tc.to_list() == [float(f"{625000 + 2 * i}e-3") for i in range(nt)]
            assert vc.to_list() == [825.0] + [float(f"{625000 + 2 * (nv - i)}e-3") for i in range(1, nv)]
            call = f"psi (S (GT {nt})) (S (GV {nv}))"
        lets = lets_for(call)
        s.ints(lets, call, cases(name, t, v, pc, ps), table=False)
        print("    printed_psi_calculation.csv:", rec["_printed"].replace("\n", " | ")[:400])
    calls, cs = [], []
    for name, tv, vv in HAND:
        t, v = f(tv), f(vv)
        pc, ps = run_slice(t, v)
        calls.append(f"psi (S {enc_fd(t['credit_risk_score'], 1)}) (S {enc_fd(v['credit_risk_score'], 1)})")
        cs += cases(f"hand: {name}", t, v, pc, ps)
    lets = lets_for(calls[0])
    half = len(calls) // 2
    s.ints(lets, " ++ ".join(calls[:half]), cs[:4 * half], table=False)
    s.ints(lets, " ++ ".join(calls[half:]), cs[4 * half:], table=False)
    s.notes = {U: "evaluated directly on logit_scored_train / logit_scored_valid (column credit_risk_score; the other columns are "
                  "not read: asserted on the real run); real = the locals of the real metrics_calculation.run at its return "
                  "(whole files for fix_Q25 and fix_G43, the first rows of the longer files); hand = the source lines 325-401 "
                  "executed verbatim; score_bin compared as Int64"}
    return s


if __name__ == "__main__":
    build().write()
