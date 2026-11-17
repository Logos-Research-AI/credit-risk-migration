"""Fuzz of the update of 2026-11-17, port-translator-10 (not the author of these units):
  def:train_run_05_association      suite fz2_s05
  def:train_run_06_coefficients_odds suite fz2_s06 (kept) and fz2_s06_rej (rejected, Python returns)
  def:train_run_07_hl               suite fz2_s07
on def:zz_carrier_t of blueprint 5365851c-5549-44b7-9207-4bd4c422031d.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz2_s567_gen.py

Inputs are built inside Lean from the seed (kit.GEN hsh / gF) and mirrored here. Expected values:
the unit's own source lines of train.py (found by their first and last statement, asserted),
executed on the mirrored inputs with the module's globals. Out-of-scope parameters, the same on
both sides: the five formatters = the injective encoding of their arguments (as tc_gen.py);
chi2 = the function x / (df + 3) put in place of scipy's chi2.sf inside sas_compat.chi2_sf (the
unit must hold for any chi2; a computable one needs no table); pow2 = Python's own `** 2`: in
Lean x * x, except on the arguments where Python's `** 2` is not x * x (this machine's pow is one
unit in the last place off on about 0.13 % of arguments): those are given to Lean as a table of
(argument, Python's square), collected here from b / se of step 06 and from observed - expected
of every group of hl_table of step 07.
One case = the digest of the kept seeds of a block of 50; the kept (resp. rejected) seeds of a
block are given to Lean as a bit mask computed here, so Lean applies no filter of its own.

Steps 05 and 07, seed s: fit_scored = [pd_logistic, default_flag], n = [0,1,2,3,5,9,24,60][hsh(s,7777)%8]
rows. pd row i (u = hsh(s, i)): 30 % from the pool EP (null, 0, 1, 0.5 and its two neighbours, 0.25,
1e-300, the float below 1, 0.1, 0.9), else k/64 with k in 0..64 (ties). Wild seeds (second range)
use EPW instead: EP plus NaN, +-inf, -0.0, 2.0, -1.0. default_flag row i (u = hsh(s+77777, i)):
null 5 %, else 1.0 when (u >> 20) % 8 < hsh(s,7778) % 9 (so some seeds have one class), else 0.0.
final_effects = [[], ["x"], ["age", "monthly_income"]][hsh(s,7779) % 3].
Preconditions as Python functions: def:train_run_05_association_precond (distinct names, one
height, both columns present, numeric dtypes of equal length) holds of every generated frame
(pre05 returns True); def:train_run_07_hl_precond: the same, and every group's event sum finite,
integral and at most 2^52, and no overflow of a square: true by construction (outcomes 0 / 1, at
most 60 rows, tame pd); on wild seeds pre07 is taken as True too (the clauses do not read pd
except through finite squares; an infinite pd gives infinite expected counts whose squares are
not finite-argument). A seed on which Python raises is listed (inside the precondition).
Step 06, seed s: k = hsh(s,7780) % 4 + 1 names (Intercept, age, a 36-character name, debt_ratio);
beta = gF(s, k, 40, 3, EB); cov = k x k of |gF(s*8+r+500000, k, 40, 3, EC)|; final_index by
hsh(s,7781) % 3: all effects in order / reversed / without the first; intercept =
gF(s+900000, 1, 40, 3, EB)[0]. pre06 renders def:train_run_06_coefficients_odds_precond clause by
clause: for idx in [0] + final_index: not cov[idx][idx] < 0; sqrt(cov) != 0; b/se finite implies
its square finite; for idx != 0: exp(b), exp(b - Z975 se), exp(b + Z975 se) finite (OverflowError
counted as not finite); the length and index clauses hold by construction.
"""
from __future__ import annotations

import json
import math
import sys
import textwrap
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
import suite as suite_mod  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
CH = 50
NS = [0, 1, 2, 3, 5, 9, 24, 60]
inf, nan = float("inf"), float("nan")
EP = [None, 0.0, 1.0, 0.5, math.nextafter(0.5, 1), math.nextafter(0.5, 0), 0.25, 1e-300, math.nextafter(1.0, 0), 0.1, 0.9]
EPW = EP + [nan, inf, -inf, -0.0, 2.0, -1.0]
FEFF = [[], ["x"], ["age", "monthly_income"]]
NM = ["Intercept", "age", "a_name_longer_than_twenty_characters", "debt_ratio"]
EB = [0.0, -0.0, 1.0, -1.0, 1e-300, 5e-324, 700.0, -745.0, 709.0, 710.0, 0.1, -0.1, 1e300]
EC = [1.0, 4.0, 0.25, 1e-300, 1e300, 0.0, 5e-324, nan, inf]
U5, U6, U7 = "train_run_05_association", "train_run_06_coefficients_odds", "train_run_07_hl"


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


