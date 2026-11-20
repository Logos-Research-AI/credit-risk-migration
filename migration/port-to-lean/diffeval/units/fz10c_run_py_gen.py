"""Fidelity pass 2026-11-20, third attempt, label compositions: def:run_py (metrics_calculation.run) as a whole,
against the REAL metrics_calculation.run at port HEAD 4a757fb, through the carrier def:zz_carrier_fid_2.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_run_py_gen.py [calls] [seeds per call]
      -> work/fz10c_run_py.json, .inputs.json, .fuzz.json
  eval_decl each input on def:zz_carrier_fid_2 / zz_carrier_fid_2; outputs by script
  (diffeval/units/fz10_collect.py <session record> fz10c_run_py); compare.py.

Successor of fz_run_py_gen.py (2026-11-16, old blueprint id; its pools, CSV writer, exact-sum lambda FS and
sas_d8 stand-in are imported unchanged). New: modes chosen by the seed, m = hsh(s, 7) % 10:
  0-5  both score files with rows: validation nv rows (1..9, or 10..40 when hsh(s, 8) % 5 == 0), training 1..9
  6    validation file with a header and no row (valid_exists False; Lean `some []`)
  7    training scores with credit_risk_score blank on every row (imported as a String column of nulls;
       Lean `Cell.str none`, the nulltext clause of def:run_py_precond)
  8    validation file absent (the stop of :96-102; Lean `none`)
  9    training file absent, and the validation file too when hsh(s, 10) % 2 == 0
Python: the files are written as CSV and the REAL mc.run runs (write_sas_csv recorded; sas_best of _into_float,
parse_float recorded as lookup tables as before; sas_d8 an injective stand-in on both sides; math.fsum = the
real one, the seed is used only if the exact-sum lambda FS of the Lean input gives the same bits on every list).
A seed is used only if proc_import_csv returns the generated tables (a column with no value / -0.0 do not
survive a CSV file: "file cannot hold").
Precondition def:run_py_precond, rendered in Python (`pre`): table clauses (wf: non-empty, same shape per row,
distinct names; numeric default_flag / pd_logistic / credit_risk_score in validation or the empty table;
training credit_risk_score numeric or text-all-null) hold by construction and are asserted on the imports; the
step preconditions are not rendered one by one: a seed where Python raises (other than the stop) is reported
as raising inside the table clauses (to be read against the step clauses), not compared.
Expected per seed: digest over [digest of the validation input, digest of the training input, number of files
or -1 for none] + one digest per (file name, table) in write order.
Real data: windows of the real risk_scores_validation.csv / risk_scores_train.csv written by the real pipeline
at HEAD (work/fz10_glue_real_out), cut to the columns the run reads (outputs asserted equal to the 51-column
run on the same lines).
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")

import fz10c_common as F  # noqa: E402  (pieces of fz_run_py_gen.py and t16_gen.py, copied: importing t16_gen runs it)
t16 = F
import b6_gen as b6  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

U = "run_py"
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
WORK = HERE.parent / "work"
REAL = WORK / "fz10_glue_real_out"
MODES = {0: "rows", 1: "rows", 2: "rows", 3: "rows", 4: "rows", 5: "rows", 6: "validation header only",
         7: "training scores text-null", 8: "stop: validation absent", 9: "stop: training absent"}


def mode(s: int) -> int:
    return kit.hsh(s, 7) % 10


def nv(s: int) -> int:
    if mode(s) == 6:
        return 0
    if kit.hsh(s, 8) % 5 == 0:
        return 10 + kit.hsh(s, 9) % 31
    return F.n_rows(s, 0)


def present(s: int) -> tuple[bool, bool]:
    m = mode(s)
    return (not (m == 8 or (m == 9 and kit.hsh(s, 10) % 2 == 0)), m != 9)


def tables(s: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    n, nt = nv(s), F.n_rows(s, 1)
    f = pl.Float64
    v = pl.DataFrame({"row_id": [float(i + 1) for i in range(n)], "default_flag": kit.gF(s + F.OV, n, 100, 0, F.EF),
                      "pd_logistic": kit.gF(s + F.OP, n, 100, 0, F.EP), "credit_risk_score": kit.gF(s + F.OS_, n, 100, 0, F.ES)},
                     schema={"row_id": f, "default_flag": f, "pd_logistic": f, "credit_risk_score": f})
    if mode(s) == 7:
        t = pl.DataFrame({"row_id": [float(i + 1) for i in range(nt)], "credit_risk_score": [None] * nt},
                         schema={"row_id": f, "credit_risk_score": pl.String})
    else:
        t = pl.DataFrame({"row_id": [float(i + 1) for i in range(nt)], "credit_risk_score": kit.gF(s + F.OT, nt, 100, 0, F.ES)},
                         schema={"row_id": f, "credit_risk_score": f})
    return v, t


def held(imp: pl.DataFrame, want: pl.DataFrame) -> bool:
    if want.height == 0:
        return imp.height == 0
    if imp.columns != want.columns or imp.height != want.height:
        return False
    for c in want.columns:
        a, b = imp.get_column(c), want.get_column(c)
        if a.dtype != b.dtype:
            return False
        if b.dtype == pl.String:
            if a.null_count() != a.len():
                return False
        elif [None if x is None else cmp.fbits(x) for x in a.to_list()] != [None if x is None else cmp.fbits(x) for x in b.to_list()]:
            return False
    return True


def pyrun_text(vtext: str | None, ttext: str | None) -> dict:
    """the real mc.run on files with this text (None: the file is absent), with the recorders of fz_run_py_gen."""
    rec: dict = {"files": [], "best": {}, "raised": None, "fsum_ok": True, "today": None, "imports": {}}
    o_write, o_best, o_d8, o_fsum = sc.write_sas_csv, sc.sas_best, sc.sas_d8, math.fsum

    def w_best(x, width):
        r = o_best(x, width)
        if width == 8 and sys._getframe(1).f_code is mc._into_float.__code__:
            assert rec["best"].setdefault(t16.key(x), r) == r
        return r

    def w_fsum(xs):
        xs = list(xs)
        r = o_fsum(xs)
        if cmp.fbits(F.fs_mirror(xs)) != cmp.fbits(r):
            rec["fsum_ok"] = False
        return r

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is mc.run.__code__:
            rec["today"] = frame.f_locals.get("model_performance_metrics")

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        outd.mkdir()
        for nm, tx in (("risk_scores_validation.csv", vtext), ("risk_scores_train.csv", ttext)):
            if tx is not None:
                (ind / nm).write_text(tx)
                rec["imports"][nm] = sc.proc_import_csv(ind / nm, guessingrows=20)
        sc.write_sas_csv, sc.sas_best, sc.sas_d8, math.fsum = (lambda df, path, formats=None: rec["files"].append((Path(path).name, df))), w_best, F.d8_standin, w_fsum
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mc.run(ind, outd)
        except Exception as e:  # noqa: BLE001
            rec["raised"] = f"{type(e).__name__}: {str(e)[:120]}"
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.sas_best, sc.sas_d8, math.fsum = o_write, o_best, o_d8, o_fsum
    return rec


def csv_v(df: pl.DataFrame) -> str:
    return F.csv(df) if df.height else ",".join(df.columns) + "\n"


def csv_t(df: pl.DataFrame) -> str:
    if df.schema["credit_risk_score"] == pl.String:
        return "row_id,credit_risk_score\n" + "".join(f"{int(r)},\n" for r in df.get_column("row_id").to_list())
    return F.csv(df)


EMPTY = cmp.digest(cmp.tokens(cmp.canon_table(pl.DataFrame())))


def pyrun(s: int) -> dict:
    v, t = tables(s)
    pv, pt = present(s)
    rec = pyrun_text(csv_v(v) if pv else None, csv_t(t) if pt else None)
    rec["held"] = ((not pv or held(rec["imports"]["risk_scores_validation.csv"], v))
                   and (not pt or held(rec["imports"]["risk_scores_train.csv"], t)))
    rec["v"], rec["t"], rec["pv"], rec["pt"] = v, t, pv, pt
    rec["stop"] = not (pv and pt)
    return rec


def expected(rec: dict) -> list[int]:
    dv = t16.dgt_in(rec["imports"]["risk_scores_validation.csv"]) if rec["pv"] else EMPTY
    dt_ = t16.dgt_in(rec["imports"]["risk_scores_train.csv"]) if rec["pt"] else EMPTY
    if rec["stop"]:
        assert rec["raised"] is not None and rec["raised"].startswith("ValueError") and not rec["files"], rec["raised"]
        return [dv, dt_, -1]
    return [dv, dt_, len(rec["files"])] + [b6.dgt(n, df) for n, df in rec["files"]]


RUN2 = ("let files := fun (r : Option (List (String × Tabular.Table Float))) => (match r with | none => [(-1 : Int)] "
        "| some fs => (fs.length : Int) :: fs.map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)) : List Int); "
        "let RUN2 := fun (V T : Option (Tabular.Table Float)) => [dg (tA (V.getD [])), dg (tA (T.getD []))] ++ files (run_py sb pf d8 today FS V T); ")

LETS_GEN = (
    "let cellO := fun (o : Option Float) => (Tabular.Cell.num o : Tabular.Cell Float); "
    f"let EF : List (Option Float) := {lt.lean_opt_floats(F.EF)}; let EP : List (Option Float) := {lt.lean_opt_floats(F.EP)}; "
    f"let ES : List (Option Float) := {lt.lean_opt_floats(F.ES)}; "
    "let md := fun (s : Nat) => ((hsh s 7) % 10).toNat; "
    "let nr := fun (s j : Nat) => 1 + ((hsh s (1000 + j)) % 9).toNat; "
    "let nv := fun (s : Nat) => (if md s == 6 then 0 else if (hsh s 8) % 5 == 0 then 10 + ((hsh s 9) % 31).toNat else nr s 0); "
    "let rid := fun (i : Nat) => (\"row_id\", cellO (some (Float.ofNat (i + 1)))); "
    "let V := fun (s : Nat) => (let n := nv s; ((List.range n).zip ((gF s n 100 0 EF).zip ((gF (s + 100000) n 100 0 EP).zip (gF (s + 200000) n 100 0 ES)))).map "
    "(fun (q : Nat × Option Float × Option Float × Option Float) => [rid q.1, (\"default_flag\", cellO q.2.1), (\"pd_logistic\", cellO q.2.2.1), (\"credit_risk_score\", cellO q.2.2.2)]) : Tabular.Table Float); "
    "let T := fun (s : Nat) => (let n := nr s 1; if md s == 7 then ((List.range n).map (fun (i : Nat) => [rid i, (\"credit_risk_score\", (Tabular.Cell.str none : Tabular.Cell Float))]) : Tabular.Table Float) "
    "else ((List.range n).zip (gF (s + 300000) n 100 0 ES)).map (fun (q : Nat × Option Float) => [rid q.1, (\"credit_risk_score\", cellO q.2)])); "
    "let OV := fun (s : Nat) => (if md s == 8 || (md s == 9 && (hsh s 10) % 2 == 0) then none else some (V s)); "
    "let OT := fun (s : Nat) => (if md s == 9 then none else some (T s)); "
    "let one := fun (s : Nat) => dg ((RUN2 (OV s) (OT s)).map (fun (i : Int) => i.toNat.toUInt64)); "
)


def lets_for(best: dict, today: str | None) -> str:
    sb, pf = b6.lean_tables(best, None).split("] [", 1)
    return (F.FS + f"let SB : List (Option UInt64 × String) := {sb}]; let PF : List (String × UInt64) := [{pf}; " + b6.SBPF + F.D8
            + f"let today : Tabular.Cell Float := Tabular.Cell.str (some {lt.lean_str(today or '2000-01-01')}); "
            + RUN2)


def u64(i: int) -> int:
    """Lean's (i : Int).toNat.toUInt64: -1 -> 0"""
    return max(i, 0) % (1 << 64)


