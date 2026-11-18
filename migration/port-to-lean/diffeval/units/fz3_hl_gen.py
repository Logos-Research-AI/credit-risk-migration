"""Fuzz of the update of 2026-11-17 by a non-author: def:train_run_07_hl (revision 2ce4352c...) and
def:train_run_07_hl_precond (revision 941f5b6b...), on def:zz_carrier_t of blueprint 5365851c-....
Successor of fz2_s567_gen.py (same encodings and method), new generator, more edges:

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz3_hl_gen.py

Inputs built inside Lean from the seed s and mirrored here (integer arithmetic only).
fit_scored = [pd_logistic, default_flag], n rows, n = NS[hsh(s,7777) % len(NS)], NS has 0, 1, 2, 3, 4, 5, 9..11, 15,
19..21, 24, 25, 35, 40, 45, 55, 60, 100 (thresholds of _hl_groups: floor(n/10+0.5), floor(0.05 n)).
pd row i (u = hsh(s+31337, i), m = (u >> 8) % 100, base(s, i) = the pool / k/64 value):
  m < 25 and i > 0: chain: base(s, i-1) + 1e-6, shifted by 0, +1 or -1 ulp ((u >> 20) % 3) (block threshold of
  searchsorted(p[i] + 1e-6, right)); m < 35 and i > 0: base(s, i-1) again (tie); else base(s, i).
  base: null 8 %, 22 % from the pool EP (null, 0, 1, 0.5 and 2 neighbours, 0.25, 1e-300, float below 1, 0.1, 0.9,
  1e-6 and 2 neighbours, 5e-7, 0.999999 and 2 neighbours, 0.9999995), else k/64 (k 0..64). Wild seeds: EP plus NaN,
  +-inf, -0.0, 2.0, -1.0.
default_flag row i (v = hsh(s+77777, i)): null 5 %, else 1.0 when (v >> 20) % 8 < hsh(s,7778) % 9 else 0.0; wild seeds:
  rows with (v >> 30) % 10 == 0 take a value of {0.5, 2.0, -1.0, NaN, inf}.
final_effects = [[], ["x"], ["age", "monthly_income"]][hsh(s,7779) % 3].
Expected: the unit's own lines of train.py (hl_table ... hl_written, the two writes), executed on the mirrored inputs.
Precondition (def:train_run_07_hl_precond) rendered as the Python function pre07, clause by clause on the raw sums
(NOT on the int-truncated table): equal lengths (by construction); after the drop of null rows, n <= 2^52; for every
group, size != 0, o1 = float sum of the group's outcomes finite, integral, |o1| <= 2^52, and finite(o1-e1) =>
finite((o1-e1)**2), finite(o0-e0) => finite((o0-e0)**2), with e1, o0, e0 as the loop computes them.
A seed rejected by pre07 is not counted; a seed pre07 accepts on which Python raises is a defect and listed.
"""
from __future__ import annotations

import json
import math
import struct
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
import suite as suite_mod  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
CH = 50
NS = [0, 1, 2, 3, 4, 5, 9, 10, 11, 15, 19, 20, 21, 24, 25, 35, 40, 45, 55, 60, 100]
inf, nan = float("inf"), float("nan")
nx = math.nextafter
EP = [None, 0.0, 1.0, 0.5, nx(0.5, 1), nx(0.5, 0), 0.25, 1e-300, nx(1.0, 0), 0.1, 0.9,
      1e-6, nx(1e-6, 1), nx(1e-6, 0), 5e-7, 0.999999, nx(0.999999, 1), nx(0.999999, 0), 0.9999995]
EPW = EP + [nan, inf, -inf, -0.0, 2.0, -1.0]
EYW = [0.5, 2.0, -1.0, nan, inf]
FEFF = [[], ["x"], ["age", "monthly_income"]]
U7 = "train_run_07_hl"


def fb(x) -> int:
    return cmp.fbits(float(x))


def bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def frombits(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b & ((1 << 64) - 1)))[0]


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


a_ = find("hl_table, hl_chisq, hl_df, hl_p = sas_compat.hosmer_lemeshow(")
b_ = find('"printed_hosmer_lemeshow.csv"', a_) + 1
C07 = compile(textwrap.dedent("\n".join(SRC[a_:b_ + 1])), f"train.py:{a_ + 1}-{b_ + 1}", "exec")
print("source range", a_ + 1, b_ + 1)
assert "hl_written" in "\n".join(SRC[a_:b_ + 1])


def run(env: dict):
    writes: list = []
    saved = {k: getattr(sc, k) for k in (*ENCODERS, "write_sas_csv", "chi2")}
    try:
        for k, f in ENCODERS.items():
            setattr(sc, k, f)
        sc.chi2 = Chi2
        sc.write_sas_csv = lambda df, path, formats=None: writes.append((Path(path).name, df.clone()))
        ns = dict(vars(train))
        ns.update(env, output_dir=Path("out"))
        exec(C07, ns)  # noqa: S102  the port's own lines
    finally:
        for k, f in saved.items():
            setattr(sc, k, f)
    return writes, ns