class Chi2:
    @staticmethod
    def sf(x, df):
        return float(x) / (float(df) + 3.0)


SRC = Path(train.__file__).read_text().splitlines()


def find(text: str, after: int = 0) -> int:
    hits = [i for i, ln in enumerate(SRC) if text in ln and i >= after]
    assert hits, text
    return hits[0]


def slice_code(first: str, last: str, extra: int = 0):
    a = find(first)
    b = find(last, a) + extra
    return compile(textwrap.dedent("\n".join(SRC[a:b + 1])), f"train.py:{a + 1}-{b + 1}", "exec"), (a + 1, b + 1)


C05, R05 = slice_code("assoc = sas_compat.association_table(", 'output_dir / "printed_association.csv"')
C06, R06 = slice_code('mc_variable: list[str] = ["Intercept"]', 'output_dir / "printed_odds_ratios.csv"')
C07, R07 = slice_code("hl_table, hl_chisq, hl_df, hl_p = sas_compat.hosmer_lemeshow(", '"printed_hosmer_lemeshow.csv"', 1)


def run(code, env: dict):
    """-> (writes, namespace); the port's lines under the encoders, the synthetic chi2 and a recorder."""
    writes: list = []
    saved = {k: getattr(sc, k) for k in (*ENCODERS, "write_sas_csv", "chi2")}
    try:
        for k, f in ENCODERS.items():
            setattr(sc, k, f)
        sc.chi2 = Chi2
        sc.write_sas_csv = lambda df, path, formats=None: writes.append((Path(path).name, df.clone()))
        ns = dict(vars(train))
        ns.update(env, output_dir=Path("out"))
        exec(code, ns)  # noqa: S102  the port's own lines
    finally:
        for k, f in saved.items():
            setattr(sc, k, f)
    return writes, ns


XP: dict[int, int] = {}  # arguments on which Python's `** 2` is not x * x -> Python's square (bits)


def note_pow(x: float) -> None:
    if x != x or math.isinf(x):
        return
    try:
        v = x ** 2
    except OverflowError:
        return
    if fb(v) != fb(x * x):
        XP[fb(x)] = fb(v)


def lean_pow2() -> str:
    return (f"let XT : List (UInt64 × UInt64) := [{', '.join(f'({a}, {b})' for a, b in sorted(XP.items()))}]; "
            "let pow2 := fun (x : Float) => (match XT.find? (fun (t : UInt64 × UInt64) => t.1 == x.toBits) with | some t => Float.ofBits t.2 | none => x * x : Float); ")


def ftoks(files) -> list[int]:
    out = [len(files)]
    for n, d in files:
        out += cmp.tok_str(n) + cmp.tokens(cmp.canon_table(d))
    return out


# ------------------------------------------------------------------ inputs of 05 / 07
def fs_frame(s: int, wild: bool) -> pl.DataFrame:
    n = NS[kit.hsh(s, 7777) % 8]
    P = EPW if wild else EP
    pd, y = [], []
    q = kit.hsh(s, 7778) % 9
    for i in range(n):
        u = kit.hsh(s, i)
        pd.append(P[(u >> 20) % len(P)] if (u >> 8) % 100 < 30 else float((u >> 20) % 65) / 64.0)
        v = kit.hsh(s + 77777, i)
        y.append(None if (v >> 8) % 100 < 5 else (1.0 if (v >> 20) % 8 < q else 0.0))
    return pl.DataFrame({"pd_logistic": pl.Series(pd, dtype=pl.Float64), "default_flag": pl.Series(y, dtype=pl.Float64)})


def feff_of(s: int) -> list[str]:
    return FEFF[kit.hsh(s, 7779) % 3]


def d05(s: int, wild: bool):
    try:
        w, _ = run(C05, {"fit_scored": fs_frame(s, wild), "final_effects": feff_of(s)})
    except Exception as e:  # noqa: BLE001
        return "defect", f"{type(e).__name__}: {str(e)[:60]}"
    return "kept", cmp.digest(ftoks(w))


