"""Fuzz of def:train_run_06_coefficients_odds (revision 9e75fbfb...) and def:train_run_06_coefficients_odds_precond
(bb6c72af...), fifth port diff, by a non-author, blueprint 5365851c-.... Nothing is changed on the blueprint.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_s06_gen.py [N] [K]
      writes work/fz5_s06.json (per-seed classes, digests, chunk digests) and work/fz5_s06.term.txt / .flip.txt / .detail<c>.txt

Evaluation: eval_decl(item def:train_run_06_coefficients_odds, decl Np.cumsumInt, inputs=[term]); the term is a List Int:
the 1-based indexes of the chunks (of K seeds) whose digest differs from the expected one, then the number of chunks.

Case of seed s (built INSIDE Lean from hsh, mirrored here):
  hasfit  hsh(s,1)%8 != 0 (else final = none)       mn = 1 + hsh(s,2)%5 (side of the covariance)
  beta    d1 of length mn (mn-1 when hsh(s,3)%12==0), element i = bpick; cov = cr rows (mn, or mn-1 when hsh(s,4)%15==0) of mn
          entries, diagonal i = cpick, rest 0.25; hsh(s,7)%40==0: wrong rank (beta d2 [[..]] or cov d1)
  effects ne = hsh(s,9)%5 names from the pool NP (long, non-ASCII, empty, 20 and 21 characters);
  final_index mode hsh(s,10)%8: 1 reversed, 2 random in 1..mn, 3 last = 0, 4 one index fewer (length mismatch), 5 last = -1, else 1+i%(mn-1)
  intercept none (1/7) or ipick;  left_out mode hsh(s,12)%5: 0,1 the i < mn with diagonal 0.0 / -0.0 (as train.py), 2 empty,
          3 random subset of 0..mn, 4 the diagonal ones plus 0 or 1.
Routines (both sides): fmt_wd / fmt_oddsr / sas_d8 / sas_pvalue = injective encodings of the argument bits, chi2 x d = x/(d+3),
pow2 = x*x (plus a table where Python's ** 2 differs, if any). Python side: the REAL lines train.py:379-434 (extracted from
the file at run time) executed with the formatters patched; write_sas_csv recorded.
Precondition: the Python function `pre`, a reading of def:train_run_06_coefficients_odds_precond. Classes: kept (pre true and
Python returns: compared), py_raises_pre_true (precondition too weak: a finding), pre_false_py_returns (narrowing),
pre_false_py_raises (excluded rightly).
"""
from __future__ import annotations

import json
import math
import re
import struct
import sys
import textwrap
import types
from collections import Counter
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[3] / "port"))
import compare as cmp  # noqa: E402
import kit  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

nx = math.nextafter
nan, inf = float("nan"), float("inf")
M64 = (1 << 64) - 1
hsh = kit.hsh


def fb(x):
    return 0x7FF8000000000000 if x != x else struct.unpack("<Q", struct.pack("<d", x))[0]


def bf(b):
    return struct.unpack("<d", struct.pack("<Q", b & M64))[0]


EXPMAX = 709.782712893384
BP = [0.0, -0.0, 1.0, -1.0, 0.5, 2.3, 700.0, -745.0, 709.0, EXPMAX, nx(EXPMAX, inf), nx(EXPMAX, 0.0), 710.0, nan, inf, -inf,
      1e-300, 5e-324, 30.0, -30.0, -708.0, -745.2, 1e300, -1e300]
CP = [0.0, -0.0, 1.0, 4.0, 0.25, 1e-300, 5e-324, nan, inf, -1.0, 1e300, 1e-10, 2.0, 1e-320, 1e-5, 100.0]
IP = [0.0, -0.0, nan, inf, -inf, 1.0, -2.5, 1e300, 5e-324, 0.1]
NP = ["Intercept", "x1", "age", "a_very_long_effect_name_over_20_chars", "é€𝄞é€𝄞é€𝄞é€𝄞é€𝄞é€𝄞é€𝄞é€𝄞", "",
      "twenty_chars_exactly", "twenty_one_chars_abcd"]