XP: dict[int, int] = {}


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


# ------------------------------------------------------------------ inputs
def nof(s: int) -> int:
    return NS[kit.hsh(s, 7777) % len(NS)]


def base(s: int, i: int, wild: bool):
    P = EPW if wild else EP
    u = kit.hsh(s, i)
    if (u >> 8) % 100 < 8:
        return None
    if (u >> 8) % 100 < 30:
        return P[(u >> 20) % len(P)]
    return float((u >> 20) % 65) / 64.0


def pd_at(s: int, i: int, wild: bool):
    u = kit.hsh(s + 31337, i)
    m = (u >> 8) % 100
    if i > 0 and m < 25:
        v = base(s, i - 1, wild)
        if v is None:
            return base(s, i, wild)
        w = v + 1e-6
        if math.isfinite(w):
            k = (u >> 20) % 3
            if k == 1:
                w = frombits(bits(w) + 1)
            elif k == 2:
                w = frombits(bits(w) - 1)
        return w
    if i > 0 and m < 35:
        return base(s, i - 1, wild)
    return base(s, i, wild)


def y_at(s: int, i: int, wild: bool):
    q = kit.hsh(s, 7778) % 9
    v = kit.hsh(s + 77777, i)
    if (v >> 8) % 100 < 5:
        return None
    if wild and (v >> 30) % 10 == 0:
        return EYW[(v >> 40) % len(EYW)]
    return 1.0 if (v >> 20) % 8 < q else 0.0


def fs_frame(s: int, wild: bool) -> pl.DataFrame:
    n = nof(s)
    return pl.DataFrame({"pd_logistic": pl.Series([pd_at(s, i, wild) for i in range(n)], dtype=pl.Float64),
                         "default_flag": pl.Series([y_at(s, i, wild) for i in range(n)], dtype=pl.Float64)})


def feff_of(s: int) -> list[str]:
    return FEFF[kit.hsh(s, 7779) % 3]


# ------------------------------------------------------------------ precondition, independent of the unit's body
def pre07(fr: pl.DataFrame) -> bool:
    y, pd_ = fr.get_column("default_flag").to_list(), fr.get_column("pd_logistic").to_list()
    d = [(a, b) for a, b in zip(y, pd_, strict=True) if a is not None and b is not None]
    if not d:
        return True
    n = len(d)
    if n > 2 ** 52:
        return False
    p0 = np.array([b for _, b in d], dtype=np.float64)
    y0 = np.array([a for a, _ in d], dtype=np.float64)
    o = np.argsort(p0, kind="stable")
    p, yy = p0[o], y0[o]
    blocks, i = [], 0
    while i < n:
        j = int(p.searchsorted(float(p[i]) + 1e-6, side="right"))
        blocks.append(j - i)
        i = j
    starts = np.concatenate([[0], np.cumsum(blocks)[:-1]]).astype(np.int64)
    p = np.repeat(p[starts], blocks)
    sizes = sc._hl_groups(blocks, n, 10)
    start = 0
    for size in sizes:
        if size == 0:
            return False
        o1 = float(yy[start:start + size].sum())
        avg = float(p[start:start + size].sum()) / size
        lo = 1e-6 if 1e-6 > avg else avg
        hi = 0.999999 if 0.999999 < lo else lo
        e1 = size * hi
        start += size
        o0, e0 = size - o1, size - e1
        if not math.isfinite(o1) or math.floor(o1) != o1 or abs(o1) > 2.0 ** 52:
            return False
        with np.errstate(all="ignore"):
            for x in (o1 - e1, o0 - e0):
                if math.isfinite(x) and not math.isfinite(float(np.float64(x) * np.float64(x))):
                    return False
    return True


STATS = Counter()


def d07(s: int, wild: bool):
    fr = fs_frame(s, wild)
    ok = pre07(fr)
    try:
        w, ns = run({"fit_scored": fr, "final_effects": feff_of(s)})
    except Exception as e:  # noqa: BLE001
        return ("defect" if ok else "drop"), f"{type(e).__name__}: {str(e)[:60]}"
    if not ok:
        return "rejected", None
    h = ns["hl_table"]
    for o1, e1, o0, e0 in zip(*(h.get_column(c).to_list() for c in ("EventsObserved", "EventsExpected", "NoneventsObserved", "NoneventsExpected")), strict=True):
        note_pow(o1 - e1)
        note_pow(o0 - e0)
    STATS[("ngroups", h.height)] += 1
    STATS[("files", len(w), bool(feff_of(s)))] += 1
    STATS[("n", nof(s))] += 1
    return "kept", cmp.digest(ftoks(w))


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
       'let pv := fun (x : Option Float) => "p" ++ en x; '
       "let chi2 := fun (x : Float) (d : Int) => x / (Float.ofInt d + 3.0); "
       "let FT := fun (fs : List (String × Tabular.Table Float)) => fs.length.toUInt64 :: fs.flatMap (fun (f : String × Tabular.Table Float) => tS f.1 ++ tA f.2); ")