def seeds_main(calls: int, per: int, base0: int) -> None:
    s = Suite("fz10c_run_py", generator="migration/port-to-lean/diffeval/units/fz10c_run_py_gen.py")
    stat = {"generated": 0, "kept": 0, "not_held": 0, "fsum": 0, "raised": [], "modes": {}, "stops": 0, "nvalid0": 0}
    today_all = None
    pending: list = []
    best: dict = {}  # one table for all calls: every input carries the same SB / PF (fewer distinct texts to send)
    for c in range(calls):
        base = base0 + c * per
        bad, cases = [], []
        for seed in range(base, base + per):
            stat["generated"] += 1
            r = pyrun(seed)
            if not r["held"]:
                stat["not_held"] += 1
                bad.append(seed)
                continue
            if r["raised"] is not None and not r["stop"]:
                stat["raised"].append((seed, r["raised"]))
                bad.append(seed)
                continue
            if not r["fsum_ok"]:
                stat["fsum"] += 1
                bad.append(seed)
                continue
            for k, v in r["best"].items():
                assert best.setdefault(k, v) == v
            if r["today"] is not None and r["today"].height:
                t = r["today"].get_column("validation_date").to_list()[0].isoformat()
                assert today_all in (None, t)
                today_all = t
            ints = expected(r)
            m = MODES[mode(seed)]
            stat["modes"][m] = stat["modes"].get(m, 0) + 1
            stat["stops"] += r["stop"]
            cases.append((f"seed {seed} [{m}]: {r['v'].height} validation / {r['t'].height} training rows, "
                          f"{'stop' if r['stop'] else str(len(r['files'])) + ' files'}", U, cmp.digest([u64(i) for i in ints]), {"fz": "kept"}))
            stat["kept"] += 1
        pending.append((base, bad, cases))
    for base, bad, cases in pending:
        lets = lets_for(best, today_all) + LETS_GEN + f"let BAD : List Nat := {lt.lean_list([str(b) for b in bad])}; "
        body = f"(((List.range {per}).map (fun (i : Nat) => {base} + i)).filter (fun (s : Nat) => !(BAD.contains s))).map one"
        s.ints(lets, body, cases, gen=True, table=True)
    s.write()
    (WORK / "fz10c_run_py.stat.json").write_text(json.dumps(stat, default=str, indent=1))
    print(json.dumps({k: v for k, v in stat.items() if k != "raised"}), "raised", len(stat["raised"]), sorted({r for _, r in stat["raised"]})[:6])
    for g in json.loads((WORK / "fz10c_run_py.inputs.json").read_text()):
        print([len(x) for x in g["inputs"]])