assert len(NP[6]) == 20 and len(NP[7]) == 21 and len(NP[4]) == 24


def pick(L, u):
    return L[(u >> 20) % len(L)]


def rnd(u, eh):
    return bf((u & 0x8000000000000000) | (((1023 - eh + (u >> 52) % (2 * eh + 1)) << 52) & M64) | (u & 0xFFFFFFFFFFFFF))


def bpick(s, i):
    u = hsh(s, 100 + i)
    return pick(BP, u) if (u >> 8) % 100 < 45 else rnd(u, 4)


def cpick(s, i):
    u = hsh(s, 200 + i)
    return pick(CP, u) if (u >> 8) % 100 < 45 else bf(fb(rnd(u, 4)) & 0x7FFFFFFFFFFFFFFF)


def ipick(s):
    u = hsh(s, 400)
    return pick(IP, u) if (u >> 8) % 100 < 55 else rnd(u, 3)


def case(s):
    h = lambda k: hsh(s, k)  # noqa: E731
    hasfit = h(1) % 8 != 0
    mn = 1 + h(2) % 5
    bl = mn - 1 if h(3) % 12 == 0 else mn
    cr = mn - 1 if h(4) % 15 == 0 else mn
    rankbad = h(7) % 40 == 0
    rb2 = h(8) % 2 == 0
    betaL = [bpick(s, i) for i in range(bl)]
    rows = [[cpick(s, i) if i == j else 0.25 for j in range(mn)] for i in range(cr)]
    ne = h(9) % 5
    effects = [NP[hsh(s, 300 + i) % 8] for i in range(ne)]
    base = [1 + i % max(mn - 1, 1) for i in range(ne)]
    im = h(10) % 8
    if im == 1:
        fidx = base[::-1]
    elif im == 2:
        fidx = [1 + hsh(s, 500 + i) % mn for i in range(ne)]
    elif im == 3:
        fidx = base[:-1] + [0] if ne > 0 else base
    elif im == 4:
        fidx = base[:-1] if ne > 0 else [1]
    elif im == 5:
        fidx = base[:-1] + [-1] if ne > 0 else base
    else:
        fidx = base
    icpt = None if h(11) % 7 == 0 else ipick(s)
    diag0 = [i for i in range(mn) if cpick(s, i) == 0.0]
    lm = h(12) % 5
    if lm <= 1:
        lo = diag0
    elif lm == 2:
        lo = []
    elif lm == 3:
        lo = [i for i in range(mn + 1) if hsh(s, 600 + i) % 3 == 0]
    else:
        lo = diag0 + [0 if h(13) % 2 == 0 else 1]
    return dict(s=s, hasfit=hasfit, mn=mn, betaL=betaL, rows=rows, rankbad=rankbad, rb2=rb2, effects=effects, fidx=fidx,
                icpt=icpt, lo=lo)


def enc(x):
    return "N" if x is None else str(fb(x))


# ---- Python side: the real lines of train.py
SRC = (HERE.parents[3] / "port" / "credit_risk" / "train.py").read_text().split("\n")
a = next(i for i, l in enumerate(SRC) if l.startswith("    mc_variable: list[str] = [] if final is None"))
b = next(i for i, l in enumerate(SRC) if i > a and l.startswith("        sas_compat.write_sas_csv(printed_odds_ratios"))
BLOCK = textwrap.dedent("\n".join(SRC[a:b + 1]))
CODE = ("def _blk(final, final_effects, final_index, intercept, left_out, sas_compat, math, pl, output_dir):\n"
        + textwrap.indent(BLOCK, "    ") + "\n    return model_coefficients\n")
NS: dict = {}
exec(CODE, NS)  # noqa: S102

WROTE: list = []
FAKE = types.SimpleNamespace(**{k: getattr(sc, k) for k in dir(sc) if not k.startswith("__")})
FAKE.fmt_wd = lambda x, w, d: f"w{enc(x)}/{w}/{d}"
FAKE.fmt_oddsr = lambda x, w, d: f"o{enc(x)}/{w}/{d}"
FAKE.sas_d8 = lambda x: f"e{enc(x)}"
FAKE.sas_pvalue = lambda x: f"p{enc(x)}"
FAKE.write_sas_csv = lambda df, path, formats=None: WROTE.append((Path(path).name, df))


