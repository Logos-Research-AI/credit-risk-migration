"""Fuzz of def:train_run_05_association (revision 56453ad3...) and def:train_run_05_association_precond
(cf596de4...) by a non-author, carrier def:zz_carrier_t, blueprint 5365851c-5549-44b7-9207-4bd4c422031d.
Nothing is changed on the blueprint.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_s05_gen.py

Expected values: the REAL lines of train.py from `estimates = [] if final is None ...` to the write_sas_csv of
printed_association.csv (found by their text, asserted), executed on the mirrored inputs; the REAL
sas_compat.association_table runs. fmt_wd and sas_d12_3 (out-of-scope formatters) are the same injective encoding
of their arguments on both sides.

Case of seed s (built INSIDE Lean from hsh / gF, mirrored here):
  n rows = [0,1,2,3,4,5,8][hsh(s,1)%7]
  columns a, b, c: kit.gF(s*7+k+100, n, 25, 3, XE), XE = null, 0, -0, 1, -1, NaN, +-inf, 1e300, 5e-324, +-700, 0.5;
     c is an Int64 column when hsh(s,9)%10 == 0 (gI(s*7+105, n, 10, 7, 3))
  pd_logistic: 30 % from EP (null, 0, 1, 0.5 and neighbours, 0.25, 1e-300, 1 - ulp, 0.1, 0.9; wild seeds: + NaN, +-inf,
     -0.0, 2.0, -1.0), else k/64 (ties)
  default_flag: null 6 %, else 1 when (v>>20)%8 < hsh(s,7778)%9 (one-class seeds), Int64 when hsh(s,10)%10 == 0
  column order: default_flag, pd_logistic, a, b, c  or  a, b, c, pd_logistic, default_flag (hsh(s,11)%2)
  final: none when hsh(s,3)%10 == 0, else beta (d1) of 1 + hsh(s,4)%4 (+1 when hsh(s,5)%10 == 0) floats from
     gF(s+500, len, 35, 3, EB): EB = 0, -0, 1, -1, 0.5, 1e-300, 5e-324, +-700, 709, -745, 1e300, 0.1, NaN, +-inf
  final_effects: the first hsh(s,6)%4 of a rotation (hsh(s,12)%3), reversed or not (hsh(s,13)%2) of [a, b, c]; a
     repeat of the first at the end 1 in 20; "zz" (not a column) as the first 1 in 20; [] when final is none
  final_index j: min(j+1, len(beta)-1) 75 %, else (u>>20)%len(beta), u = hsh(s+900, j)
  left_out: final none: [0] 5 %, else []; else [] 50 %, [1] 35 %, [0, 2] 15 %  (hsh(s,16)%100)
Precondition (rendered as `pre`): distinct names, one height, beta 1-D, equal lengths, 0 <= i < len(estimates)
(all by construction); left_out non-empty -> every effect is a Float64 column of fit_scored and exp(-eta) finite for
every non-null eta (eta by polars on the frame; NaN eta, exp overflow: rejected); default_flag and pd_logistic exist
(construction); association_table_precond: numeric dtypes of equal length (construction).
One case = the digest of the kept seeds of a block of 50 (the kept seeds of a block are given as a bit mask).
"""
from __future__ import annotations

import json
import math
import sys
import textwrap
from collections import Counter
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
NS = [0, 1, 2, 3, 4, 5, 8]
inf, nan = float("inf"), float("nan")
H = kit.hsh
EP = [None, 0.0, 1.0, 0.5, math.nextafter(0.5, 1), math.nextafter(0.5, 0), 0.25, 1e-300, math.nextafter(1.0, 0), 0.1, 0.9]
EPW = EP + [nan, inf, -inf, -0.0, 2.0, -1.0]
XE = [None, 0.0, -0.0, 1.0, -1.0, nan, inf, -inf, 1e300, 5e-324, 700.0, -700.0, 0.5]
EB = [0.0, -0.0, 1.0, -1.0, 0.5, 1e-300, 5e-324, 700.0, -700.0, 709.0, -745.0, 1e300, 0.1, nan, inf, -inf]
BASE = ["a", "b", "c"]
UNIT = "train_run_05_association"


def fb(x) -> int:
    return cmp.fbits(float(x))


def enc(x) -> str:
    return "N" if x is None else str(fb(x))


ENCODERS = {
    "fmt_wd": lambda x, w_, d: f"w{enc(x)}/{w_}/{d}",
    "sas_d12_3": lambda x: f"t{enc(x)}",
}

SRC = Path(train.__file__).read_text().splitlines()


def find(text: str, after: int = 0) -> int:
    hits = [i for i, ln in enumerate(SRC) if text in ln and i >= after]
    assert hits, text
    return hits[0]


