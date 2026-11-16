"""T3 (update 2026-11-16): def:fe_run_01_clean against real runs of feature_engineering.run.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t3_gen.py
      -> diffeval/work/t3_clean.json, .inputs.json (carrier def:zz_carrier_f / zz_carrier_f)

Python side: the REAL feature_engineering.run on a data directory; a profile hook copies the
locals of `run` when it returns or raises: `credit_raw` (after the input check) and
`credit_raw_clean` are the input and the expected result of the step. Nothing of `run` is copied.
Scenarios: slices (header + chosen data lines, verbatim) of legacy/data/cs-training.csv and of the
judge scenarios the plan names, plus hand-made files / frames for the BEST12 branch.
Lean side: the frame is built from short codes (first case: its digest equals Python's credit_raw);
`sas_best12` and `input_best32` are lookup tables made from the real sas_compat functions on the
values of the scenario (a value absent from a table gives a marker that cannot match).
"""
from __future__ import annotations
import contextlib, io, sys, tempfile
from decimal import Decimal
from pathlib import Path
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402
from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

ROOT = HERE.parents[3]
SPLIT = HERE.parents[1] / "inputs" / "split_ids.csv"
nan, inf = float("nan"), float("inf")


def pyrun(*, csv_text=None, frame=None):
    rec = {}
    o_import = sc.proc_import_csv

    def prof(fr, event, arg):
        if event in ("return", "exception") and fr.f_code is fe.run.__code__:
            rec["locals"] = dict(fr.f_locals)

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        if csv_text is not None:
            (ind / "cs-training.csv").write_text(csv_text)
        else:
            sc.proc_import_csv = lambda path, guessingrows=20: frame
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ind, outd, split_ids=SPLIT)
        except Exception as e:  # noqa: BLE001
            rec["exc"] = repr(e)
        finally:
            sys.setprofile(None)
            sc.proc_import_csv = o_import
    return rec


def num_code(v):
    if v != v or v in (inf, -inf) or v < 0 or (v == 0 and cmp.fbits(v) != 0):
        return None
    sign, digits, exp = Decimal(repr(v)).as_tuple()
    m = int("".join(map(str, digits)))
    if exp > 0:
        m, exp = m * 10 ** exp, 0
    e = -exp
    if e >= 32 or cmp.fbits(float(f"{m}e-{e}")) != cmp.fbits(v):
        return None
    return m * 32 + e + 1


def lean_optf(v):
    if v is None:
        return "none"
    c = num_code(v)
    return f"(d {c})" if c is not None else f"(some {lt.lean_float(v)})"


PRE = ("let d := fun (c : Nat) => (some (Float.ofScientific ((c - 1) / 32) true ((c - 1) % 32)) : Option Float); "
       "let F := fun (L : List Nat) => (Pl.Col.f64 (L.map (fun (c : Nat) => if c = 0 then none else d c)) : Pl.Col Float); "
       "let mkB := fun (T : List (UInt64 × String)) => (fun (o : Option Float) => (match o with | some x => (T.lookup x.toBits).getD \"?MISSING\" | none => \"?NONE\")); "
       "let mkI := fun (T : List (String × Option Float)) => (fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
       "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | some s => (match T.lookup s with | some r => r | none => some (-987654321.0)) | none => none))) "
       "| _ => Pl.Col.int []) } : Pl.Expr Float)); ")


def lean_frame(name, df):
    cols = []
    for n in df.columns:
        s = df.get_column(n)
        if s.dtype == pl.String:
            body = "Pl.Col.str [" + ", ".join("none" if v is None else f"some {lt.lean_str(v)}" for v in s.to_list()) + "]"
        else:
            assert s.dtype == pl.Float64, (n, s.dtype)
            vals = s.to_list()
            codes = [0 if v is None else num_code(v) for v in vals]
            if all(c is not None for c in codes):
                body = "F [" + ", ".join(map(str, codes)) + "]"
            else:
                body = "Pl.Col.f64 [" + ", ".join(lean_optf(v) for v in vals) + "]"
        cols.append(f"({lt.lean_str(n)}, {body})")
    return f"let {name} : Pl.Frame Float := [" + ", ".join(cols) + "]; "