LCH = (f"let ch := fun (U : Nat → List UInt64) (M : List Nat) (b c : Nat) => dg (((List.range {CH}).filter (fun (i : Nat) => "
       f"(M.getD c 0 >>> i) % 2 == 1)).map (fun (i : Nat) => (dg (U (b + c * {CH} + i))).toNat.toUInt64)); ")


def l7(wild: bool) -> str:
    yw = opt_pool("EY", EYW) if wild else ""
    ycell = ("if (v >>> 8) % 100 < 5 then none else "
             + ("if (v >>> 30) % 10 == 0 then EY.getD ((v >>> 40) % EY.length.toUInt64).toNat none else " if wild else "")
             + "some (if (v >>> 20) % 8 < q then 1.0 else 0.0)")
    return (opt_pool("EP", EPW if wild else EP) + yw
            + f"let nOf := fun (s : Nat) => ([{', '.join(map(str, NS))}] : List Nat).getD ((hsh s 7777) % {len(NS)}).toNat 0; "
            "let base := fun (s i : Nat) => (let u := hsh s i; if (u >>> 8) % 100 < 8 then (none : Option Float) else "
            "if (u >>> 8) % 100 < 30 then EP.getD ((u >>> 20) % EP.length.toUInt64).toNat none else some (Float.ofNat ((u >>> 20) % 65).toNat / 64.0)); "
            "let pdAt := fun (s i : Nat) => (let u := hsh (s + 31337) i; let m := (u >>> 8) % 100; "
            "if i > 0 && m < 25 then (match base s (i - 1) with | none => base s i | some v => "
            "(let w := v + 1e-6; if w.isFinite then (let k := (u >>> 20) % 3; if k == 1 then some (Float.ofBits (w.toBits + 1)) else if k == 2 then some (Float.ofBits (w.toBits - 1)) else some w) else some w)) "
            "else if i > 0 && m < 35 then base s (i - 1) else base s i); "
            "let FS := fun (s : Nat) => (let n := nOf s; let q := (hsh s 7778) % 9; let f : Pl.Frame Float := [(\"pd_logistic\", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => pdAt s i))), "
            "(\"default_flag\", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => let v := hsh (s + 77777) i; " + ycell + ")))]; f); "
            'let FE := fun (s : Nat) => ([[], ["x"], ["age", "monthly_income"]] : List (List String)).getD ((hsh s 7779) % 3).toNat []; ')


def blocks(per_seed, base_: int, chunks: int):
    XP.clear()
    masks, digs = [], []
    n = Counter()
    defects = []
    for c in range(chunks):
        m, ds = 0, []
        for i in range(CH):
            s = base_ + c * CH + i
            cls, d = per_seed(s)
            n[cls] += 1
            if cls == "kept":
                m |= 1 << i
                ds.append(d)
            elif cls == "defect":
                defects.append((s, d))
        masks.append(m)
        digs.append((len(ds), cmp.digest(ds)))
    return masks, digs, n, defects


def add(st: Suite, what: str, lets: str, uterm: str, base_: int, chunks: int, masks, digs) -> None:
    cases = [(f"{what} seeds {base_ + c * CH}..{base_ + c * CH + CH - 1} ({k} inputs)", U7, d, {"fz": "kept", "covers": k})
             for c, (k, d) in enumerate(digs)]
    st.ints(FMT + lean_pow2() + lets + LCH + f"let M : List Nat := {masks}; ", f"((List.range {chunks}).map (ch ({uterm}) M {base_}))", cases, gen=True, table=True)


def main() -> None:
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")
    T7 = "fun (s : Nat) => FT (train_run_07_hl (α := Float) fw pv chi2 pow2 (FS s) (FE s))"
    TT, TW = 50, 10
    st = Suite("fz3_hl")
    m1, d1, n1, def1 = blocks(lambda s: d07(s, False), 400000, TT)
    add(st, "tame pd,", l7(False), T7, 400000, TT, m1, d1)
    print("tame pow2 exceptions", len(XP))
    m2, d2, n2, def2 = blocks(lambda s: d07(s, True), 500000, TW)
    add(st, "wild pd/outcomes,", l7(True), T7, 500000, TW, m2, d2)
    st.write()
    print("tame", dict(n1), "wild", dict(n2), "defects", (def1 + def2)[:8])
    for k in sorted(STATS, key=str):
        print(k, STATS[k])
    for i, x in enumerate(json.loads((suite_mod.WORK / "fz3_hl.inputs.json").read_text())[0]["inputs"]):
        print("input", i, len(x), "chars")
    (suite_mod.WORK / "fz3_hl.fuzz.json").write_text(json.dumps({"generated": sum(n1.values()) + sum(n2.values()),
        "kept": n1["kept"] + n2["kept"], "rejected": n1["rejected"] + n2["rejected"], "drop": n1["drop"] + n2["drop"],
        "defects": [s for s, _ in def1 + def2]}, indent=1))


main()