a_ = find("estimates = [] if final is None else [float(v) for v in final.beta]")
assert sum("estimates = [] if final is None" in ln for ln in SRC) == 1
b_ = find('output_dir / "printed_association.csv"', a_)
C05 = compile(textwrap.dedent("\n".join(SRC[a_:b_ + 1])), f"train.py:{a_ + 1}-{b_ + 1}", "exec")
R05 = (a_ + 1, b_ + 1)


def run(env: dict):
    writes: list = []
    saved = {k: getattr(sc, k) for k in (*ENCODERS, "write_sas_csv")}
    try:
        for k, f in ENCODERS.items():
            setattr(sc, k, f)
        sc.write_sas_csv = lambda df, path, formats=None: writes.append((Path(path).name, df.clone()))
        ns = dict(vars(train))
        ns.update(env, output_dir=Path("out"))
        exec(C05, ns)  # noqa: S102  the port's own lines
    finally:
        for k, f in saved.items():
            setattr(sc, k, f)
    return writes, ns


def ftoks(files) -> list[int]:
    out = [len(files)]
    for n, d in files:
        out += cmp.tok_str(n) + cmp.tokens(cmp.canon_table(d))
    return out


# ------------------------------------------------------------------ the case
def case(s: int, wild: bool):
    n = NS[H(s, 1) % 7]
    P = EPW if wild else EP
    q = H(s, 7778) % 9
    cols = {}
    for k, nm in enumerate(BASE):
        if nm == "c" and H(s, 9) % 10 == 0:
            cols[nm] = pl.Series(kit.gI(s * 7 + 105, n, 10, 7, 3), dtype=pl.Int64)
        else:
            cols[nm] = pl.Series(kit.gF(s * 7 + k + 100, n, 25, 3, XE), dtype=pl.Float64)
    pd, y = [], []
    for i in range(n):
        u = H(s, i)
        pd.append(P[(u >> 20) % len(P)] if (u >> 8) % 100 < 30 else float((u >> 20) % 65) / 64.0)
        v = H(s + 77777, i)
        flag = None if (v >> 8) % 100 < 6 else (1 if (v >> 20) % 8 < q else 0)
        y.append(flag if H(s, 10) % 10 == 0 else (None if flag is None else float(flag)))
    ycol = pl.Series(y, dtype=pl.Int64 if H(s, 10) % 10 == 0 else pl.Float64)
    pcol = pl.Series(pd, dtype=pl.Float64)
    if H(s, 11) % 2 == 0:
        df = pl.DataFrame({"default_flag": ycol, "pd_logistic": pcol, **cols})
    else:
        df = pl.DataFrame({**cols, "pd_logistic": pcol, "default_flag": ycol})
    fk = H(s, 3) % 10
    q1 = H(s, 4) % 4
    blen = q1 + 1 + (1 if H(s, 5) % 10 == 0 else 0)
    beta = kit.gF(s + 500, blen, 35, 3, EB)
    if fk == 0:
        final, effs, idx = None, [], []
    else:
        final = sc.LogisticFit(["Intercept", "a", "b", "c"][:q1 + 1], np.array(beta, dtype=np.float64), np.zeros((0, 0)), 0.0, 1, True)
        r = H(s, 12) % 3
        rot = BASE[r:] + BASE[:r]
        rot2 = rot[::-1] if H(s, 13) % 2 == 0 else rot
        effs = rot2[:H(s, 6) % 4]
        if H(s, 14) % 20 == 0 and effs:
            effs = effs + [rot2[0]]
        if H(s, 15) % 20 == 0 and effs:
            effs = ["zz"] + effs[1:]
        idx = []
        for j in range(len(effs)):
            u = H(s + 900, j)
            idx.append(min(j + 1, blen - 1) if (u >> 8) % 100 < 75 else (u >> 20) % blen)
    lk = H(s, 16) % 100
    if fk == 0:
        lo = [0] if lk < 5 else []
    else:
        lo = [] if lk < 50 else [1] if lk < 85 else [0, 2]
    return dict(n=n, df=df, final=final, effs=effs, idx=idx, lo=lo, beta=beta, fk=fk)


def pre(c, ns) -> bool:
    df, lo = c["df"], c["lo"]
    if lo:
        for e in c["effs"]:
            if e not in df.columns or df.schema[e] != pl.Float64:
                return False
        eta = df.with_columns(__e=ns["eta_iteration"]).get_column("__e").to_list()
        for v in eta:
            if v is None:
                continue
            try:
                if not math.isfinite(math.exp(-v)):
                    return False
            except OverflowError:
                return False
    return True