# ------------------------------------------------------------------ real data windows
def head_window(p: Path, start: int, n: int, cols: list[str]) -> str:
    out = []
    with p.open() as fh:
        hdr = fh.readline().rstrip("\n").split(",")
        ix = [hdr.index(c) for c in cols]
        out.append(",".join(cols))
        for k, ln in enumerate(fh):
            if k < start:
                continue
            if k >= start + n:
                break
            cells = ln.rstrip("\n").split(",")
            assert len(cells) == len(hdr) and '"' not in ln
            out.append(",".join(cells[i] for i in ix))
    return "\n".join(out) + "\n"


def real_main() -> None:
    s = Suite("fz10c_run_py_real", generator="migration/port-to-lean/diffeval/units/fz10c_run_py_gen.py")
    vp, tp = REAL / "risk_scores_validation.csv", REAL / "risk_scores_train.csv"
    hv = vp.open().readline().rstrip("\n").split(",")
    ht = tp.open().readline().rstrip("\n").split(",")
    VC, TC = ["default_flag", "pd_logistic", "credit_risk_score"], ["credit_risk_score"]
    wins = [(0, 120, 0, 120), (22000, 120, 52000, 120), (44880, 120, 104880, 120)]  # start, middle, end of each file
    best, terms, cases, today = {}, [], [], None
    for i, (v0, vn, t0, tn) in enumerate(wins):
        vt, tt = head_window(vp, v0, vn, VC), head_window(tp, t0, tn, TC)
        r = pyrun_text(vt, tt)
        assert r["raised"] is None, r["raised"]
        rf = pyrun_text(head_window(vp, v0, vn, hv), head_window(tp, t0, tn, ht))  # all 51 columns
        assert [n for n, _ in r["files"]] == [n for n, _ in rf["files"]]
        for (n, x), (_, y) in zip(r["files"], rf["files"], strict=True):
            assert b6.dgt(n, x) == b6.dgt(n, y), n
        for k, v in r["best"].items():
            assert best.setdefault(k, v) == v
        today = r["today"].get_column("validation_date").to_list()[0].isoformat()
        iv, it = r["imports"]["risk_scores_validation.csv"], r["imports"]["risk_scores_train.csv"]
        terms.append(f"RUN2 (some {t16.table_term(iv)}) (some {t16.table_term(it)})")
        ints = [t16.dgt_in(iv), t16.dgt_in(it), len(r["files"])] + [b6.dgt(n, df) for n, df in r["files"]]
        names = ["input validation", "input training", "number of files"] + [n for n, _ in r["files"]]
        w = f"real window {i}: validation lines {v0 + 1}..{v0 + vn}, training lines {t0 + 1}..{t0 + tn}"
        cases += [(f"{w}: {n}", U, v, {"fz": "kept"}) for n, v in zip(names, ints, strict=True)]
    s.ints(lets_for(best, today) + t16.MK, "(" + " ++ ".join(terms) + ")", cases, table=True)
    s.write()
    for g in json.loads((WORK / "fz10c_run_py_real.inputs.json").read_text()):
        print([len(x) for x in g["inputs"]])