def d07(s: int, wild: bool):
    try:
        w, ns = run(C07, {"fit_scored": fs_frame(s, wild), "final_effects": feff_of(s)})
    except Exception as e:  # noqa: BLE001
        return "defect", f"{type(e).__name__}: {str(e)[:60]}"
    h = ns["hl_table"]
    for o1, e1, o0, e0 in zip(*(h.get_column(c).to_list() for c in ("EventsObserved", "EventsExpected", "NoneventsObserved", "NoneventsExpected")), strict=True):
        note_pow(o1 - e1)
        note_pow(o0 - e0)
    return "kept", cmp.digest(ftoks(w))


# ------------------------------------------------------------------ inputs of 06
def in06(s: int):
    k = kit.hsh(s, 7780) % 4 + 1
    beta = kit.gF(s, k, 40, 3, EB)
    cov = [[abs(v) for v in kit.gF(s * 8 + r + 500000, k, 40, 3, EC)] for r in range(k)]
    mode = kit.hsh(s, 7781) % 3
    idxs = list(range(1, k))
    if mode == 1:
        idxs = idxs[::-1]
    elif mode == 2:
        idxs = idxs[1:]
    icpt = kit.gF(s + 900000, 1, 40, 3, EB)[0]
    return k, beta, cov, idxs, icpt


def finite_exp(a: float) -> bool:
    try:
        return math.isfinite(math.exp(a))
    except OverflowError:
        return False


def pre06(beta, cov, idxs) -> bool:
    for idx in [0, *idxs]:
        b, cv = beta[idx], cov[idx][idx]
        if cv < 0.0:
            return False
        se = math.sqrt(cv)
        if se == 0.0:
            return False
        if math.isfinite(b / se) and not math.isfinite((b / se) * (b / se)):
            return False
        if idx != 0 and not (finite_exp(b) and finite_exp(b - sc.Z975 * se) and finite_exp(b + sc.Z975 * se)):
            return False
    return True


def d06(s: int):
    k, beta, cov, idxs, icpt = in06(s)
    ok = pre06(beta, cov, idxs)
    fin = sc.LogisticFit(NM[:k], np.array(beta, dtype=np.float64), np.array(cov, dtype=np.float64).reshape(k, k), 0.0, 1, True)
    try:
        w, ns = run(C06, {"final": fin, "final_effects": [NM[i] for i in idxs], "final_index": idxs, "intercept": icpt})
    except Exception as e:  # noqa: BLE001
        return ("defect" if ok else "drop"), f"{type(e).__name__}: {str(e)[:60]}"
    for idx in [0, *idxs]:
        note_pow(beta[idx] / math.sqrt(cov[idx][idx]))
    toks = cmp.tokens(cmp.canon_frame(ns["model_coefficients"])) + ftoks(w)
    return ("kept" if ok else "rejected"), cmp.digest(toks)


# ------------------------------------------------------------------ Lean side
def bl(xs) -> str:
    return "[" + ", ".join(str(fb(x)) for x in xs) + "]"


def opt_pool(name: str, P: list) -> str:
    vals = [x for x in P if x is not None]
    pre = "[none] ++ " if P[0] is None else ""
    assert all(x is not None for x in P[1:])
    return (f"let {name} : List (Option Float) := {pre}({bl(vals)} : List UInt64).map (fun (b : UInt64) => some (Float.ofBits b)); ")


FMT = ('let en := fun (x : Option Float) => (match x with | none => "N" | some v => toString v.toBits.toNat : String); '
       'let fw := fun (x : Option Float) (a b : Int) => "w" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
       'let fo := fun (x : Option Float) (a b : Int) => "o" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
       'let d8 := fun (x : Option Float) => "e" ++ en x; let d12 := fun (x : Option Float) => "t" ++ en x; '
       'let pv := fun (x : Option Float) => "p" ++ en x; '
       "let chi2 := fun (x : Float) (d : Int) => x / (Float.ofInt d + 3.0); "
       "let FT := fun (fs : List (String × Tabular.Table Float)) => fs.length.toUInt64 :: fs.flatMap (fun (f : String × Tabular.Table Float) => tS f.1 ++ tA f.2); ")
LCH = (f"let ch := fun (U : Nat → List UInt64) (M : List Nat) (b c : Nat) => dg (((List.range {CH}).filter (fun (i : Nat) => "
       f"(M.getD c 0 >>> i) % 2 == 1)).map (fun (i : Nat) => (dg (U (b + c * {CH} + i))).toNat.toUInt64)); ")