def d05(s: int, wild: bool):
    c = case(s, wild)
    env = {"final": c["final"], "final_effects": c["effs"], "final_index": c["idx"], "left_out": c["lo"], "fit_scored": c["df"]}
    try:
        w, ns = run(env)
    except Exception as e:  # noqa: BLE001
        # raised: is it inside the precondition? (re-evaluate pre by hand when possible)
        return "raise", f"{type(e).__name__}: {str(e)[:70]}"
    if not pre(c, ns):
        return "rejected", cmp.digest(ftoks(w))
    return "kept", cmp.digest(ftoks(w))


# ------------------------------------------------------------------ Lean side
def bl(xs) -> str:
    return "[" + ", ".join(str(fb(x)) for x in xs) + "]"


def opt_pool(name: str, P: list) -> str:
    vals = [x for x in P if x is not None]
    pre_ = "[none] ++ " if P[0] is None else ""
    assert all(x is not None for x in P[1:])
    return f"let {name} : List (Option Float) := {pre_}({bl(vals)} : List UInt64).map (fun (b : UInt64) => some (Float.ofBits b)); "


FMT = ('let en := fun (x : Option Float) => (match x with | none => "N" | some v => toString v.toBits.toNat : String); '
       'let fw := fun (x : Option Float) (a b : Int) => "w" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
       'let d12 := fun (x : Option Float) => "t" ++ en x; '
       "let FT := fun (fs : List (String × Tabular.Table Float)) => fs.length.toUInt64 :: fs.flatMap (fun (f : String × Tabular.Table Float) => tS f.1 ++ tA f.2); ")
LCH = (f"let ch := fun (U : Nat → List UInt64) (M : List Nat) (b c : Nat) => dg (((List.range {CH}).filter (fun (i : Nat) => "
       f"(M.getD c 0 >>> i) % 2 == 1)).map (fun (i : Nat) => (dg (U (b + c * {CH} + i))).toNat.toUInt64)); ")


def lean_case(wild: bool) -> str:
    return (opt_pool("EP", EPW if wild else EP) + opt_pool("XE", XE) + opt_pool("EB", EB)
            + "let CS := fun (s : Nat) => "
            "(let n := ([0, 1, 2, 3, 4, 5, 8] : List Nat).getD ((hsh s 1) % 7).toNat 0; let q := (hsh s 7778) % 9; "
            "let fcol := fun (k : Nat) => Pl.Col.f64 (gF (s * 7 + k + 100) n 25 3 XE); "
            "let ca : Pl.Col Float := fcol 0; let cb : Pl.Col Float := fcol 1; "
            "let cc : Pl.Col Float := if (hsh s 9) % 10 == 0 then Pl.Col.int (gI (s * 7 + 105) n 10 7 3) else fcol 2; "
            "let pcol : Pl.Col Float := Pl.Col.f64 ((List.range n).map (fun (i : Nat) => let u := hsh s i; "
            "if (u >>> 8) % 100 < 30 then EP.getD ((u >>> 20) % EP.length.toUInt64).toNat none else some (Float.ofNat ((u >>> 20) % 65).toNat / 64.0))); "
            "let flag := fun (i : Nat) => let v := hsh (s + 77777) i; (if (v >>> 8) % 100 < 6 then none else some ((v >>> 20) % 8 < q) : Option Bool); "
            "let ycol : Pl.Col Float := if (hsh s 10) % 10 == 0 then Pl.Col.int ((List.range n).map (fun (i : Nat) => (flag i).map (fun (b : Bool) => if b then (1 : Int) else 0))) "
            "else Pl.Col.f64 ((List.range n).map (fun (i : Nat) => (flag i).map (fun (b : Bool) => if b then (1.0 : Float) else 0.0))); "
            'let fs : Pl.Frame Float := if (hsh s 11) % 2 == 0 then [("default_flag", ycol), ("pd_logistic", pcol), ("a", ca), ("b", cb), ("c", cc)] '
            'else [("a", ca), ("b", cb), ("c", cc), ("pd_logistic", pcol), ("default_flag", ycol)]; '
            "let fk := (hsh s 3) % 10; let q1 := ((hsh s 4) % 4).toNat; "
            "let blen := q1 + 1 + (if (hsh s 5) % 10 == 0 then 1 else 0); "
            "let beta : List Float := (gF (s + 500) blen 35 3 EB).map (fun (o : Option Float) => o.getD 0.0); "
            'let fin : LogisticFit Float := { names := (["Intercept", "a", "b", "c"] : List String).take (q1 + 1), beta := Np.NDArray.d1 beta, cov := Np.NDArray.d2 [], loglik := 0.0, n_iter := 1, converged := true }; '
            'let r := ((hsh s 12) % 3).toNat; let base : List String := ["a", "b", "c"]; let rot := base.drop r ++ base.take r; '
            "let rot2 := if (hsh s 13) % 2 == 0 then rot.reverse else rot; "
            "let e0 := rot2.take ((hsh s 6) % 4).toNat; "
            "let e1 := if (hsh s 14) % 20 == 0 && !e0.isEmpty then e0 ++ [rot2.headD \"\"] else e0; "
            'let e2 := if (hsh s 15) % 20 == 0 && !e1.isEmpty then "zz" :: e1.drop 1 else e1; '
            'let effs : List String := if fk == 0 then [] else e2; '
            "let idxs : List Int := if fk == 0 then [] else (List.range effs.length).map (fun (j : Nat) => let u := hsh (s + 900) j; "
            "if (u >>> 8) % 100 < 75 then ((if j + 1 < blen - 1 then j + 1 else blen - 1 : Nat) : Int) else (((u >>> 20) % blen.toUInt64).toNat : Int)); "
            "let lk := (hsh s 16) % 100; "
            "let lo : List Int := if fk == 0 then (if lk < 5 then [0] else []) else (if lk < 50 then [] else if lk < 85 then [1] else [0, 2]); "
            "let fin' : Option (LogisticFit Float) := if fk == 0 then none else some fin; "
            "FT (train_run_05_association (α := Float) fw d12 fin' effs idxs lo fs)); ")