# ------------------------------------------------------------------ per-file decomposition of chosen seeds
def diag_main(seeds: list[int]) -> None:
    s = Suite("fz10c_run_py_diag", generator="migration/port-to-lean/diffeval/units/fz10c_run_py_gen.py")
    best, cases, today = {}, [], None
    for seed in seeds:
        r = pyrun(seed)
        for k, v in r["best"].items():
            assert best.setdefault(k, v) == v
        if r["today"] is not None and r["today"].height:
            today = r["today"].get_column("validation_date").to_list()[0].isoformat()
        ints = expected(r)
        names = ["input validation", "input training", "number of files"] + [n for n, _ in r["files"]]
        pdl = r["v"].get_column("pd_logistic").to_list()
        z = "both zeros in pd_logistic" if any(x == 0 and math.copysign(1, x) < 0 for x in pdl if x is not None) and any(
            x == 0 and math.copysign(1, x) > 0 for x in pdl if x is not None) else "not both zeros"
        cases += [(f"seed {seed} ({z}): {n}", U, v, {"fz": "rejected"}) for n, v in zip(names, ints, strict=True)]
    lets = lets_for(best, today) + LETS_GEN
    body = "(" + " ++ ".join(f"RUN2 (OV {x}) (OT {x})" for x in seeds) + ")"
    s.ints(lets, body, cases, gen=True, table=True)
    s.write()