class Chi2:
    @staticmethod
    def sf(x, df):
        return float(x) / (float(df) + 3.0)


FAKE.chi2 = Chi2
FAKE.chi2_sf = lambda x, df: float(Chi2.sf(x, df))


def py_run(c):
    WROTE.clear()
    if c["rankbad"] and not c["rb2"]:
        cov = np.array([r[i] if i < len(r) else 0.0 for i, r in enumerate(c["rows"])], dtype=np.float64)
    else:
        cov = np.array(c["rows"], dtype=np.float64).reshape(len(c["rows"]), c["mn"])
    beta = np.array([c["betaL"]], dtype=np.float64) if c["rankbad"] and c["rb2"] else np.array(c["betaL"], dtype=np.float64)
    fit = sc.LogisticFit(names=[], beta=beta, cov=cov, loglik=0.0, n_iter=0, converged=True)
    final = fit if c["hasfit"] else None
    try:
        with np.errstate(all="ignore"):
            mc = NS["_blk"](final, list(c["effects"]), list(c["fidx"]), c["icpt"], list(c["lo"]), FAKE, math, pl, Path("out"))
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}"
    return (mc, list(WROTE)), None


def pre(c):
    """def:train_run_06_coefficients_odds_precond, read from the Lean statement."""
    if len(c["fidx"]) != len(c["effects"]):
        return False
    if not c["hasfit"]:
        return True
    if any(i == 0 for i in c["fidx"]):
        return False
    for idx in [0] + c["fidx"]:
        if idx in c["lo"]:
            continue
        if c["rankbad"] and (c["rb2"] or True):
            # beta d2 (rb2) or cov d1 (not rb2): the Lean clause needs d1 and d2
            return False
        if not (0 <= idx < len(c["betaL"]) and idx < len(c["rows"]) and idx < len(c["rows"][idx])):
            return False
        bv, cv = c["betaL"][idx], c["rows"][idx][idx]
        if cv < 0.0:
            return False
        se = math.sqrt(cv) if cv == cv else nan
        if se == 0.0:
            return False
        r = bv / se
        if math.isfinite(r) and not math.isfinite(r * r):
            return False
        if idx != 0:
            for arg in (bv, bv - sc.Z975 * se, bv + sc.Z975 * se):
                try:
                    if not math.isfinite(math.exp(arg)):
                        return False
                except OverflowError:
                    return False
    return True


def tS(s):
    return cmp.tok_str(s)


def toks(res):
    mc, files = res
    out = cmp.tokens(cmp.canon_frame(mc)) + [len(files)]
    for name, df in files:
        out += tS(name) + cmp.tokens(cmp.canon_table(df))
    return out


def u64(xs):
    return "[" + ", ".join(hex(fb(x)) for x in xs) + "]"