def blocks(wild: bool, base: int, chunks: int):
    out = {"kept": ([], []), "rejected": ([], [])}
    n = Counter()
    raises = []
    for c in range(chunks):
        m = {"kept": 0, "rejected": 0}
        ds = {"kept": [], "rejected": []}
        for i in range(CH):
            s = base + c * CH + i
            cls, d = d05(s, wild)
            n[cls] += 1
            if cls in m:
                m[cls] |= 1 << i
                ds[cls].append(d)
            else:
                raises.append((s, d))
        for k_ in m:
            out[k_][0].append(m[k_])
            out[k_][1].append((len(ds[k_]), cmp.digest(ds[k_])))
    return out, n, raises


def add(st: Suite, what: str, wild: bool, base: int, chunks: int, masks, digs, fz: str) -> None:
    cases = [(f"{what} seeds {base + c * CH}..{base + c * CH + CH - 1} ({k} inputs)", UNIT, d, {"fz": fz, "covers": k})
             for c, (k, d) in enumerate(digs)]
    st.ints(FMT + lean_case(wild) + LCH + f"let M : List Nat := {masks}; ", f"((List.range {chunks}).map (ch CS M {base}))", cases, gen=True, table=True)


def main() -> None:
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_e", "zz_carrier_e")
    print("source range", R05)
    TAME, WILD = (500000, 46), (600000, 14)
    st = Suite("fz5_s05")
    o1, n1, r1 = blocks(False, TAME[0], TAME[1])
    add(st, "tame pd,", False, TAME[0], TAME[1], o1["kept"][0], o1["kept"][1], "kept")
    o2, n2, r2 = blocks(True, WILD[0], WILD[1])
    add(st, "wild pd (NaN, +-inf, -0.0, 2.0, -1.0),", True, WILD[0], WILD[1], o2["kept"][0], o2["kept"][1], "kept")
    st.write()
    sr = Suite("fz5_s05_rej")
    add(sr, "rejected by the precondition, Python returns,", False, TAME[0], TAME[1], o1["rejected"][0], o1["rejected"][1], "rejected")
    add(sr, "rejected by the precondition, Python returns, wild pd,", True, WILD[0], WILD[1], o2["rejected"][0], o2["rejected"][1], "rejected")
    sr.write()
    kept = n1["kept"] + n2["kept"]
    print("tame", dict(n1), "wild", dict(n2))
    print("python raises:", (r1 + r2)[:10], len(r1 + r2))
    (suite_mod.WORK / "fz5_s05.fuzz.json").write_text(json.dumps({
        "generator": "diffeval/units/fz5_s05_gen.py", "blueprint": BLUEPRINT,
        "units": {UNIT: {"seeds": f"{TAME[0]}..{TAME[0] + TAME[1] * CH - 1} (tame pd), {WILD[0]}..{WILD[0] + WILD[1] * CH - 1} (wild pd)",
                         "generated": (TAME[1] + WILD[1]) * CH, "kept": kept, "rejected_python_returns": n1["rejected"] + n2["rejected"],
                         "python_raises": [s for s, _ in r1 + r2]}}}, indent=1))
    for s_ in ("fz5_s05", "fz5_s05_rej"):
        for i, x in enumerate(json.loads((suite_mod.WORK / f"{s_}.inputs.json").read_text())[0]["inputs"]):
            print(s_, i, len(x), "chars")


main()
