"""Fuzz pass 2026-11-16, port-translator-1 (did not write the unit): def:run_py
(metrics_calculation.run) on generated small score files. Protocol: prompts/fuzz-2026-11-16.md.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_run_py_gen.py [calls] [seeds per call]
      -> work/fz_run_py.json, .inputs.json, .fuzz.json
  eval_decl each input on def:zz_carrier_m; python3 diffeval/fuzz_collect.py 1 fz_run_py; compare.py;
  python3 diffeval/fuzz_receipt.py fz_run_py

One case = one seed s. Both sides build from s (kit.gF, every value drawn from a pool):
  validation table: nv(s) in 1..9 rows; row_id = 1.., default_flag from EF, pd_logistic from EP,
                    credit_risk_score from ES
  training table:   nt(s) in 1..9 rows; row_id, credit_risk_score from ES
Python: the two tables are written as CSV files and the REAL mc.run runs on them
(write_sas_csv replaced by a recorder, as t16_gen.py). A seed is used only if the frames
proc_import_csv returns are the generated tables bit for bit (a column with no value is not imported
as a number, -0.0 may lose its sign: such seeds are counted under "file cannot hold the table").
Lean: run_py on the tables built from the same seed; one digest per seed over the digests of the two
input tables, the number of files, and every (file name, table).
Parameters: sas_best / parse_float = lookup tables of the real sas_best(x, 8) and float() over the
calls of _into_float (as t16); today = the run date as text; fsum = an exact-sum lambda (error-free
partials, then their sum), checked in Python against math.fsum on every list the run passes (a seed
where they differ is not used); sas_d8 = an injective stand-in on BOTH sides ("." for missing, else
the decimal text of the IEEE bits): the parameter is opaque to run_py, and a lookup table of the real
D8. texts would make the inputs too long to carry thousands of cases.
Precondition (def:run_py_precond), rendered in Python: the table clauses only (both tables non-empty,
same shape in every row, numeric default_flag / pd_logistic / credit_risk_score): they hold for every
used seed by construction. The ten step preconditions are NOT rendered here (the step fuzzers render
them): every used seed on which Python returns is compared and counted as kept; a seed on which
Python raises is listed with its exception, to be read against the step preconditions.
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import t16_gen as t16  # noqa: E402  (sets the carrier to def:zz_carrier_m; RUN, SIX, PRINTED)
import b6_gen as b6  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

U = "run_py"
DECOMP = 5000135
# found by this fuzz run (30 of 2,092 seeds differ) and traced: see the receipt
LIMIT = ("30 seeds, each with pd_logistic -0.0 and 0.0 in one decile: recorded limit (1) of the polars prelude (min / max of zeros "
         "of opposite sign: the prelude returns the first of the equal values, polars -0.0 for min and 0.0 for max). Shown two "
         "ways: seed 5000135 file by file in Lean (only decile_analysis.csv and printed_cumulative_lift.csv differ), and for all "
         "30 seeds the Python result with min_pd / max_pd replaced by the first-of-equal value has exactly the Lean digest")


def nx(x: float, up: bool) -> float:
    return math.nextafter(x, math.inf if up else -math.inf)


EF = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, None]
EP = [None, 0.0, -0.0, 1.0, 0.5, nx(0.5, True), nx(0.5, False), 0.3, nx(0.3, True), nx(0.3, False), 0.4, nx(0.4, True),
      0.6, nx(0.6, False), 0.7, nx(0.7, True), 0.1, 0.9, 0.25, 0.25, 0.75, 1e-300, 5e-324, 0.1 + 1e-9, 0.1 + 1e-13,
      0.1, 0.5, 0.5, 2.0, -0.25]
ES = [None, 600.0, 850.0, 725.0, nx(725.0, True), nx(725.0, False), 612.5, 837.5, 725.0, 600.0, 1e300, -5.0, 0.0,
      -0.0, 700.0, 700.0, 650.25, 1e-300, 849.9999999999999, 600.0000000000001]
OV, OP, OS_, OT = 0, 100000, 200000, 300000


def n_rows(s: int, j: int) -> int:
    return 1 + kit.hsh(s, 1000 + j) % 9


def tables(s: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    nv, nt = n_rows(s, 0), n_rows(s, 1)
    f = pl.Float64
    v = pl.DataFrame({"row_id": [float(i + 1) for i in range(nv)], "default_flag": kit.gF(s + OV, nv, 100, 0, EF),
                      "pd_logistic": kit.gF(s + OP, nv, 100, 0, EP), "credit_risk_score": kit.gF(s + OS_, nv, 100, 0, ES)},
                     schema={"row_id": f, "default_flag": f, "pd_logistic": f, "credit_risk_score": f})
    t = pl.DataFrame({"row_id": [float(i + 1) for i in range(nt)], "credit_risk_score": kit.gF(s + OT, nt, 100, 0, ES)},
                     schema={"row_id": f, "credit_risk_score": f})
    return v, t


def csv(df: pl.DataFrame) -> str:
    def cell(x):
        if x is None:
            return ""
        return str(int(x)) if x == int(x) and abs(x) < 1e15 and not (x == 0 and math.copysign(1, x) < 0) else repr(x)
    return ",".join(df.columns) + "\n" + "".join(",".join(cell(x) for x in r) + "\n" for r in df.rows())


def bits(df: pl.DataFrame):
    return [(n, str(df.schema[n]), [None if x is None else cmp.fbits(x) for x in df.get_column(n).to_list()]) for n in df.columns]


def fs_mirror(xs: list[float]) -> float:
    """the Lean FS below, operation for operation"""
    ps: list[float] = []
    for x in xs:
        a, out = x, []
        for y in ps:
            s_ = a + y
            bb = s_ - a
            e = (a - (s_ - bb)) + (y - bb)
            if e != 0:
                out.append(e)
            a = s_
        ps = out + [a]
    r = 0.0
    for y in ps:
        r = r + y
    return r


FS = ("let FS := fun (xs : List Float) => (let ps := xs.foldl (fun (ps : List Float) (x : Float) => "
      "(let r := ps.foldl (fun (a : Float × List Float) (y : Float) => (let s := a.1 + y; let bb := s - a.1; "
      "let e := (a.1 - (s - bb)) + (y - bb); (s, if e != 0 then a.2 ++ [e] else a.2))) (x, ([] : List Float)); "
      "r.2 ++ [r.1])) ([] : List Float); ps.foldl (fun (a y : Float) => a + y) 0.0); ")
D8 = 'let d8 := fun (x : Option Float) => (match x with | none => "." | some v => toString v.toBits.toNat); '


def d8_standin(x):
    return "." if x is None else str(cmp.fbits(float(x)))


def pyrun(s: int) -> dict:
    v, t = tables(s)
    rec: dict = {"files": [], "best": {}, "raised": None, "fsum_ok": True, "held": True}
    o_write, o_best, o_d8, o_fsum = sc.write_sas_csv, sc.sas_best, sc.sas_d8, math.fsum

    def w_best(x, width):
        r = o_best(x, width)
        if width == 8 and sys._getframe(1).f_code is mc._into_float.__code__:
            assert rec["best"].setdefault(t16.key(x), r) == r
        return r

    def w_fsum(xs):
        xs = list(xs)
        r = o_fsum(xs)
        if cmp.fbits(fs_mirror(xs)) != cmp.fbits(r):
            rec["fsum_ok"] = False
        return r

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is mc.run.__code__:
            rec["today"] = frame.f_locals.get("model_performance_metrics")

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        outd.mkdir()
        (ind / "risk_scores_validation.csv").write_text(csv(v))
        (ind / "risk_scores_train.csv").write_text(csv(t))
        try:
            iv = sc.proc_import_csv(ind / "risk_scores_validation.csv", guessingrows=20)
            it = sc.proc_import_csv(ind / "risk_scores_train.csv", guessingrows=20)
            rec["held"] = bits(iv) == bits(v) and bits(it) == bits(t)
        except Exception:  # noqa: BLE001
            rec["held"] = False
        if not rec["held"]:
            return rec
        sc.write_sas_csv, sc.sas_best, sc.sas_d8, math.fsum = (lambda df, path, formats=None: rec["files"].append((Path(path).name, df))), w_best, d8_standin, w_fsum
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mc.run(ind, outd)
        except Exception as e:  # noqa: BLE001
            rec["raised"] = f"{type(e).__name__}: {str(e)[:120]}"
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.sas_best, sc.sas_d8, math.fsum = o_write, o_best, o_d8, o_fsum
    rec["v"], rec["t"] = v, t
    return rec


LETS_GEN = (
    "let cellO := fun (o : Option Float) => (Tabular.Cell.num o : Tabular.Cell Float); "
    f"let EF : List (Option Float) := {lt.lean_opt_floats(EF)}; let EP : List (Option Float) := {lt.lean_opt_floats(EP)}; "
    f"let ES : List (Option Float) := {lt.lean_opt_floats(ES)}; "
    "let nr := fun (s j : Nat) => 1 + ((hsh s (1000 + j)) % 9).toNat; "
    "let rid := fun (i : Nat) => (\"row_id\", cellO (some (Float.ofNat (i + 1)))); "
    "let V := fun (s : Nat) => (let n := nr s 0; ((List.range n).zip ((gF s n 100 0 EF).zip ((gF (s + 100000) n 100 0 EP).zip (gF (s + 200000) n 100 0 ES)))).map "
    "(fun (q : Nat × Option Float × Option Float × Option Float) => [rid q.1, (\"default_flag\", cellO q.2.1), (\"pd_logistic\", cellO q.2.2.1), (\"credit_risk_score\", cellO q.2.2.2)]) : Tabular.Table Float); "
    "let T := fun (s : Nat) => (let n := nr s 1; ((List.range n).zip (gF (s + 300000) n 100 0 ES)).map "
    "(fun (q : Nat × Option Float) => [rid q.1, (\"credit_risk_score\", cellO q.2)]) : Tabular.Table Float); "
    "let one := fun (s : Nat) => dg ((RUN (V s) (T s)).map (fun (i : Int) => i.toNat.toUInt64)); "
)


def main() -> None:
    calls = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    base0 = 5_000_000
    s = Suite("fz_run_py", generator="port-to-lean/diffeval/units/fz_run_py_gen.py")
    stat = {"generated": 0, "kept": 0, "not_held": 0, "fsum": 0, "raised": []}
    for c in range(calls):
        base = base0 + c * per
        best: dict = {}
        today = None
        bad, cases = [], []
        for seed in range(base, base + per):
            stat["generated"] += 1
            r = pyrun(seed)
            if not r["held"]:
                stat["not_held"] += 1
                bad.append(seed)
                continue
            if r["raised"] is not None:
                stat["raised"].append((seed, r["raised"]))
                bad.append(seed)
                continue
            if not r["fsum_ok"]:
                stat["fsum"] += 1
                bad.append(seed)
                continue
            for k, v in r["best"].items():
                assert best.setdefault(k, v) == v
            if r.get("today") is not None:
                today = r["today"].get_column("validation_date").to_list()[0].isoformat()
            ints = [t16.dgt_in(r["v"]), t16.dgt_in(r["t"]), len(r["files"])] + [b6.dgt(n, df) for n, df in r["files"]]
            cases.append((f"seed {seed}: {r['v'].height} validation / {r['t'].height} training rows, {len(r['files'])} files",
                          U, cmp.digest(ints), {"fz": "kept"}))
            stat["kept"] += 1
        sb, pf = b6.lean_tables(best, None).split("] [", 1)
        lets = (FS + f"let SB : List (Option UInt64 × String) := {sb}]; let PF : List (String × UInt64) := [{pf}; " + b6.SBPF + D8
                + f"let today : Tabular.Cell Float := Tabular.Cell.str (some {lt.lean_str(today or '2000-01-01')}); "
                + t16.RUN + LETS_GEN
                + f"let BAD : List Nat := {lt.lean_list([str(b) for b in bad])}; ")
        body = f"(((List.range {per}).map (fun (i : Nat) => {base} + i)).filter (fun (s : Nat) => !(BAD.contains s))).map one"
        if c == 1:
            # the first differing seed of call 0, file by file (SB / PF of that seed added to this call's tables)
            r = pyrun(DECOMP)
            for k, v in r["best"].items():
                assert best.setdefault(k, v) == v
            sb, pf = b6.lean_tables(best, None).split("] [", 1)
            lets = lets.split("let SB :")[0] + f"let SB : List (Option UInt64 × String) := {sb}]; let PF : List (String × UInt64) := [{pf}; " + lets.split("let sb :=", 1)[1].join(["let sb :=", ""])[:-0 or None]
            ints = [t16.dgt_in(r["v"]), t16.dgt_in(r["t"]), len(r["files"])] + [b6.dgt(n, df) for n, df in r["files"]]
            names = ["input validation", "input training", "number of files"] + [n for n, _ in r["files"]]
            body = f"({body}) ++ RUN (V {DECOMP}) (T {DECOMP})"
            cases += [(f"decomposition of seed {DECOMP}: {n}", "run_py (one differing seed, file by file)", v, {"fz": "rejected"})
                      for n, v in zip(names, ints, strict=True)]
        s.ints(lets, body, cases, gen=True, table=True)
    s.write()
    note = (f"one case = one seed: validation 1-9 rows, training 1-9 rows, values from pools (flags 0/1/null; probabilities with the "
            f"thresholds 0.3-0.7 and one ulp either side, 0, -0, 1, ties, 1e-300, 5e-324, 2, -0.25, null; scores with ties, one ulp "
            f"either side, 1e300, null). Not used: {stat['not_held']} seeds the CSV file cannot hold (a column with no value; -0.0), "
            f"{stat['fsum']} where the exact-sum lambda differs from math.fsum, {len(stat['raised'])} where Python raises: "
            f"{sorted({r for _, r in stat['raised']})[:4]}. sas_d8 is an injective stand-in on both sides; step preconditions not "
            f"rendered (table clauses hold by construction)")
    (HERE.parent / "work" / "fz_run_py.fuzz.json").write_text(json.dumps({
        "fuzzer": "port-translator-1", "generator": "port-to-lean/diffeval/units/fz_run_py_gen.py",
        "units": {U: {"seeds": f"{base0}..{base0 + calls * per - 1}", "generated": stat["generated"], "kept": stat["kept"],
                      "python_raises_inside_precondition": [], "python_raises_table_clauses_hold": stat["raised"][:50],
                      "note": note,
                      "all_differences_are_recorded_limit": LIMIT}}}, indent=1))
    print(stat["generated"], "generated", stat["kept"], "kept", stat["not_held"], "not held by the file", stat["fsum"], "fsum",
          len(stat["raised"]), "raised", sorted({r for _, r in stat["raised"]}))
    for g in json.loads((HERE.parent / "work" / "fz_run_py.inputs.json").read_text()):
        print([len(x) for x in g["inputs"]])


if __name__ == "__main__":
    main()
