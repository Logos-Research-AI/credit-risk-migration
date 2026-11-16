"""T13 (update after verification, 2026-11-16): differential test of def:metrics_run_02_ks,
credit_risk/metrics_calculation.py:156-196.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t13_gen.py   -> work/t13_ks.*
  (eval_decl each input of work/t13_ks.inputs.json on def:zz_carrier_m / zz_carrier_m, outputs one
   per line in work/t13_ks.out.txt)
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/t13_ks.json diffeval/work/t13_ks.out.txt

Python side: the REAL metrics_calculation.run on a scenario directory (or on a temporary directory
holding a subset of the lines of the real validation file, verbatim, next to the whole training
file); a profile hook copies the locals of `run` when it returns. Nothing of `run` is copied here.
Hand-made frames that the CSV import cannot produce (NaN, -0.0, a null default_flag ...) go through
the source lines 156-196 read from the file at run time and executed with the module's globals.
Lean side: the unit on the frame restricted to (row_id, default_flag, pd_logistic[, credit_risk_score]);
the Python results are asserted identical on the restricted frame (the slice reads no other column).
Each case returns three digests: the input frame, the sorted frame, ks_statistic.
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
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_m", "zz_carrier_m")

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

SCEN = ROOT / "judge" / "scenarios"
A, B = 156, 196
U = "metrics_run_02_ks"
nan = float("nan")
BEST: dict = {}


def key(x):
    return None if x is None else cmp.fbits(float(x))


@contextlib.contextmanager
def recording():
    o = sc.sas_best

    def w(x, width):
        r = o(x, width)
        if width == 8 and sys._getframe(1).f_code is mc._into_float.__code__:  # the calls of _into_float only
            assert BEST.setdefault(key(x), r) == r
        return r

    sc.sas_best = w
    try:
        yield
    finally:
        sc.sas_best = o


def real_run(ind: Path) -> dict:
    rec: dict = {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is mc.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    with tempfile.TemporaryDirectory() as d:  # no recording: `expected` makes the calls of the slice again
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mc.run(ind, Path(d))
        finally:
            sys.setprofile(None)
    rec["valid"] = sc.proc_import_csv(ind / "risk_scores_validation.csv", guessingrows=20)
    return rec


def slice_source() -> str:
    src = "".join(Path(mc.__file__).read_text().splitlines(keepends=True)[A - 1:B])
    assert "ne_missing" in src and src.lstrip().startswith("# metrics_calculation.sas:124-126") and "sql_min" in src
    return textwrap.dedent(src)


def run_slice(df: pl.DataFrame) -> dict:
    ns = dict(vars(mc))
    ns["logit_scored_valid"] = df
    with recording():
        exec(compile(slice_source(), f"{mc.__file__}:{A}-{B}", "exec"), ns)  # noqa: S102
    return ns


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def same(a, b) -> bool:
    return cmp.canon_frame(a) == cmp.canon_frame(b)


def expected(name: str, r: dict, cols: list[str]) -> tuple[pl.DataFrame, list]:
    """The restricted input frame and the three expected digests of a real run."""
    L = r["locals"]
    v = r["valid"].select(cols)
    assert all(t == pl.Float64 for t in v.dtypes), (name, v.schema)
    srt, ks = L["logit_scored_valid"].select(cols), L["ks_statistic"]
    ns = run_slice(v)  # the slice on the restricted frame gives the results of the real run
    assert same(ns["logit_scored_valid"], srt) and same(ns["ks_statistic"], ks), name
    kc = L["ks_calculation"]
    print(f"[{name}] rows={v.height} ks_statistic={ks.rows()} schema={[str(t) for t in ks.dtypes]} "
          f"null ks_value={kc.get_column('ks_value').null_count()} distinct pd={v.get_column('pd_logistic').n_unique()}")
    return v, [(f"{name}: input frame", U, dgf(v)), (f"{name}: logit_scored_valid sorted", U, dgf(srt)),
               (f"{name}: ks_statistic", U, dgf(ks))]


# ---------------------------------------------------------------- the Lean side, kept short
# (every eval input is typed by hand into the eval_decl call)
# digests as kit.KIT_NOTABLE computes them, for frames whose columns are all Float64
KITF = (
    "let mx := fun (h x : UInt64) => let g := (h ^^^ x) * 1099511628211; g ^^^ (g >>> 32); "
    "let dg := fun (t : List UInt64) => ((t.foldl mx 14695981039346656037).toNat : Int); "
    "let tS := fun (s : String) => s.length.toUInt64 :: s.toList.map (fun c => c.toNat.toUInt64); "
    "let tF := fun (v : List (Option Float)) => v.length.toUInt64 :: v.flatMap (fun o => (match o with | none => [0] | some x => [1, x.toBits] : List UInt64)); "
    "let tC := fun (c : Pl.Col Float) => (match c with | .f64 v => 1 :: tF v | _ => [99] : List UInt64); "
    "let tR := fun (fr : Pl.Frame Float) => fr.length.toUInt64 :: fr.flatMap (fun p => tS p.1 ++ tC p.2); "
)
# sas_best / parse_float as lookups in the pairs Python produced: T = [(count, text, float(text))],
# all three integers here (asserted). An argument Python never passed gives "?" / 5e-324.
SBPF = ('let sb := fun (x : Option Float) (_ : Int) => (match T.find? (fun (t : Nat × String × Nat) => x.map Float.toBits == some (Float.ofNat t.1).toBits) with | some t => t.2.1 | none => "?"); '
        "let pf := fun (s : String) => (match T.find? (fun (t : Nat × String × Nat) => t.2.1 == s) with | some t => Float.ofNat t.2.2 | none => Float.ofBits 1); ")
THREE = ("let three := fun (f : Pl.Frame Float) => (let r := metrics_run_02_ks sb pf f; "
         "([dg (tR f), dg (tR r.1), dg (tR r.2)] : List Int)); ")
# value codes: -1 null, -2 NaN, -3 -0.0, k >= 0: k * 10^-d (default_flag: d = 0)
VAL = ("let val := fun (d : Nat) (k : Int) => (if k == -1 then none else if k == -2 then some (0.0 / 0.0) else "
       "if k == -3 then some (-0.0) else some (Float.ofScientific k.toNat true d) : Option Float); ")
# mk base d C: row_id = base + i, default_flag = val 0 C[i].1, pd_logistic = val d C[i].2
MK = ("let mk := fun (base d : Nat) (C : List (Int × Int)) => ("
      'let f : Pl.Frame Float := [("row_id", Pl.Col.f64 ((List.range C.length).map (fun (i : Nat) => some (Float.ofNat (base + i))))), '
      '("default_flag", Pl.Col.f64 (C.map (fun (p : Int × Int) => val 0 p.1))), '
      '("pd_logistic", Pl.Col.f64 (C.map (fun (p : Int × Int) => val d p.2)))]; f); ')
# mkS base w d s: row_id = base + i; row i is w digits of s: code = k * 2 + flag, pd_logistic = k * 10^-d
MKS = ("let mkS := fun (base w d : Nat) (s : String) => (let a := s.toList.toArray; let n := a.size / w; "
       "let code := fun (i : Nat) => (List.range w).foldl (fun (acc j : Nat) => acc * 10 + ((a[w * i + j]!).toNat - 48)) 0; "
       'let f : Pl.Frame Float := [("row_id", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofNat (base + i))))), '
       '("default_flag", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofNat (code i % 2))))), '
       '("pd_logistic", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofScientific (code i / 2) true d))))]; f); ')
# mkL d C: rows (row_id, code): code = k * 2 + flag, pd_logistic = k * 10^-d
MKL = ("let mkL := fun (d : Nat) (C : List (Nat × Nat)) => ("
       'let f : Pl.Frame Float := [("row_id", Pl.Col.f64 (C.map (fun (p : Nat × Nat) => some (Float.ofNat p.1)))), '
       '("default_flag", Pl.Col.f64 (C.map (fun (p : Nat × Nat) => some (Float.ofNat (p.2 % 2))))), '
       '("pd_logistic", Pl.Col.f64 (C.map (fun (p : Nat × Nat) => some (Float.ofScientific (p.2 / 2) true d))))]; f); ')
COLS3 = ["row_id", "default_flag", "pd_logistic"]


def tables() -> str:
    rows = []
    for k, v in BEST.items():
        x = lt.from_bits(k)
        assert x == int(x) and x >= 0 and v and float(v) == int(float(v)), (x, v)
        rows.append(f'({int(x)}, "{v}", {int(float(v))})')
    return f"let T : List (Nat × String × Nat) := [{', '.join(rows)}]; "


def codes(v: pl.DataFrame, d: int) -> list[tuple[int, int]]:
    out = []
    for r, f, p in v.select(COLS3).iter_rows():
        assert f in (0.0, 1.0) and r == int(r) and r >= 0
        k = round(p * 10**d)
        assert cmp.fbits(float(f"{k}e-{d}")) == cmp.fbits(p), p
        out.append((int(r), k * 2 + int(f)))
    return out


def vcode(x, d: int) -> int:
    if x is None:
        return -1
    if x != x:
        return -2
    if x == 0 and cmp.fbits(x) != 0:
        return -3
    k = round(x * 10**d)
    assert cmp.fbits(float(f"{k}e-{d}")) == cmp.fbits(x), (x, d)
    return k


def mk_term(df: pl.DataFrame, d: int) -> str:
    assert df.columns == COLS3 and all(t == pl.Float64 for t in df.dtypes), df.schema
    rid = df.get_column("row_id").to_list()
    base = int(rid[0])
    assert all(r == base + i for i, r in enumerate(rid))
    cs = [(vcode(f, 0), vcode(p, d)) for f, p in df.select("default_flag", "pd_logistic").iter_rows()]
    fm = lambda k: f"({k})" if k < 0 else str(k)  # noqa: E731
    return f"(mk {base} {d} [" + ", ".join(f"({fm(a)}, {fm(b)})" for a, b in cs) + "])"


def main() -> None:
    s = Suite("t13_ks")
    F = pl.Float64

    def add(pre: str, body: str, cases: list) -> None:
        s.ints(tables() + SBPF + THREE + pre, body, cases, use_kit=False)
        s.inputs[-1]["text"] = "(" + KITF + s.inputs[-1]["text"][1:]
        BEST.clear()

    # ---- input 1: the small scenarios, whole files (real runs)
    terms, cases = [], []
    for name, d in [("fix_Q23_tie", 1), ("fix_Q23_near", 13), ("fix_Q24", 1), ("fix_Q23", 1), ("fix_Q23_nodefaulter", 1),
                    ("fix_Q23_alldefaulters", 1)]:
        r = real_run(SCEN / name)
        v, cs = expected(name, r, COLS3)
        terms.append("three " + mk_term(v, d))
        cases += cs
    add(VAL + MK, "(" + " ++ ".join(terms) + ")", cases)

    # ---- input 2: hand-made frames through the source lines 156-196
    hand = {
        "nulls NaN zeros ties, null flag": (1, [0.0, 1.0, None, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0, None, 1.0, 0.0, 2.0, 0.0, 1.0],
                                            [0.3, None, 0.3, nan, 0.0, -0.0, None, 0.5, nan, 0.3, 0.1, 0.5, -0.0, 0.1, None, 0.7]),
        "one row, flag 0": (2, [0.0], [0.25]),
        "one row, flag 1": (2, [1.0], [0.25]),
        "one row, null pd": (1, [1.0], [None]),
        "all pd null": (1, [1.0, 0.0, 0.0], [None, None, None]),
        "all pd NaN": (1, [1.0, 0.0, 1.0], [nan, nan, nan]),
        "one value of pd": (1, [1.0, 0.0, 0.0, 1.0], [0.4] * 4),
        "no defaulter, ties, a null pd": (1, [0.0] * 5, [0.4, 0.2, None, 0.2, 0.9]),
        "no non-defaulter, null flags": (1, [1.0, None, 1.0, 3.0], [0.4, 0.2, 0.2, 0.1]),
        "maximum attained twice": (1, [0.0, 1.0, 0.0, 1.0, 0.0, 1.0], [0.5, 0.6, 0.1, 0.2, 0.3, 0.4]),
        "maximum on the null group and later": (1, [0.0, 1.0, 0.0, 1.0], [None, 0.6, 0.1, 0.2]),
        "40 rows, heavy ties": (4, [float((i * 7 + i // 3) % 5 == 0) for i in range(40)], [((i * 13) % 9) / 16 for i in range(40)]),
    }
    terms, cases = [], []
    for name, (d, fl, pdv) in hand.items():
        df = pl.DataFrame({"row_id": [float(i) for i in range(len(fl))], "default_flag": fl, "pd_logistic": pdv},
                          schema={"row_id": F, "default_flag": F, "pd_logistic": F})
        ns = run_slice(df)
        ks = ns["ks_statistic"]
        print(f"[hand: {name}] ks_statistic={ks.rows()} ks_value={ns['ks_calculation'].get_column('ks_value').to_list()}")
        terms.append("three " + mk_term(df, d))
        cases += [(f"hand ({name}): input frame", U, dgf(df)), (f"hand ({name}): logit_scored_valid sorted", U, dgf(ns["logit_scored_valid"])),
                  (f"hand ({name}): ks_statistic", U, dgf(ks))]
    add(VAL + MK, "(" + " ++ ".join(terms) + ")", cases)

    # ---- inputs 3-5: edge_metrics_a/b/c, the whole validation file
    for name, d, w in [("edge_metrics_a", 2, 3), ("edge_metrics_b", 3, 4), ("edge_metrics_c", 2, 3)]:
        r = real_run(SCEN / name)
        v, cs = expected(name, r, COLS3)
        cd = codes(v, d)
        base = cd[0][0]
        assert all(rid == base + i for i, (rid, _) in enumerate(cd)) and all(c < 10**w for _, c in cd)
        txt = "".join(f"{c:0{w}d}" for _, c in cd)
        add(MKS, f'(three (mkS {base} {w} {d} "{txt}"))', cs)

    # ---- inputs 6-7: real_metrics. The whole file (45000 rows) cannot be typed into an eval call:
    # two subsets of its lines, verbatim, each run through the real mc.run with the whole training file
    rdir = SCEN / "real_metrics"
    full = real_run(rdir)
    print(f"[real_metrics whole file, Python only] ks_statistic={full['locals']['ks_statistic'].rows()}")
    lines = (rdir / "risk_scores_validation.csv").read_text().splitlines(keepends=True)
    pd_all = full["valid"].get_column("pd_logistic").to_list()
    seen: dict = {}
    for i, p in enumerate(pd_all):
        seen.setdefault(p, []).append(i)
    tied_vals = [p for p, ix in seen.items() if len(ix) > 1][:80]  # first 80 tied values, by appearance
    tied_rows = sorted(i for p in tied_vals for i in seen[p])[:200]
    for tag, rows in [("first 200 lines", list(range(200))), ("the rows of its first tied probabilities", tied_rows)]:
        with tempfile.TemporaryDirectory() as d:
            ind = Path(d)
            (ind / "risk_scores_validation.csv").write_text(lines[0] + "".join(lines[1 + i] for i in rows))
            (ind / "risk_scores_train.csv").write_bytes((rdir / "risk_scores_train.csv").read_bytes())
            r = real_run(ind)
        name = f"real_metrics ({tag})"
        v, cs = expected(name, r, COLS3)
        cd = codes(v, 10)
        add(MKL, "(three (mkL 10 [" + ", ".join(f"({a}, {c})" for a, c in cd) + "]))", cs)

    # ---- input 8: zeros of both signs with no maximum (raised in review as a possible prelude limit)
    df = pl.DataFrame({"row_id": [0.0, 1.0], "default_flag": [0.0, 0.0], "pd_logistic": [0.0, -0.0]},
                      schema={"row_id": F, "default_flag": F, "pd_logistic": F})
    ns = run_slice(df)
    print(f"[limit: zeros] ks_statistic={ns['ks_statistic'].rows()}")
    # measured here: the slice gives +0.0 for [0.0, -0.0] and -0.0 for [-0.0, 0.0] (the first of the equal values,
    # as the prelude's min); so this is a plain case, not an expected difference
    add(VAL + MK, "(three " + mk_term(df, 1) + ")",
        [("limit (zeros of both signs, no maximum): input frame", U, dgf(df)),
         ("limit (zeros of both signs, no maximum): logit_scored_valid sorted", U, dgf(ns["logit_scored_valid"])),
         ("limit (zeros of both signs, no maximum): ks_statistic", U, dgf(ns["ks_statistic"]))])

    s.notes = {U: "real mc.run on fix_Q23*, fix_Q24, edge_metrics_a/b/c (whole files) and two subsets of the lines of "
                  "real_metrics (the first 200; the rows of the first tied probabilities); hand-made frames through the source lines"}
    s.write()
    for i, inp in enumerate(s.inputs):
        (suite_mod.WORK / f"t13_ks.in{i}.txt").write_text(inp["text"])
        print(i, len(inp["text"]))


main()