def l57(wild: bool) -> str:
    return (opt_pool("EP", EPW if wild else EP)
            + "let nOf := fun (s : Nat) => ([0, 1, 2, 3, 5, 9, 24, 60] : List Nat).getD ((hsh s 7777) % 8).toNat 0; "
            "let FS := fun (s : Nat) => (let n := nOf s; let q := (hsh s 7778) % 9; let f : Pl.Frame Float := [(\"pd_logistic\", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => "
            "let u := hsh s i; if (u >>> 8) % 100 < 30 then EP.getD ((u >>> 20) % EP.length.toUInt64).toNat none else some (Float.ofNat ((u >>> 20) % 65).toNat / 64.0)))), "
            "(\"default_flag\", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => let v := hsh (s + 77777) i; if (v >>> 8) % 100 < 5 then none else "
            "some (if (v >>> 20) % 8 < q then 1.0 else 0.0))))]; f); "
            'let FE := fun (s : Nat) => ([[], ["x"], ["age", "monthly_income"]] : List (List String)).getD ((hsh s 7779) % 3).toNat []; ')


L06 = (opt_pool("EB", EB) + opt_pool("EC", EC)
       + "let NM : List String := [" + ", ".join(lt.lean_str(x) for x in NM) + "]; "
       "let U6 := fun (s : Nat) => (let k := ((hsh s 7780) % 4).toNat + 1; "
       "let beta := (gF s k 40 3 EB).map (fun (o : Option Float) => o.getD 0.0); "
       "let cov := (List.range k).map (fun (r : Nat) => (gF (s * 8 + r + 500000) k 40 3 EC).map (fun (o : Option Float) => (o.getD 1.0).abs)); "
       "let mode := (hsh s 7781) % 3; let i0 := (List.range k).drop 1; "
       "let idxs := if mode == 1 then i0.reverse else if mode == 2 then i0.drop 1 else i0; "
       "let icpt := ((gF (s + 900000) 1 40 3 EB).headD none).getD 0.0; "
       "let fin : LogisticFit Float := { names := NM.take k, beta := Np.NDArray.d1 beta, cov := Np.NDArray.d2 cov, loglik := 0.0, n_iter := 1, converged := true }; "
       "let r := train_run_06_coefficients_odds (α := Float) fw fo d8 pv chi2 pow2 fin (idxs.map (fun (i : Nat) => NM.getD i \"\")) (idxs.map (fun (i : Nat) => (i : Int))) icpt; "
       "tR r.1 ++ FT r.2); ")


def blocks(per_seed, base: int, chunks: int):
    """-> per class: masks and digests per block; counts; the seeds of the defects."""
    XP.clear()
    out = {"kept": ([], []), "rejected": ([], [])}
    n = {"kept": 0, "rejected": 0, "drop": 0, "defect": 0}
    defects = []
    for c in range(chunks):
        m = {"kept": 0, "rejected": 0}
        ds = {"kept": [], "rejected": []}
        for i in range(CH):
            s = base + c * CH + i
            cls, d = per_seed(s)
            n[cls] += 1
            if cls in m:
                m[cls] |= 1 << i
                ds[cls].append(d)
            elif cls == "defect":
                defects.append((s, d))
        for k_ in m:
            out[k_][0].append(m[k_])
            out[k_][1].append((len(ds[k_]), cmp.digest(ds[k_])))
    return out, n, defects


def add(st: Suite, unit: str, what: str, lets: str, uterm: str, base: int, chunks: int, masks, digs, fz: str) -> None:
    cases = [(f"{what} seeds {base + c * CH}..{base + c * CH + CH - 1} ({k} inputs)", unit, d, {"fz": fz, "covers": k})
             for c, (k, d) in enumerate(digs)]
    st.ints(FMT + lean_pow2() + lets + LCH + f"let M : List Nat := {masks}; ", f"((List.range {chunks}).map (ch ({uterm}) M {base}))", cases, gen=True, table=True)


def fuzz_json(suite: str, unit: str, body: dict, tag: str = "") -> None:
    (suite_mod.WORK / f"{suite}.fuzz.json").write_text(json.dumps(
        {"fuzzer": "port-translator-10", "generator": "diffeval/units/fz2_s567_gen.py" + tag, "blueprint": BLUEPRINT, "units": {unit: body}}, indent=1))