# ------------------------------------------------------------------ signed-zero explanation of differing seeds
TAZ = ("let tXz := fun (c : Tabular.Cell Float) => (match c with | .num none => [1, 0] | .num (some x) => [1, 1, if x == 0 then 0 else x.toBits] "
       "| .str none => [2, 0] | .str (some s) => 2 :: 1 :: tS s : List UInt64); "
       "let tAz := fun (t : Tabular.Table Float) => t.length.toUInt64 :: t.flatMap (fun r => r.length.toUInt64 :: r.flatMap (fun p => tS p.1 ++ tXz p.2)); "
       "let filesZ := fun (r : Option (List (String × Tabular.Table Float))) => (match r with | none => [(-1 : Int)] "
       "| some fs => (fs.length : Int) :: fs.flatMap (fun (p : String × Tabular.Table Float) => [dg (tS p.1 ++ tA p.2), dg (tS p.1 ++ tAz p.2)]) : List Int); "
       "let RUNZ := fun (s : Nat) => filesZ (run_py sb pf d8 today FS (OV s) (OT s)); ")


def zero_norm(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns([pl.when(pl.col(c) == 0).then(pl.lit(0.0)).otherwise(pl.col(c)).alias(c)
                            for c in df.columns if df.schema[c] == pl.Float64])


def zdiag_main(seeds: list[int]) -> None:
    """per differing seed: number of files, then for each file (digest, digest with every zero cell read as +0.0)."""
    s = Suite("fz10c_run_py_zero", generator="migration/port-to-lean/diffeval/units/fz10c_run_py_gen.py")
    best, cases, today = {}, [], None
    for seed in seeds:
        r = pyrun(seed)
        for k, v in r["best"].items():
            assert best.setdefault(k, v) == v
        if r["today"] is not None and r["today"].height:
            today = r["today"].get_column("validation_date").to_list()[0].isoformat()
        cases.append((f"seed {seed}: number of files", U, len(r["files"]), {"fz": "rejected"}))
        for n, df in r["files"]:
            cases.append((f"seed {seed}: {n} (exact)", U, b6.dgt(n, df), {"fz": "rejected"}))
            cases.append((f"seed {seed}: {n} (zeros unsigned)", U, b6.dgt(n, zero_norm(df)), {"fz": "rejected"}))
    lets = lets_for(best, today) + LETS_GEN + TAZ
    body = f"({lt.lean_list([str(x) for x in seeds])}).flatMap RUNZ"
    s.ints(lets, body, cases, gen=True, table=True)
    s.write()


def tok_main(seed: int, names: list[str]) -> None:
    """the whole value of chosen files of one seed, decoded and compared with paths (tokens mode)."""
    s = Suite("fz10c_run_py_tok", generator="migration/port-to-lean/diffeval/units/fz10c_run_py_gen.py")
    r = pyrun(seed)
    today = r["today"].get_column("validation_date").to_list()[0].isoformat()
    files = dict(r["files"])
    lets = lets_for(r["best"], today) + LETS_GEN
    for n in names:
        term = f'tA ((((run_py sb pf d8 today FS (OV {seed}) (OT {seed})).getD []).lookup {lt.lean_str(n)}).getD [])'
        s.tokens(lets, f"seed {seed}: {n}", U, term, "table", b6.canon_table(files[n]), fz="rejected")
    s.write()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tok":
        tok_main(int(sys.argv[2]), sys.argv[3:])
    elif len(sys.argv) > 1 and sys.argv[1] == "zero":
        res = json.loads((WORK / "fz10c_run_py.result.json").read_text())
        zdiag_main([int(c["id"].split("seed ")[1].split()[0]) for c in res if c["status"] != "PASS"] if len(sys.argv) == 2
                   else [int(x) for x in sys.argv[2:]])
    elif len(sys.argv) > 1 and sys.argv[1] == "diag":
        diag_main([int(x) for x in sys.argv[2:]])
    elif len(sys.argv) > 1 and sys.argv[1] == "real":
        real_main()
    else:
        calls = int(sys.argv[1]) if len(sys.argv) > 1 else 4
        per = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        base0 = int(sys.argv[3]) if len(sys.argv) > 3 else 7_000_000
        seeds_main(calls, per, base0)