LEAN = (
    kit.GEN.split("let gF")[0]
    + f"let BP : List UInt64 := {u64(BP)}; let CP : List UInt64 := {u64(CP)}; let IP : List UInt64 := {u64(IP)}; "
    "let NP : List String := [" + ", ".join(json.dumps(x, ensure_ascii=False) for x in NP) + "]; "
    "let pick := fun (L : List UInt64) (u : UInt64) => Float.ofBits (L.getD ((u >>> 20) % L.length.toUInt64).toNat 0); "
    "let rnd := fun (u : UInt64) (eh : UInt64) => let k : UInt64 := u >>> 52; Float.ofBits ((u &&& 0x8000000000000000) ||| ((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) ||| (u &&& 0xFFFFFFFFFFFFF)); "
    "let bpick := fun (s i : Nat) => let u := hsh s (100 + i); if (u >>> 8) % 100 < 45 then pick BP u else rnd u 4; "
    "let cpick := fun (s i : Nat) => let u := hsh s (200 + i); if (u >>> 8) % 100 < 45 then pick CP u else Float.ofBits ((rnd u 4).toBits &&& 0x7FFFFFFFFFFFFFFF); "
    "let ipick := fun (s : Nat) => let u := hsh s 400; if (u >>> 8) % 100 < 55 then pick IP u else rnd u 3; "
    "let enc := fun (x : Option Float) => (match x with | none => \"N\" | some v => toString v.toBits.toNat : String); "
    "let fw := fun (x : Option Float) (a b : Int) => \"w\" ++ enc x ++ \"/\" ++ toString a ++ \"/\" ++ toString b; "
    "let fo := fun (x : Option Float) (a b : Int) => \"o\" ++ enc x ++ \"/\" ++ toString a ++ \"/\" ++ toString b; "
    "let d8 := fun (x : Option Float) => \"e\" ++ enc x; let pv := fun (x : Option Float) => \"p\" ++ enc x; "
    "let ch := fun (x : Float) (d : Int) => x / (Float.ofInt d + 3.0); let p2 := fun (x : Float) => x * x; "
    "let one := fun (s : Nat) => ("
    "let h := fun (k : Nat) => hsh s k; "
    "let hasfit : Bool := h 1 % 8 != 0; let mn : Nat := 1 + (h 2 % 5).toNat; "
    "let bl : Nat := if h 3 % 12 == 0 then mn - 1 else mn; let cr : Nat := if h 4 % 15 == 0 then mn - 1 else mn; "
    "let rankbad : Bool := h 7 % 40 == 0; let rb2 : Bool := h 8 % 2 == 0; "
    "let betaL : List Float := (List.range bl).map (fun (i : Nat) => bpick s i); "
    "let rows : List (List Float) := (List.range cr).map (fun (i : Nat) => (List.range mn).map (fun (j : Nat) => if i == j then cpick s i else 0.25)); "
    "let ne : Nat := (h 9 % 5).toNat; "
    "let effects : List String := (List.range ne).map (fun (i : Nat) => NP.getD ((hsh s (300 + i) % 8).toNat) \"\"); "
    "let base : List Int := (List.range ne).map (fun (i : Nat) => ((1 + i % (max (mn - 1) 1) : Nat) : Int)); "
    "let im : UInt64 := h 10 % 8; "
    "let fidx : List Int := if im == 1 then base.reverse "
    "else if im == 2 then (List.range ne).map (fun (i : Nat) => ((1 + (hsh s (500 + i) % mn.toUInt64).toNat : Nat) : Int)) "
    "else if im == 3 then (if ne > 0 then base.dropLast ++ [0] else base) "
    "else if im == 4 then (if ne > 0 then base.dropLast else [1]) "
    "else if im == 5 then (if ne > 0 then base.dropLast ++ [-1] else base) else base; "
    "let icpt : Option Float := if h 11 % 7 == 0 then none else some (ipick s); "
    "let diag0 : List Int := ((List.range mn).filter (fun (i : Nat) => cpick s i == 0.0)).map (fun (i : Nat) => (i : Int)); "
    "let lm : UInt64 := h 12 % 5; "
    "let lo : List Int := if lm ≤ 1 then diag0 else if lm == 2 then [] "
    "else if lm == 3 then ((List.range (mn + 1)).filter (fun (i : Nat) => hsh s (600 + i) % 3 == 0)).map (fun (i : Nat) => (i : Int)) "
    "else diag0 ++ [if h 13 % 2 == 0 then 0 else 1]; "
    "let beta : FloatArray_ Float := if rankbad && rb2 then Np.NDArray.d2 [betaL] else Np.NDArray.d1 betaL; "
    "let cov : FloatArray_ Float := if rankbad && !rb2 then Np.NDArray.d1 ((List.range cr).map (fun (i : Nat) => cpick s i)) else Np.NDArray.d2 rows; "
    "let fit : LogisticFit Float := { names := [], beta := beta, cov := cov, loglik := 0.0, n_iter := 0, converged := true }; "
    "let r := train_run_06_coefficients_odds fw fo d8 pv ch p2 (if hasfit then some fit else none) effects fidx icpt lo; "
    "(tR r.1 ++ [r.2.length.toUInt64] ++ r.2.flatMap (fun (p : String × Tabular.Table Float) => tS p.1 ++ tA p.2) : List UInt64)); "
)