def tables(raw):
    """lookup tables of the two parameters, from the real functions, for this frame"""
    b12, texts = {}, set()
    for n in ("MonthlyIncome", "NumberOfDependents"):
        s = raw.get_column(n)
        if s.dtype == pl.String:
            texts.update(v for v in s.to_list() if v is not None)
        else:
            for v in s.to_list():
                if v is not None:
                    t = sc.sas_best12(v)
                    b12[cmp.fbits(v)] = t
                    texts.add(t)
    texts = sorted(texts)
    vals = pl.DataFrame({"t": texts}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
    B = "[" + ", ".join(f"({k}, {lt.lean_str(t)})" for k, t in b12.items()) + "]"
    I = "[" + ", ".join(f"({lt.lean_str(t)}, {lean_optf(v)})" for t, v in zip(texts, vals, strict=True)) + "]"
    return B, I, b12, dict(zip(texts, vals, strict=True))


def dgf(df):
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def slice_csv(path, rows):
    lines = Path(path).read_text().splitlines()
    return "\n".join([lines[0]] + [lines[i] for i in rows]) + "\n"


def pick(path, pred, k):
    """1-based data line numbers of the first k lines whose (MonthlyIncome, NumberOfDependents) satisfy pred"""
    out = []
    for i, ln in enumerate(Path(path).read_text().splitlines()[1:], start=1):
        f = ln.split(",")
        if pred(f[6], f[11]):
            out.append(i)
            if len(out) == k:
                break
    return out


REAL = ROOT / "legacy/data/cs-training.csv"
SC = ROOT / "judge/scenarios"
HDR = Path(REAL).read_text().splitlines()[0]
row = lambda i, inc, dep: f"{i},0,0.5,45,0,0.3,{inc},5,0,1,0,{dep}"  # noqa: E731
scen = [
    ("real_head", dict(csv_text=slice_csv(REAL, range(1, 11))), "legacy/data/cs-training.csv data lines 1-10, verbatim"),
    ("real_both_numeric", dict(csv_text=slice_csv(REAL, pick(REAL, lambda a, b: a != "NA" and b != "NA", 400)[380:388])),
     "legacy/data: 8 lines with no NA in either column: both columns imported Float64, BEST12 branch twice"),
    ("real_income_text", dict(csv_text=slice_csv(REAL, pick(REAL, lambda a, b: a == "NA" and b != "NA", 2) + pick(REAL, lambda a, b: a != "NA" and b != "NA", 300)[100:106])),
     "legacy/data: 8 lines with every NumberOfDependents stated, two of them with income NA: MonthlyIncome String, NumberOfDependents Float64"),
    ("real_na_rows", dict(csv_text=slice_csv(REAL, pick(REAL, lambda a, b: a == "NA", 5) + pick(REAL, lambda a, b: a != "NA", 3))),
     "legacy/data: 5 lines with income NA (some with dependents NA) and 3 with a known income"),
    ("q13_median_width", dict(csv_text=slice_csv(SC / "fix2/q13_median_width/cs-training.csv", range(1, 11))),
     "judge/scenarios/fix2/q13_median_width data lines 1-10"),
    ("train_age_exponent", dict(csv_text=slice_csv(SC / "fix_round5/train_age_exponent/cs-training.csv", range(26, 34))),
     "judge/scenarios/fix_round5/train_age_exponent data lines 26-33 (line 30 has age 4.5e1)"),
    ("hand_best12", dict(csv_text=HDR + "\n" + "\n".join(row(i + 1, a, b) for i, (a, b) in enumerate([
        ("1234567890123", "2"), ("0.1234567890123", "0"), ("123456.7890123", "1234567890123"), ("1e15", "3"),
        ("99999999999.96", "0"), ("0", "0"), ("0.000001234567891", "1"), ("5400", "12"), ("123456789012", "0"),
        ("1E20", "2")])) + "\n"),
     "hand-made file, both columns numeric: values that need more than 12 characters (BEST12 changes them)"),
    ("hand_frame_nan", dict(frame=None), "hand-made imported frame (the import replaced): Float64 MonthlyIncome with null, NaN, -0.0, inf"),
]
base = pl.read_csv(io.StringIO(slice_csv(REAL, pick(REAL, lambda a, b: a != "NA" and b != "NA", 6))), null_values="NA")
hf = sc.proc_import_csv.__call__  # noqa: B004
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "x.csv"
    p.write_text(slice_csv(REAL, pick(REAL, lambda a, b: a != "NA" and b != "NA", 6)))
    hand = sc.proc_import_csv(p, guessingrows=None)
hand = hand.with_columns(MonthlyIncome=pl.Series([None, nan, -0.0, inf, 1234567890123.0, 2500.0], dtype=pl.Float64),
                         NumberOfDependents=pl.Series([0.0, None, 2.0, 1.0, 0.0, 3.0], dtype=pl.Float64))
scen[-1][1]["frame"] = hand

s = Suite("t3_clean")
s.item, s.decl = "def:zz_carrier_f", "zz_carrier_f"
lets, body, cases, report = PRE, [], [], []
for k, (name, kw, note) in enumerate(scen):
    r = pyrun(**kw)
    L = r["locals"]
    raw = L["credit_raw"]
    kinds = (str(raw.schema["MonthlyIncome"]), str(raw.schema["NumberOfDependents"]))
    if "credit_raw_clean" not in L:
        report.append(f"{name}: run stopped before step 01 ({r.get('exc')}); no result to compare")
        continue
    exp = L["credit_raw_clean"]
    B, I, b12, ib = tables(raw)
    changed = sum(1 for kb, t in b12.items() if ib[t] is None or cmp.fbits(ib[t]) != kb)
    lets += lean_frame(f"f{k}", raw) + f"let r{k} := fe_run_01_clean (mkI {I}) (mkB {B}) f{k}; "
    body += [f"dg (tR f{k})", f"dg (tR r{k})"]
    cases += [(f"{name}/input", "fe_run_01_clean (input frame)", cmp.canon_frame(raw)),
              (f"{name}/credit_raw_clean", "fe_run_01_clean", cmp.canon_frame(exp))]
    report.append(f"{name}: rows={raw.height} kinds={kinds} exc={r.get('exc')} best12 values={len(b12)} changed by the round trip={changed}  [{note}]")
    if k in (3, 7):
        s.digest_body(lets, "[" + ", ".join(body) + "]", cases, gen=False, table=False)
        lets, body, cases = PRE, [], []
s.notes = {"fe_run_01_clean": "real feature_engineering.run on slices of legacy/data and of the named judge scenarios; "
           "sas_best12 / input_best32 = lookup tables from the real functions"}
s.write()
print("\n".join(report))
# the full runs the plan names: kinds of the two columns and whether step 01 was reached
for name, dd in [("legacy/data", ROOT / "legacy/data"), ("fix2/train_income_long", SC / "fix2/train_income_long"),
                 ("fix2/q13_median_width", SC / "fix2/q13_median_width"), ("fix_round5/train_age_exponent", SC / "fix_round5/train_age_exponent")]:
    r = pyrun(csv_text=(dd / "cs-training.csv").read_text())
    L = r["locals"]
    raw = L["credit_raw"]
    msg = f"FULL {name}: rows={raw.height} kinds=({raw.schema['MonthlyIncome']}, {raw.schema['NumberOfDependents']}) exc={r.get('exc')}"
    if "credit_raw_clean" in L:
        # the whole-file result against the step's formula with the REAL parameters is not a Lean evaluation; only recorded
        msg += f" credit_raw_clean rows={L['credit_raw_clean'].height}"
    print(msg)
