"""Update after the verification round, task T14: differential tests of
  def:metrics_run_04_deciles          credit_risk/metrics_calculation.py:214-283
  def:metrics_run_05_cumulative_lift  credit_risk/metrics_calculation.py:287-321

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t14_gen.py
      -> diffeval/work/t14_dec.json, t14_lift.json (+ .inputs.json)
  (eval_decl each input on def:zz_carrier_m / zz_carrier_m; save diffeval/work/t14_<suite>.out.txt)
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/t14_<suite>.json diffeval/work/t14_<suite>.out.txt

Python side: always the code of the package, never a re-implementation.
  real   the REAL metrics_calculation.run(input_dir, output_dir) on a scenario directory, under a
         line tracer that copies the locals of `run` when it reaches line 214, when it first passes
         line 283 and when it first passes line 321: the inputs and results of the two steps in the
         real run. "prefix N": the scenario's validation file cut to its first N data rows (the Lean
         input has to be typed into an eval_decl call), the training file whole; still the real run.
  slice  the source lines of the step, read from the file at run time and executed verbatim with the
         module's globals: (1) on the real run's inputs restricted to the columns the step reads
         (asserted equal to the real run's results, column for column); (2) on hand-made frames
         that the code before the step cannot produce.

Lean side: frames are built from short codes (HX: 0/1 flags from hex digits, RL / PL: decimal
values k * 10^-e, run-length coded or plain); the digest of every input frame is compared with the
digest of the Python frame first, so the inputs are equal bit for bit. The Int64 column `decile`,
which the Lean keeps as Float64 (R-F2I), is cast to Float64 on the Python side.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1]  # migration/port-to-lean
ROOT = KIT.parents[1]
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_m", "zz_carrier_m")

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

nan = float("nan")
SCEN = ROOT / "judge" / "scenarios"
OUT = HERE.parent / "work" / "t14_run"
S04, S05 = (214, 283, "decile_list.join(decile_grouped"), (287, 321, ".otherwise(0.0)")
U04, U05 = "metrics_run_04_deciles", "metrics_run_05_cumulative_lift"


def slice_source(sl) -> str:
    a, b, must = sl
    src = "".join(Path(mc.__file__).read_text().splitlines(keepends=True)[a - 1:b])
    assert must in src, "the slice does not hold the changed line: line numbers moved?"
    return textwrap.dedent(src)


def run_slice(sl, env: dict) -> dict:
    ns = dict(vars(mc))
    ns.update(env)
    exec(compile(slice_source(sl), f"{mc.__file__}:{sl[0]}-{sl[1]}", "exec"), ns)  # noqa: S102
    return ns


def real_run(name: str, prefix: int | None) -> dict:
    """The real mc.run on the scenario; the locals of `run` at the boundaries of the two steps."""
    src = SCEN / name
    ind = src
    if prefix is not None:
        ind = OUT / f"{name}_in{prefix}"
        ind.mkdir(parents=True, exist_ok=True)
        lines = (src / "risk_scores_validation.csv").read_text().splitlines(keepends=True)
        (ind / "risk_scores_validation.csv").write_text("".join(lines[:prefix + 1]))
        (ind / "risk_scores_train.csv").write_text((src / "risk_scores_train.csv").read_text())
    out = OUT / f"{name}_out{prefix or ''}"
    snap: dict = {}
    code = mc.run.__code__

    def local(frame, event, arg):
        if event == "line":
            ln = frame.f_lineno
            if "in04" not in snap and ln >= S04[0]:
                snap["in04"] = dict(frame.f_locals)
            if "in05" not in snap and ln > S04[1]:
                snap["in05"] = dict(frame.f_locals)
            if "out05" not in snap and ln > S05[1]:
                snap["out05"] = dict(frame.f_locals)
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is code else None

    sys.settrace(glob)
    try:
        mc.run(ind, out)
    finally:
        sys.settrace(None)
    assert set(snap) == {"in04", "in05", "out05"}, (name, set(snap))
    return snap


def canon(df: pl.DataFrame) -> dict:
    if "decile" in df.columns:
        assert df.schema["decile"] == pl.Int64, df.schema
        df = df.with_columns(pl.col("decile").cast(pl.Float64))  # R-F2I
    return cmp.canon_frame(df)


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(canon(df)))


def same(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return canon(a) == canon(b)


# ---------------------------------------------------------------- columns as short Lean terms
ENC = (
    "let HX := fun (n : Nat) (s : String) => (let a := s.toList.toArray; Pl.Col.f64 ((List.range n).map (fun (i : Nat) => "
    "let c := (a[i / 4]!).toNat; let d := if c ≥ 97 then c - 87 else c - 48; "
    "some (if (d / ([8, 4, 2, 1].getD (i % 4) 1)) % 2 == 1 then (1.0 : Float) else 0.0))) : Pl.Col Float); "
    "let RL := fun (e : Nat) (v : List (Nat × Nat)) => (Pl.Col.f64 (v.flatMap (fun (p : Nat × Nat) => "
    "List.replicate p.2 (some (Float.ofScientific p.1 true e)))) : Pl.Col Float); "
    "let PL := fun (e : Nat) (v : List Nat) => (Pl.Col.f64 (v.map (fun (k : Nat) => some (Float.ofScientific k true e))) : Pl.Col Float); "
    "let QQ := fun (v : List Int) => (Pl.Col.f64 (v.map (fun (k : Int) => if k == -1 then (none : Option Float) else if k == -2 then some (0.0 / 0.0) "
    "else if k == -3 then some (1.0 / 0.0) else if k == -4 then some (-1.0 / 0.0) else if k == -5 then some (-0.0) else some (Float.ofNat k.toNat / 32.0))) : Pl.Col Float); "
    "let FL := fun (s : String) => (Pl.Col.f64 (s.toList.map (fun (c : Char) => "
    "if c == '0' then some 0.0 else if c == '1' then some 1.0 else (none : Option Float))) : Pl.Col Float); "
)


def enc_flags(s: pl.Series) -> str:
    v = s.to_list()
    assert s.dtype == pl.Float64
    if any(x is None for x in v) or len(v) < 40:
        return '(FL "' + "".join("n" if x is None else {0.0: "0", 1.0: "1"}[x] for x in v) + '")'
    assert all(x in (0.0, 1.0) and cmp.fbits(x) in (cmp.fbits(0.0), cmp.fbits(1.0)) for x in v)
    bits = [int(x) for x in v] + [0] * (-len(v) % 4)
    hx = "".join("0123456789abcdef"[bits[i] * 8 + bits[i + 1] * 4 + bits[i + 2] * 2 + bits[i + 3]] for i in range(0, len(bits), 4))
    return f'(HX {len(v)} "{hx}")'


def enc_dec(s: pl.Series) -> str:
    """A Float64 column without null whose values are decimals k * 10^-e, e the smallest that fits."""
    v = s.to_list()
    assert s.dtype == pl.Float64 and all(x is not None for x in v)
    for e in (3, 4, 5, 10):
        ks = [round(x * 10**e) for x in v]
        if all(k >= 0 and cmp.fbits(float(f"{k}e-{e}")) == cmp.fbits(x) for k, x in zip(ks, v)):
            break
    else:
        raise AssertionError("not decimals")
    runs: list[list[int]] = []
    for k in ks:
        if runs and runs[-1][0] == k:
            runs[-1][1] += 1
        else:
            runs.append([k, 1])
    rl = f"(RL {e} [" + ", ".join(f"({k}, {c})" for k, c in runs) + "])"
    plain = f"(PL {e} [" + ", ".join(str(k) for k in ks) + "])"
    return rl if len(rl) < len(plain) else plain


def frame_term(cols: list[tuple[str, str]]) -> str:
    return "[" + ", ".join(f"({lt.lean_str(n)}, {t})" for n, t in cols) + "]"


class Group:
    """One eval input: a list of calls, each returning a list of digests (List Int)."""

    def __init__(self, lets: str):
        self.lets, self.calls, self.cases = lets, [], []

    def add(self, call: str, cases: list[tuple]):
        self.calls.append(call)
        self.cases += cases

    def flush(self, s: Suite):
        if self.calls:
            s.ints(self.lets, " ++ ".join(self.calls), self.cases, table=False)
        self.calls, self.cases = [], []


# ---------------------------------------------------------------- step 04
DEC = ENC + ("let d4 := fun (fr : Pl.Frame Float) => (let r := metrics_run_04_deciles fr; "
             "[dg (tR fr), dg (tR r.1), dg (tR r.2)]); ")
COLS04 = ["default_flag", "pd_logistic"]


ZERO_NOTE = ("recorded limit (1) of the polars prelude: max of zeros of opposite sign. The decile holds pd -0.0, 0.0, 0.0: "
             "polars gives max_pd = 0.0, the prelude's max the first of the equal values, -0.0. Checked cell by cell "
             "(work/t14_zero.py): the Lean frame equals the Python frame with that one cell replaced")


def dec_case(g: Group, name: str, df: pl.DataFrame, term: str) -> dict:
    ns = run_slice(S04, {"logit_scored_valid": df})
    kw = {"expect_diff": True, "note": ZERO_NOTE} if "signed zeros" in name else {}
    g.add(f"d4 {term}", [
        (f"{name}: input logit_scored_valid", U04, dgf(df)),
        (f"{name}: decile_data", U04, dgf(ns["decile_data"])),
        (f"{name}: decile_analysis", U04, dgf(ns["decile_analysis"]), kw)])
    da = ns["decile_analysis"]
    print(f"[04 {name}] rows {df.height}; total_count {da['total_count'].to_list()} defaults {da['defaults'].to_list()} "
          f"null default_rate {da['default_rate'].null_count()} lift {da['lift'].to_list()}")
    return ns


def f64(vals) -> pl.Series:
    return pl.Series("x", [None if v is None else float(v) for v in vals], dtype=pl.Float64)


inf = float("inf")
# hand-made inputs of step 04: (name, default_flag string (n = null), pd_logistic codes: k = k / 32,
# -1 null, -2 NaN, -3 +inf, -4 -inf, -5 -0.0)
H04 = [
    ("null pd, null flag, NaN pd, ties", "01n101n01011", [16, -1, 8, 8, -2, 24, 24, -1, 3, 29, 3, 10]),
    ("one row", "1", [13]),
    ("one row, null pd (every decile empty)", "1", [-1]),
    ("every pd null", "011", [-1, -1, -1]),
    ("every default_flag null (totals missing)", "nnnn", [3, 6, 10, 13]),
    ("no defaulter (0 / 0)", "00000", [3, 6, 6, 10, 13]),
    ("unsorted, 25 rows with ties", "".join(str((i * 7) % 3 % 2) for i in range(25)), [((i * 37) % 11) * 2 for i in range(25)]),
    ("signed zeros and infinities", "101010", [-5, 0, -3, -4, 16, 0]),
    ("a decile whose default_flag is all null", "nn" + "".join(str(i % 2) for i in range(2, 20)), [20 - i for i in range(20)]),
    ("11 distinct rows (every decile but one has one row)", "".join(str(i % 2) for i in range(11)), [2 * i for i in range(11)]),
]
QV = {-1: None, -2: nan, -3: inf, -4: -inf, -5: -0.0}


def hand04(flags: str, ks: list[int]) -> pl.DataFrame:
    return pl.DataFrame({"default_flag": f64([None if c == "n" else int(c) for c in flags]),
                         "pd_logistic": f64([QV[k] if k < 0 else k / 32 for k in ks])})


def suite_dec(runs: dict) -> Suite:
    s = Suite("t14_dec")
    g = Group(DEC)
    for name, snap in runs.items():
        i4, o4 = snap["in04"], snap["in05"]
        full = i4["logit_scored_valid"]
        assert full.schema["default_flag"] == pl.Float64 and full.schema["pd_logistic"] == pl.Float64
        # the real run: decile_data is the input plus `decile`
        assert o4["decile_data"].columns == full.columns + ["decile"] and same(o4["decile_data"].drop("decile"), full), name
        # the slice on the full frame is what the real run did
        nsf = run_slice(S04, {"logit_scored_valid": full})
        assert same(nsf["decile_data"], o4["decile_data"]) and same(nsf["decile_analysis"], o4["decile_analysis"]), name
        small = full.select(COLS04)
        term = frame_term([("default_flag", enc_flags(small["default_flag"])), ("pd_logistic", enc_dec(small["pd_logistic"]))])
        if len(term) > 20000:
            print(f"[04 {name}] {full.height} rows: Lean input of {len(term)} characters, not evaluated on this run")
            continue
        ns = dec_case(g, f"real mc.run, {name} ({small.height} rows, columns {COLS04})", small, term)
        assert same(ns["decile_analysis"], o4["decile_analysis"]), name
        assert same(ns["decile_data"], o4["decile_data"].select(COLS04 + ["decile"])), name
        if sum(len(c) for c in g.calls) > 9000:
            g.flush(s)
    g.flush(s)
    g = Group(DEC)
    for name, flags, pds in H04:
        df = hand04(flags, pds)
        dec_case(g, f"hand: {name}", df, frame_term([("default_flag", f'(FL "{flags}")'), ("pd_logistic", "(QQ [" + ", ".join(f"({k})" if k < 0 else str(k) for k in pds) + "])")]))
    g.flush(s)
    s.notes = {U04: "evaluated directly on logit_scored_valid; real = the locals of the real metrics_calculation.run at the "
                    "step boundaries (line tracer), Lean input = the columns the step reads (default_flag, pd_logistic), the "
                    "other columns pass through unchanged (asserted); hand = the step's source lines executed verbatim; "
                    "decile compared as Float64 (R-F2I)"}
    return s


# ---------------------------------------------------------------- step 05
SBPF = ('let sb := fun (x : Option Float) (_ : Int) => (match SB.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
        "let pf := fun (s : String) => Float.ofBits ((PF.lookup s).getD 1); ")
LIFT = ENC + (
    "let lift := fun (fc : Pl.Col Float) (D : List (Int × Int × Int)) (SB : List (Option UInt64 × String)) (PF : List (String × UInt64)) => ("
    + SBPF +
    "let dd : Pl.Frame Float := [(\"default_flag\", fc)]; "
    "let o := fun (k : Int) => if k == -1 then (none : Option Float) else if k == -7 then some (0.0 / 0.0) else some (Float.ofNat k.toNat); "
    "let da : Pl.Frame Float := [(\"decile\", Pl.Col.f64 (D.map (fun (p : Int × Int × Int) => o p.1))), "
    "(\"total_count\", Pl.Col.int (D.map (fun (p : Int × Int × Int) => if p.2.1 == -9 then none else some p.2.1))), "
    "(\"defaults\", Pl.Col.f64 (D.map (fun (p : Int × Int × Int) => o p.2.2)))]; "
    "[dg (tR dd), dg (tR da), dg (tR (metrics_run_05_cumulative_lift sb pf dd da))]); "
)


def run05(dd: pl.DataFrame, da: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    best: dict = {}
    o_best = sc.sas_best

    def w_best(x, w):
        r = o_best(x, w)
        assert w == 8
        assert best.setdefault(None if x is None else cmp.fbits(float(x)), r) == r
        return r

    sc.sas_best = w_best
    try:
        ns = run_slice(S05, {"decile_data": dd, "decile_analysis": da})
    finally:
        sc.sas_best = o_best
    return ns["cumulative_lift"], best


def lean_tables(best: dict) -> str:
    sb = ", ".join(f"({'none' if k is None else f'some {k}'}, {lt.lean_str(v)})" for k, v in best.items())
    pf = ", ".join(f"({lt.lean_str(v)}, {cmp.fbits(float(v))})" for v in sorted({v for v in best.values() if v}))
    return f"[{sb}] [{pf}]"


def lift_case(g: Group, name: str, dd: pl.DataFrame, da: pl.DataFrame) -> pl.DataFrame:
    assert dd.columns == ["default_flag"] and da.columns == ["decile", "total_count", "defaults"]
    assert da.schema["decile"] == pl.Int64 and da.schema["total_count"] == pl.Int64 and da.schema["defaults"] == pl.Float64
    out, best = run05(dd, da)

    def code(v):  # decile, defaults: -1 = null, -7 = NaN, else a non-negative integer
        if v is None:
            return -1
        if v != v:
            return -7
        assert v == int(v) and 0 <= v < 2**53 and cmp.fbits(float(v)) == cmp.fbits(float(int(v))), v
        return int(v)

    def cnt(v):  # total_count: -9 = null
        assert v != -9
        return -9 if v is None else v

    D = "[" + ", ".join(f"({code(a)}, {cnt(b)}, {code(c)})" for a, b, c in da.iter_rows()) + "]"
    g.add(f"lift {enc_flags(dd['default_flag'])} {D} {lean_tables(best)}", [
        (f"{name}: input decile_data", U05, dgf(dd)),
        (f"{name}: input decile_analysis", U05, dgf(da)),
        (f"{name}: cumulative_lift", U05, dgf(out))])
    print(f"[05 {name}] best {best}; cum_defaults {out['cum_defaults'].to_list()} cum_count {out['cum_count'].to_list()} "
          f"rate {out['cum_capture_rate'].to_list()} lift {out['cum_lift'].to_list()}")
    return out


# hand-made: (name, default_flag string, (decile, total_count, defaults) rows; 999 = NaN in `defaults`, None = null)
HL = [
    ("unsorted deciles, null defaults first / middle / last", "0110n1", [(3, 4, None), (1, 5, None), (5, 2, 2), (2, 3, 1), (4, 6, None), (6, 1, None)]),
    ("all defaults null", "nn", [(1, 2, None), (2, 2, None), (3, 1, None)]),
    ("no null", "0101", [(2, 2, 1), (1, 2, 1)]),
    ("NaN defaults is kept, not filled", "011", [(1, 2, 1), (2, 2, 999), (3, 2, None), (4, 2, 3)]),
    ("null decile key sorts first; one row", "1", [(None, 1, 1)]),
    ("total_count 0 on the first deciles and later (cum_count 0, then unchanged)", "01", [(1, 0, 0), (2, 0, 0), (3, 2, 1), (4, 0, 0), (5, 1, 0)]),
    ("total_count 0 everywhere", "01", [(1, 0, 0), (2, 0, 0)]),
    ("null total_count (cum_count null: not above 0)", "011", [(1, None, 1), (2, 3, 1), (3, None, 0)]),
    ("negative running count", "011", [(1, -2, 1), (2, 1, 1), (3, 4, 0)]),
    ("every default_flag null (totals missing): both 0, lift missing while empty", "nnn", [(1, 0, 0), (2, 2, 0), (3, 1, 0)]),
    ("default_flag all 0 (no defaulter)", "000", [(1, 0, 0), (2, 2, 0), (3, 1, 0)]),
    ("default_flag all 0, null defaults", "000", [(1, 2, None), (2, 1, 0)]),
    ("all defaulters", "1111", [(1, 1, 1), (2, 0, 0), (3, 3, 3)]),
]


def suite_lift(runs: dict) -> Suite:
    s = Suite("t14_lift")
    g = Group(LIFT)
    new = ["cum_defaults", "cum_count", "cum_capture_rate", "cum_lift"]
    for name, snap in runs.items():
        i5, o5 = snap["in05"], snap["out05"]
        ddf, daf = i5["decile_data"], i5["decile_analysis"]
        out_full, _ = run05(ddf, daf)
        assert same(out_full, o5["cumulative_lift"]), name  # the slice on the full frames is the real run
        dd, da = ddf.select("default_flag"), daf.select("decile", "total_count", "defaults")
        out = lift_case(g, f"real mc.run, {name} ({dd.height} rows)", dd, da)
        assert same(out.select(new), o5["cumulative_lift"].select(new)), name
        assert same(o5["cumulative_lift"].drop(new), daf.sort("decile", maintain_order=True)), name
        if sum(len(c) for c in g.calls) > 9000:
            g.flush(s)
    g.flush(s)
    g = Group(LIFT)
    for name, fl, rows in HL:
        dd = pl.DataFrame({"default_flag": f64([None if ch == "n" else int(ch) for ch in fl])})
        da = pl.DataFrame({"decile": pl.Series("x", [r[0] for r in rows], dtype=pl.Int64),
                           "total_count": pl.Series("x", [r[1] for r in rows], dtype=pl.Int64),
                           "defaults": f64([None if r[2] is None else (nan if r[2] == 999 else r[2]) for r in rows])})
        lift_case(g, f"hand: {name}", dd, da)
    g.flush(s)
    s.notes = {U05: "evaluated directly on decile_data / decile_analysis; real = the locals of the real metrics_calculation.run at "
                    "the step boundaries (line tracer), Lean input = the columns the step reads (default_flag; decile, total_count, "
                    "defaults), the other columns pass through unchanged (asserted); hand = the step's source lines executed "
                    "verbatim; decile compared as Float64 (R-F2I); sas_best / parse_float = lookup tables of the values that occur"}
    return s


RUNS = [("real_metrics", None), ("real_metrics", 300), ("fix_Q23_nodefaulter", None), ("fix_G43", None),
        ("edge_metrics_a", None), ("edge_metrics_b", None), ("edge_metrics_c", None)]


def main():
    runs = {}
    for name, prefix in RUNS:
        runs[name if prefix is None else f"{name}, first {prefix} validation rows"] = real_run(name, prefix)
    suite_dec(runs).write()
    suite_lift(runs).write()


if __name__ == "__main__":
    main()