def lean_term(N, K, kept, chunk_exp, flip=None):
    mask = 0
    for s in range(N):
        if s in kept:
            mask |= 1 << s
    exp = list(chunk_exp)
    if flip is not None:
        exp[flip] = (exp[flip] + 1) % (1 << 64)
    return ("(" + kit.KIT + LEAN + f"let MASK : Nat := {hex(mask)}; let EXP : List Nat := [{', '.join(str(e) for e in exp)}]; "
            f"let bad := (List.range {N // K}).filter (fun (c : Nat) => "
            f"let d := dg ((List.range {K}).flatMap (fun (t : Nat) => if Nat.testBit MASK ({K} * c + t) then one ({K} * c + t) ++ [999] else [])); "
            "d.toNat != EXP.getD c 0); "
            f"(bad.map (fun (c : Nat) => ((c + 1 : Nat) : Int))) ++ [({N // K} : Int)] : List Int)")


def detail_term(s0, k, kept):
    return ("(" + kit.KIT + LEAN + f"(List.range {k}).map (fun (t : Nat) => dg (one ({s0} + t)))" + " : List Int)")


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    assert N % K == 0
    cls, dig, kept = {}, {}, set()
    cov = Counter()
    raises = Counter()
    for s in range(N):
        c = case(s)
        res, err = py_run(c)
        p = pre(c)
        if p and res is not None:
            k = "kept"
            kept.add(s)
            dig[s] = cmp.digest(toks(res))
        elif p:
            k = "py_raises_pre_true"
            raises[err] += 1
        elif res is not None:
            k = "pre_false_py_returns"
        else:
            k = "pre_false_py_raises"
        cls[s] = k
        cov[k] += 1
        if k == "kept":
            cov["fit_none"] += not c["hasfit"]
            cov["icpt_none"] += c["icpt"] is None
            cov["ne0"] += len(c["effects"]) == 0
            cov["left_out_nonempty"] += len(c["lo"]) > 0
            cov["lo_contains0"] += 0 in c["lo"]
            cov["lo_idx_ne0_in_fidx"] += any(i in c["lo"] for i in c["fidx"])
            cov["long_name"] += any(len(x) > 20 for x in c["effects"])
            cov["nonbmp"] += any("𝄞" in x for x in c["effects"])
            cov["nan_beta0"] += c["hasfit"] and bool(c["betaL"]) and c["betaL"][0] != c["betaL"][0]
            cov["fi_reversed_or_random"] += c["fidx"] != sorted(c["fidx"])
            mc, files = res
            cov["files_written"] += len(files)
            cov["empty_odds_table_written"] += any(df.height == 0 for _, df in files)
            cov["mc_rows_0"] += mc.height == 0
    chunk_exp = []
    for ch in range(N // K):
        t = []
        for s in range(ch * K, ch * K + K):
            if s in kept:
                t += toks(py_run(case(s))[0]) + [999]
        chunk_exp.append(cmp.digest(t))
    out = {"N": N, "K": K, "classes": dict(cov), "kept": sorted(kept), "chunk_exp": chunk_exp,
           "digests": {str(s): dig[s] for s in sorted(kept)}, "py_raise_kinds": dict(raises)}
    W = HERE.parent / "work"
    (W / "fz5_s06.json").write_text(json.dumps(out))
    (W / "fz5_s06.term.txt").write_text(lean_term(N, K, kept, chunk_exp))
    (W / "fz5_s06.flip.txt").write_text(lean_term(N, K, kept, chunk_exp, flip=0))
    print(json.dumps({k: v for k, v in out.items() if k in ("N", "K", "classes", "py_raise_kinds")}, indent=1, sort_keys=True))
    print("term length", len(lean_term(N, K, kept, chunk_exp)))


if __name__ == "__main__":
    main()
