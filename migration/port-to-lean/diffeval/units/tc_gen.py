"""T-C of the update of 2026-11-17: def:train_run_05_association, def:train_run_06_coefficients_odds,
def:train_run_07_hl against the port as it stands (train.py:290-414; the four printed files are
written only `if final_effects:`).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/tc_gen.py
      -> diffeval/work/tc_train.json, tc_train.inputs.json
  eval_decl each input on def:zz_carrier_t (blueprint 5365851c-...); python3 diffeval/fuzz_collect.py 3 tc_train;
  python3 diffeval/compare.py diffeval/work/tc_train.json diffeval/work/tc_train.out.txt

Python side: the REAL train.run on feature files, under recorders: sas_compat.write_sas_csv records
(file name, frame) in call order and writes nothing; chi2_sf calls outside the stepwise fit are
recorded; the locals of train.run at its return give fit_scored, final, final_effects, final_index,
intercept, model_coefficients, hl_table. The five formatters are replaced on both sides by the same
injective encoding of their arguments (as in b9_gen.py: a cell is equal exactly when the formatter
received the same arguments); a second run with the real formatters is checked cell by cell
against the encoded one (the real formatter applied to the decoded arguments).

Scenarios (feature files built from the real feature-engineering run on legacy/data, cached in
work/tc_data):
  real       60 training rows / 25 validation rows of the real feature files (every 1250th / 1700th row)
  effects    another sample (90 / 30 rows; three variables enter, one name longer than 20 characters)
  icpt_only  a sample whose default_flag is set by row position, so that no variable enters: the
             final model has the intercept only and the four files are not written
Lean side, per scenario: each unit on the values the real run handed it (fit_scored restricted to
default_flag and pd_logistic; final; final_effects; final_index; intercept), then with final_effects
replaced by [] / by ["x"] (steps 05 and 07: the files must go / stay whatever the table).
Out-of-scope routines: chi2 = table of the recorded chi2_sf calls; pow2 = table of Python's x ** 2
on the arguments the two units pass ((o - e) of every group of hl_table; b / se of every index).
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import struct
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

REPO = HERE.parents[3]
DATA = HERE.parent / "work" / "tc_data"
ITEM, DECL = "def:zz_carrier_t", "zz_carrier_t"
SENT = struct.unpack("<Q", struct.pack("<d", -7.25))[0]
FOUR = ["printed_association.csv", "printed_odds_ratios.csv", "printed_hl_partition.csv", "printed_hosmer_lemeshow.csv"]


def fb(x) -> int:
    return cmp.fbits(float(x))


def enc(x) -> str:
    return "N" if x is None else str(fb(x))


ENCODERS = {
    "fmt_wd": lambda x, w_, d: f"w{enc(x)}/{w_}/{d}",
    "fmt_oddsr": lambda x, w_, d: f"o{enc(x)}/{w_}/{d}",
    "sas_d8": lambda x: f"e{enc(x)}",
    "sas_d12_3": lambda x: f"t{enc(x)}",
    "sas_pvalue": lambda x: f"p{enc(x)}",
}
REAL = {k: getattr(sc, k) for k in ENCODERS}


def decode_and_format(cell: str):
    import re
    m = re.match(r"^([woetp])(N|\d+)(?:/(-?\d+)/(-?\d+))?$", cell)
    if not m:
        return None
    x = None if m.group(2) == "N" else struct.unpack("<d", struct.pack("<Q", int(m.group(2))))[0]
    k = m.group(1)
    if k in "wo":
        return REAL["fmt_wd" if k == "w" else "fmt_oddsr"](x, int(m.group(3)), int(m.group(4)))
    return REAL[{"e": "sas_d8", "t": "sas_d12_3", "p": "sas_pvalue"}[k]](x)


# ---------------------------------------------------------------- feature files
def full_features() -> Path:
    full = DATA / "fe_out"
    if not (full / "model_features_train.csv").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            fe.run(REPO / "legacy" / "data", full, split_ids=HERE.parents[1] / "inputs" / "split_ids.csv")
    return full


def scenario_dir(name: str) -> Path:
    ind = DATA / name
    if (ind / "model_features_train.csv").exists():
        return ind
    full = full_features()
    ind.mkdir(parents=True, exist_ok=True)
    spec = {"real": ((60, 1250, 2), (25, 1700, 1)), "effects": ((90, 1000, 13), (30, 1200, 5)), "icpt_only": ((40, 2100, 11), (20, 1500, 3))}[name]
    for fname, (n, stride, off) in zip(("model_features_train.csv", "model_features_validation.csv"), spec, strict=True):
        d = sc.proc_import_csv(full / fname, guessingrows=None)[off::stride].head(n)
        assert d.height == n
        if name == "icpt_only" and "train" in fname:
            d = d.with_columns(default_flag=pl.Series([1.0 if i % 4 == 1 else 0.0 for i in range(n)]))
        d.write_csv(ind / fname)
    return ind


def real_run(ind: Path, encoded: bool) -> dict:
    rec: dict = {"writes": [], "chi2": [], "locals": None, "in_fit": False}
    o_write, o_step, o_chi2 = sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf

    def w_write(df, path, formats=None):
        rec["writes"].append((Path(path).name, df.clone()))

    def w_step(*a, **k):
        rec["in_fit"] = True
        try:
            return o_step(*a, **k)
        finally:
            rec["in_fit"] = False

    def w_chi2(x, df):
        r = o_chi2(x, df)
        if not rec["in_fit"]:
            rec["chi2"].append((float(x), int(df), float(r)))
        return r

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is train.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf = w_write, w_step, w_chi2
    if encoded:
        for k, f in ENCODERS.items():
            setattr(sc, k, f)
    try:
        with tempfile.TemporaryDirectory() as td, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sys.setprofile(prof)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    train.run(ind, Path(td))
                rec["raised"] = None
            except Exception as ex:  # noqa: BLE001
                rec["raised"] = f"{type(ex).__name__}: {ex}"
            finally:
                sys.setprofile(None)
    finally:
        sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf = o_write, o_step, o_chi2
        for k, f in REAL.items():
            setattr(sc, k, f)
    return rec



# ---------------------------------------------------------------- Lean side
def ul(xs) -> str:
    return "[" + ", ".join(str(fb(x)) for x in xs) + "]"


LETS = (
    "let FL := fun (v : List UInt64) => v.map Float.ofBits; "
    'let en := fun (x : Option Float) => (match x with | none => "N" | some v => toString v.toBits.toNat : String); '
    'let fw := fun (x : Option Float) (a b : Int) => "w" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
    'let fo := fun (x : Option Float) (a b : Int) => "o" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
    'let d8 := fun (x : Option Float) => "e" ++ en x; '
    'let d12 := fun (x : Option Float) => "t" ++ en x; '
    'let pv := fun (x : Option Float) => "p" ++ en x; '
    f"let T1 := fun (T : List (UInt64 × UInt64)) (x : Float) => (match T.find? (fun (t : UInt64 × UInt64) => t.1 == x.toBits) with "
    f"| some t => Float.ofBits t.2 | none => Float.ofBits {SENT} : Float); "
    f"let T2 := fun (T : List (UInt64 × Int × UInt64)) (x : Float) (d : Int) => (match T.find? (fun (t : UInt64 × Int × UInt64) => t.1 == x.toBits && t.2.1 == d) with "
    f"| some t => Float.ofBits t.2.2 | none => Float.ofBits {SENT} : Float); "
    "let mkfit := fun (names : List String) (beta : List UInt64) (cov : List (List UInt64)) (ll : UInt64) (ni : Int) (cv : Bool) => "
    "({ names := names, beta := Np.NDArray.d1 (FL beta), cov := Np.NDArray.d2 (cov.map FL), loglik := Float.ofBits ll, "
    "n_iter := ni, converged := cv } : LogisticFit Float); "
    "let fc := fun (v : List UInt64) => (Pl.Col.f64 (v.map (fun (b : UInt64) => some (Float.ofBits b))) : Pl.Col Float); "
    "let EF := fun (fs : List (String × Tabular.Table Float)) => (fs.length : Int) :: fs.map (fun (f : String × Tabular.Table Float) => dg (tS f.1 ++ tA f.2)); "
)


def ef(files: list[tuple[str, pl.DataFrame]]) -> list[int]:
    return [len(files)] + [cmp.digest(cmp.tok_str(n) + cmp.tokens(cmp.canon_table(d))) for n, d in files]


def build() -> Suite:
    st = Suite("tc_train")
    st.item, st.decl = ITEM, DECL
    for name in ("real", "effects", "icpt_only"):
        ind = scenario_dir(name)
        r, rr = real_run(ind, True), real_run(ind, False)
        assert r["raised"] is None and rr["raised"] is None, (name, r["raised"])
        L, LR = r["locals"], rr["locals"]
        W = dict(r["writes"])
        feff, fidx, fin, icpt, fsc, hl = L["final_effects"], L["final_index"], L["final"], L["intercept"], L["fit_scored"], L["hl_table"]
        # ---- the files of the four names are written exactly when final_effects is not empty
        assert [n for n in FOUR if n in W] == (FOUR if feff else []), (name, list(W))
        order = [n for n, _ in r["writes"]]
        # ---- the run with the real formatters is the encoded one, formatter applied
        cells = 0
        for a, b in [(dict(rr["writes"]).get(n), W.get(n)) for n in FOUR] + [(LR[k], L[k]) for k in ("model_coefficients", "printed_association", "printed_odds_ratios", "printed_hl_partition", "printed_hosmer_lemeshow")]:
            assert (a is None) == (b is None)
            if a is None:
                continue
            assert a.columns == b.columns and a.height == b.height
            for c in a.columns:
                for x, y in zip(a.get_column(c).to_list(), b.get_column(c).to_list(), strict=True):
                    f = decode_and_format(y)
                    assert x == (y if f is None else f), (name, c, x, y)
                    cells += f is not None
        # ---- routine tables
        chi2 = {(fb(x), d): fb(v) for x, d, v in r["chi2"]}
        pargs = []
        for idx in [0, *fidx]:
            pargs.append(float(fin.beta[idx]) / math.sqrt(float(fin.cov[idx, idx])))
        for o1, e1, o0, e0 in zip(*(hl.get_column(c).to_list() for c in ("EventsObserved", "EventsExpected", "NoneventsObserved", "NoneventsExpected")), strict=True):
            pargs += [o1 - e1, o0 - e0]
        pow2 = {fb(x): fb(x ** 2) for x in pargs}
        # ---- the inputs
        assert fsc.get_column("default_flag").null_count() == 0 and fsc.get_column("pd_logistic").null_count() == 0
        lets = (LETS
                + f"let chi2 := T2 [{', '.join(f'({a}, ({d}), {b})' for (a, d), b in chi2.items())}]; "
                + f"let pow2 := T1 [{', '.join(f'({a}, {b})' for a, b in pow2.items())}]; "
                + f"let FS : Pl.Frame Float := ["
                  f"(\"pd_logistic\", fc {ul(fsc.get_column('pd_logistic').to_list())}), (\"default_flag\", fc {ul(fsc.get_column('default_flag').to_list())})]; "
                + f"let fin := mkfit [{', '.join(lt.lean_str(n) for n in fin.names)}] {ul(fin.beta)} [{', '.join(ul(row) for row in np.atleast_2d(fin.cov))}] {fb(fin.loglik)} ({int(fin.n_iter)}) {'true' if fin.converged else 'false'}; "
                + f"let feff : List String := [{', '.join(lt.lean_str(n) for n in feff)}]; let fidx : List Int := {list(fidx)}; let icpt := Float.ofBits {fb(icpt)}; "
                + "let r6 := train_run_06_coefficients_odds (α := Float) fw fo d8 pv chi2 pow2 fin feff fidx icpt; ")
        body = ("EF (train_run_05_association (α := Float) fw d12 FS feff) ++ EF (train_run_05_association (α := Float) fw d12 FS []) ++ "
                "EF (train_run_05_association (α := Float) fw d12 FS [\"x\"]) ++ [dg (tR r6.1)] ++ EF r6.2 ++ "
                "EF (train_run_07_hl (α := Float) fw pv chi2 pow2 FS feff) ++ EF (train_run_07_hl (α := Float) fw pv chi2 pow2 FS []) ++ "
                "EF (train_run_07_hl (α := Float) fw pv chi2 pow2 FS [\"x\"])")
        u5, u6, u7 = "train_run_05_association", "train_run_06_coefficients_odds", "train_run_07_hl"
        cases: list[tuple] = []

        def add(unit: str, what: str, vals: list[int], labels: list[str]):
            for v, lab in zip(vals, labels, strict=True):
                cases.append((f"{name}: {what}: {lab}", unit, v))

        def flab(files):
            return ["number of files"] + [n for n, _ in files]

        f5 = [(n, W[n]) for n in FOUR[:1] if n in W]
        f5x = [(FOUR[0], L["printed_association"])]
        f6 = [(n, W[n]) for n in FOUR[1:2] if n in W]
        f7 = [(n, W[n]) for n in FOUR[2:] if n in W]
        f7x = [(FOUR[2], L["printed_hl_partition"]), (FOUR[3], L["printed_hosmer_lemeshow"])]
        add(u5, f"the run's final_effects {feff}", ef(f5), flab(f5))
        add(u5, "final_effects [] (no file)", [0], ["number of files"])
        add(u5, "final_effects [\"x\"] (the table Python computed, written)", ef(f5x), flab(f5x))
        add(u6, "model_coefficients", [cmp.digest(cmp.tokens(cmp.canon_frame(L["model_coefficients"])))], [f"{L['model_coefficients'].height} rows"])
        add(u6, f"the run's final_effects {feff}", ef(f6), flab(f6))
        add(u7, f"the run's final_effects {feff}", ef(f7), flab(f7))
        add(u7, "final_effects [] (no file)", [0], ["number of files"])
        add(u7, "final_effects [\"x\"] (the two tables Python computed, written)", ef(f7x), flab(f7x))
        st.ints(lets, body, cases, table=True)
        if f5 and f7:  # the order of the write_sas_csv calls
            assert [n for n in order if n in FOUR] == FOUR
        print(f"{name}: final_effects {feff}; files of the four: {[n for n in FOUR if n in W]}; fit_scored {fsc.height} rows; hl_table {hl.height} groups; "
              f"{cells} formatted cells checked against the real formatters; chi2 {len(chi2)}, pow2 {len(pow2)} entries")
    st.notes = {u: "T-C 2026-11-17: real train.run on three feature samples (model with effects x2, intercept-only final model); formatters as injective encodings, checked against the real ones"
                for u in ("train_run_05_association", "train_run_06_coefficients_odds", "train_run_07_hl")}
    return st


if __name__ == "__main__":
    st = build()
    st.write()
    for i, inp in enumerate(st.inputs):
        print(i, len(inp["text"]), "chars;", sum(1 for c in st.cases if c["input"] == i), "cases")