def main() -> None:
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")
    print("source ranges", R05, R06, R07)
    T5 = "fun (s : Nat) => FT (train_run_05_association (α := Float) fw d12 (FS s) (FE s))"
    T7 = "fun (s : Nat) => FT (train_run_07_hl (α := Float) fw pv chi2 pow2 (FS s) (FE s))"
    for suite, unit, term, fn, b0 in (("fz2_s05", U5, T5, d05, 100000), ("fz2_s07", U7, T7, d07, 200000)):
        st = Suite(suite)
        o1, n1, def1 = blocks(lambda s: fn(s, False), b0, 48)
        add(st, unit, "tame pd,", l57(False), term, b0, 48, o1["kept"][0], o1["kept"][1], "kept")
        print(suite, "tame pow2 exceptions", len(XP))
        o2, n2, def2 = blocks(lambda s: fn(s, True), b0 + 50000, 12)
        add(st, unit, "wild pd (NaN, +-inf, -0.0, 2.0, -1.0 in the pool),", l57(True), term, b0 + 50000, 12, o2["kept"][0], o2["kept"][1], "kept")
        st.write()
        fuzz_json(suite, unit, {
            "seeds": f"{b0}..{b0 + 2399} (tame pd), {b0 + 50000}..{b0 + 50599} (wild pd)", "generated": 3000, "kept": n1["kept"] + n2["kept"],
            "python_raises_inside_precondition": [s for s, _ in def1 + def2],
            "note": "fit_scored of 0-60 rows built in Lean from the seed: pd k/64 with ties, 30 % from null, 0, 1, 0.5 and neighbours, 0.25, 1e-300, "
                    "the float below 1 (wild seeds: also NaN, +-inf, -0.0, 2.0, -1.0); default_flag 0/1 with 5 % null, class share by seed "
                    "(one-class seeds included); final_effects [], [x] or two names; chi2 = x/(df+3) on both sides, formatters = encodings; "
                    "pow2 on the Lean side = x * x plus a table of the arguments where Python's ** 2 differs (0 to 21 entries per input); one case = digest of the kept seeds of a block of 50"})
        print(suite, "tame", n1, "wild", n2, "defects", (def1 + def2)[:6])
    o, n, defs = blocks(d06, 300000, 68)
    st = Suite("fz2_s06")
    add(st, U6, "final / final_index / intercept of", L06, "U6", 300000, 68, o["kept"][0], o["kept"][1], "kept")
    st.write()
    body = {"seeds": "300000..303399", "generated": 3400, "kept": n["kept"], "python_raises_inside_precondition": [s for s, _ in defs],
            "note": f"final model of 1-4 names built in Lean from the seed: beta and |cov| from gF with pools (0, -0, +-1, 1e-300, 5e-324, 700, -745, 709, 710, "
                    f"1e300 / 1, 4, 0.25, 1e-300, 1e300, 0, 5e-324, NaN, inf); final_index in order, reversed or without the first effect; of 3400: "
                    f"{n['kept']} kept, {n['rejected']} rejected with Python returning (suite fz2_s06_rej), {n['drop']} rejected with Python raising; "
                    "chi2 = x/(df+3), formatters = encodings; pow2 on the Lean side = x * x plus a table of the arguments where Python's ** 2 differs (7 entries)"}
    LIM = ("the last bit of exp (RULEBOOK section 6): 4 of 68 blocks differ, traced by a per-seed evaluation (work/fz2_dbg06*.py) to seeds 300006, "
           "301212, 301515, 303397; in each the token lists differ only in odds-ratio cells of printed_odds_ratios.csv (1, 1, 3 equal cells, 1), "
           "whose float bits differ by exactly 1 between the Lean evaluator's Float.exp and numpy's exp; every other token equal")
    fuzz_json("fz2_s06", U6, {**body, "all_differences_are_recorded_limit": LIM})
    sr = Suite("fz2_s06_rej")
    add(sr, U6, "rejected by the precondition, Python returns,", L06, "U6", 300000, 68, o["rejected"][0], o["rejected"][1], "rejected")
    sr.write()
    fuzz_json("fz2_s06_rej", U6, {**body, "kept": 0, "note": body["note"] + "; THIS ROW: the rejected class only (249 inputs the precondition rejects and "
               "Python returns on); 1 of its 68 blocks differs (seed 300445, one odds-ratio cell, last bit of exp), so its 5 inputs are not counted as narrowings"},
              tag=" (rejected class)")
    print("fz2_s06", n, "defects", defs[:6], "pow2 exceptions", len(XP))
    for s_ in ("fz2_s05", "fz2_s07", "fz2_s06", "fz2_s06_rej"):
        for i, x in enumerate(json.loads((suite_mod.WORK / f"{s_}.inputs.json").read_text())[0]["inputs"]):
            print(s_, i, len(x), "chars")


main()
