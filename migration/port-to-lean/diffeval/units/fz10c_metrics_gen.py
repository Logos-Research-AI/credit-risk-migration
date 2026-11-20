"""Fidelity pass 2026-11-20, third attempt, label metrics: def:confusion_metrics, def:metrics_run_03_thresholds,
def:metrics_run_05_cumulative_lift against the CURRENT port (HEAD 4a757fb), on the carrier def:zz_carrier_fid_2.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_metrics_gen.py
      -> work/fz10c_cm, fz10c_th, fz10c_lift, fz10c_lift_nz, fz10c_real  (.json, .inputs.json, .fuzz.json)
  (eval_decl every input of work/<suite>.inputs.json on def:zz_carrier_fid_2 / zz_carrier_fid_2; outputs one per
   line in work/<suite>.out.txt; compare.py; FUZZ_RECEIPTS=fuzz_2026-11-20c-metrics.tsv python3 diffeval/fuzz_receipt.py)

Expected values: the REAL port code. confusion_metrics: the function itself (metrics_calculation.confusion_metrics).
Step 03: the source lines of run from `_confusion_03, ... = confusion_metrics(0.3` to the end of the pl.concat,
cut by marker text and executed with the module globals. Step 05: the source lines from `into = decile_data.select(`
to `# listing-only: PROC SGPLOT cumulative_lift` (the valid_exists branch included), same way; sas_best(x, 8) and
float(text) are explicit parameters of the Lean unit: lookup tables recorded from the real functions during the
Python run (as fz_t14_gen / fz7_metrics_gen).

Inputs are built inside Lean from the seed (kit.GEN gF / gI / hsh) and mirrored here bit for bit. One case = one
64-bit digest over the token streams of the seeds of one class inside one window (`covers` = number of seeds):
for each seed the input frame(s), and the result frame(s). Seeds on which Python raises are listed in `EX` of the
input and left out (counted as dropped or as defects).

Preconditions, rendered from the Lean text of the _precond items:
  confusion_metrics_precond: distinct names, equal lengths (true by construction: a pl.DataFrame); pd_logistic and
    default_flag present with a numeric kind (Float64 or Int64). Rejected flavour: a Boolean default_flag.
  metrics_run_03_thresholds_precond: the same clause for each of the five thresholds (same frame) = the same test.
  metrics_run_05_cumulative_lift_precond: distinct names, equal lengths (construction); Float64 default_flag in
    decile_data (0 rows admitted since 2026-11-18); decile Float64 in Lean = Int64 in Python (R-F2I, by
    construction); Float64 defaults; Int64 total_count. Rejected flavour: a Float64 total_count.
"""
from __future__ import annotations

import json
import math
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
_argv, sys.argv = sys.argv, [sys.argv[0]]
import suite as suite_mod  # noqa: E402
import fz_t14_gen as f14  # noqa: E402  (imports t14_gen, which sets another carrier: reset below)
import t14_gen as t14  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import WORK, Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

sys.argv = _argv
CARRIER = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")
suite_mod.CARRIERS["identity"] = CARRIER
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
GENR = "diffeval/units/fz10c_metrics_gen.py"
FUZZER = "port-translator (fidelity pass 2026-11-20c, metrics)"
UCM, U03, U05 = "confusion_metrics", "metrics_run_03_thresholds", "metrics_run_05_cumulative_lift"
nan, inf = float("nan"), float("inf")
u = math.nextafter

# ------------------------------------------------------------------ real source, cut by markers
L = Path(mc.__file__).read_text().splitlines(keepends=True)


def cut(a, b, incl_b=False):
    i = next(k for k, l in enumerate(L) if a in l)
    j = next(k for k in range(i, len(L)) if b in L[k])
    return compile(textwrap.dedent("".join(L[i:j + (1 if incl_b else 0)])), f"mc:{i + 1}-{j + (1 if incl_b else 0)}", "exec")


# step 03: from the first call to the closing parenthesis of the concat ends on the line after the list: include the closing parenthesis
_i3 = next(k for k, l in enumerate(L) if "_confusion_03, _conf_matrix_03" in l)
_j3 = next(k for k in range(_i3, len(L)) if 'how="vertical"' in L[k])
C03 = compile(textwrap.dedent("".join(L[_i3:_j3 + 2])), f"mc:{_i3 + 1}-{_j3 + 2}", "exec")
assert L[_j3 + 1].strip() == ")", L[_j3 + 1]
C05 = cut("into = decile_data.select(", "# listing-only: PROC SGPLOT cumulative_lift")
assert "if not valid_exists:" in "".join(L[next(k for k, l in enumerate(L) if "into = decile_data.select(" in l):][:60])


def ex(code, ns):
    exec(code, ns)  # noqa: S102


def f64(v):
    return pl.Series(v, dtype=pl.Float64, nan_to_null=False)


def i64(v):
    return pl.Series(v, dtype=pl.Int64)


def ob(name, E):
    return f14.pool(name, E)


# ------------------------------------------------------------------ confusion_metrics / step 03 frames
NS = [0, 1, 1, 2, 3, 4, 5, 7, 10, 13, 20, 30, 45]
FC = [None, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
FW = [None, 0.0, 1.0, nan, inf, -inf, 2.0, 0.5, -1.0, -0.0, 1e300, 1.0, 0.0]
TS = [0.3, 0.4, 0.5, 0.6, 0.7]
PE = [None, nan, inf, -inf, 0.0, -0.0, 1.0, 1e300, 1e-300, 5e-324, 0.25, 2.0, -1.0] + [x for t in TS for x in (t, u(t, 0), u(t, 1))]
TH = [x for t in TS for x in (t, u(t, 0), u(t, 1))] + [0.0, -0.0, nan, inf, -inf, 1.0, 5e-324, 2.0, -1.0, 0.45]
SP = ["", ".", "NA", " 1", "-2", "x"]


def flav(s):
    """(n, flag kind, pd kind, extras, swap): flag kind 0 clean f64, 1 Int64, 2 wild f64, 3 Boolean (rejected)."""
    n = NS[kit.hsh(s, 7) % len(NS)]
    a = kit.hsh(s, 11) % 10
    fk = 1 if a in (5, 6) else 2 if a == 7 else (3 if kit.hsh(s, 15) % 3 == 0 else 0) if a == 9 else 0
    b = kit.hsh(s, 12) % 8
    pk = 1 if b == 6 else 2 if b == 7 else 0
    return n, fk, pk, kit.hsh(s, 13) % 4, kit.hsh(s, 14) % 2


def frameF(s):
    n, fk, pk, xk, sw = flav(s)
    if fk == 1:
        fl = i64(kit.gI(4 * s, n, 10, 4, 1))
    elif fk == 2:
        fl = f64(kit.gF(4 * s, n, 85, 2, FW))
    elif fk == 3:
        fl = pl.Series([None if v is None else v == 1 for v in kit.gI(4 * s, n, 10, 2, 0)], dtype=pl.Boolean)
    else:
        fl = f64(kit.gF(4 * s, n, 100, 2, FC))
    pd_ = i64(kit.gI(4 * s + 1, n, 10, 4, 1)) if pk == 1 else f64(kit.gF(4 * s + 1, n, 10 if pk == 2 else 70, 1 if pk == 2 else 2, PE))
    cols = [("default_flag", fl), ("pd_logistic", pd_)] if sw == 0 else [("pd_logistic", pd_), ("default_flag", fl)]
    if xk % 2 == 1:
        cols.append(("credit_risk_score", f64(kit.gF(4 * s + 2, n, 30, 3, PE))))
    if xk >= 2:
        cols.append(("row_id", pl.Series([None if v is None else SP[v] for v in kit.gI(4 * s + 3, n, 10, 6, 0)], dtype=pl.String)))
    return pl.DataFrame([c.alias(nm) for nm, c in cols])


def thr(s):
    return kit.gF(4 * s + 5, 1, 85, 2, TH)[0]


LF = (f14.OB + ob("FC", FC) + ob("FW", FW) + ob("PE", PE) + ob("TH", TH) + f"let NS : List Nat := {NS}; "
      f"let SP : List String := [{', '.join(lt.lean_str(x) for x in SP)}]; "
      "let fk := fun (s : Nat) => (let a := (hsh s 11) % 10; if a == 5 || a == 6 then 1 else if a == 7 then 2 else "
      "if a == 9 then (if (hsh s 15) % 3 == 0 then 3 else 0) else 0 : Nat); "
      "let pk := fun (s : Nat) => (let b := (hsh s 12) % 8; if b == 6 then 1 else if b == 7 then 2 else 0 : Nat); "
      "let mkF := fun (s : Nat) => (let n := NS.getD ((hsh s 7) % 13).toNat 0; let xk := ((hsh s 13) % 4).toNat; "
      "let fl : Pl.Col Float := (if fk s == 1 then Pl.Col.int (gI (4 * s) n 10 4 1) else if fk s == 2 then Pl.Col.f64 (gF (4 * s) n 85 2 FW) "
      "else if fk s == 3 then Pl.Col.bool ((gI (4 * s) n 10 2 0).map (fun (o : Option Int) => o.map (fun (k : Int) => k == 1))) "
      "else Pl.Col.f64 (gF (4 * s) n 100 2 FC)); "
      "let pd : Pl.Col Float := (if pk s == 1 then Pl.Col.int (gI (4 * s + 1) n 10 4 1) else if pk s == 2 then Pl.Col.f64 (gF (4 * s + 1) n 10 1 PE) "
      "else Pl.Col.f64 (gF (4 * s + 1) n 70 2 PE)); "
      'let base : Pl.Frame Float := (if (hsh s 14) % 2 == 0 then [("default_flag", fl), ("pd_logistic", pd)] else [("pd_logistic", pd), ("default_flag", fl)]); '
      'let e1 : Pl.Frame Float := (if xk % 2 == 1 then [("credit_risk_score", Pl.Col.f64 (gF (4 * s + 2) n 30 3 PE))] else []); '
      'let e2 : Pl.Frame Float := (if xk >= 2 then [("row_id", Pl.Col.str ((gI (4 * s + 3) n 10 6 0).map (fun (o : Option Int) => o.map (fun (k : Int) => SP.getD k.toNat ""))))] else []); '
      "(base ++ e1 ++ e2 : Pl.Frame Float)); "
      "let thr := fun (s : Nat) => ((gF (4 * s + 5) 1 85 2 TH).headD none).getD 0.0; ")


def cls_cm(s, EX):
    return 99 if s in EX else 2 if flav(s)[1] == 3 else 0


CLS_CM = "let cls := fun (s : Nat) => (if EX.contains s then 99 else if fk s == 3 then 2 else 0 : Nat); "
MK_CM = 'let mk := fun (s : Nat) => (let F := mkF s; let r := confusion_metrics (thr s) "x" F; tR F ++ tR r.1 ++ tR r.2.1 ++ tR r.2.2); '
MK_TH = "let mk := fun (s : Nat) => (let F := mkF s; tR F ++ tR (metrics_run_03_thresholds F)); "


def pre_cm(F):
    return F.schema["default_flag"] in (pl.Float64, pl.Int64) and F.schema["pd_logistic"] in (pl.Float64, pl.Int64)


def tok_cm(s):
    F = frameF(s)
    t = thr(s)
    r = mc.confusion_metrics(t, "x", F)
    return cmp.tokens(cmp.canon_frame(F)) + [x for d in r for x in cmp.tokens(cmp.canon_frame(d))]


def tok_th(s):
    F = frameF(s)
    ns = dict(vars(mc))
    ns["logit_scored_valid"] = F
    ex(C03, ns)
    return cmp.tokens(cmp.canon_frame(F)) + cmp.tokens(cmp.canon_frame(ns["threshold_analysis"]))


# ------------------------------------------------------------------ step 05
ND = [0, 1, 1, 2, 3, 4, 5, 8, 3]
NM = [0, 1, 2, 3, 5, 10, 10, 12]
FV = [None, 0.0, 1.0, nan, inf, 2.0, -0.0, 1.0, 0.0]
DF = [None, nan, 0.0, 1.0, 2.0, 3.0, inf, -inf, 1e300, 0.5, None]
DFZ = DF + [-0.0, -0.0, -0.0]
BIG = 2 ** 41


def flav5(s):
    """(n, m, big counts, extra column, valid_exists, Float64 total_count (rejected), zeros family)."""
    z = s % 8 == 5
    return (ND[kit.hsh(s, 77) % 9], NM[kit.hsh(s, 78) % 8], kit.hsh(s, 79) % 10 == 0, kit.hsh(s, 80) % 3 == 0,
            kit.hsh(s, 81) % 4 != 0, (not z) and kit.hsh(s, 82) % 12 == 0, z)


def frames5(s):
    n, m, big, extra, ve, ftc, z = flav5(s)
    dd = pl.DataFrame({"default_flag": f64(kit.gF(5 * s, n, 100, 2, FV if s % 8 == 0 else FC))})
    tc = kit.gI(5 * s + 2, m, 8, 2 * BIG, BIG) if big else kit.gI(5 * s + 2, m, 8, 9, 2)
    cols = {"decile": i64(kit.gI(5 * s + 1, m, 6, 13, 0)),
            "total_count": f64([None if v is None else float(v) for v in tc]) if ftc else i64(tc),
            "defaults": f64(kit.gF(5 * s + 3, m, 80, 2, DFZ if z else DF))}
    if extra:
        cols["avg_pd"] = f64(kit.gF(5 * s + 4, m, 30, 2, DF))
    return dd, pl.DataFrame(cols), ve


def tables(best):
    sb = ", ".join(f"({'none' if k is None else f'some {k}'}, {lt.lean_str(v)})" for k, v in best.items())
    pf = ", ".join(f"({lt.lean_str(v)}, {cmp.fbits(float(v))})" for v in sorted({v for v in best.values() if v}))
    return f"let SB : List (Option UInt64 × String) := [{sb}]; let PF : List (String × UInt64) := [{pf}]; " + t14.SBPF


def run05(dd, da, ve, best):
    o_best = sc.sas_best

    def w_best(x, w):
        r = o_best(x, w)
        assert w == 8
        assert best.setdefault(None if x is None else cmp.fbits(float(x)), r) == r
        return r

    sc.sas_best = w_best
    try:
        ns = dict(vars(mc))
        ns.update(decile_data=dd, decile_analysis=da, valid_exists=ve)
        ex(C05, ns)
    finally:
        sc.sas_best = o_best
    return ns["cumulative_lift"]


NZ05 = ["cum_defaults", "cum_capture_rate", "cum_lift"]


def tok05(s, best, nz=False):
    dd, da, ve = frames5(s)
    out = run05(dd, da, ve, best)
    if nz:
        out = f14.nzp(out, NZ05)
    return cmp.tokens(t14.canon(dd)) + cmp.tokens(t14.canon(da)) + [1 if ve else 0] + cmp.tokens(t14.canon(out))


L5 = (f14.OB + ob("FC", FC) + ob("FV", FV) + ob("DF", DF) + ob("DFZ", DFZ) + f"let ND : List Nat := {ND}; let NM : List Nat := {NM}; "
      "let mk5 := fun (s : Nat) => (let n := ND.getD ((hsh s 77) % 9).toNat 0; let m := NM.getD ((hsh s 78) % 8).toNat 0; "
      "let z : Bool := s % 8 == 5; let ftc : Bool := !z && (hsh s 82) % 12 == 0; let ve : Bool := (hsh s 81) % 4 != 0; "
      'let dd : Pl.Frame Float := [("default_flag", Pl.Col.f64 (gF (5 * s) n 100 2 (if s % 8 == 0 then FV else FC)))]; '
      f"let tc : List (Option Int) := (if (hsh s 79) % 10 == 0 then gI (5 * s + 2) m 8 {2 * BIG} {BIG} else gI (5 * s + 2) m 8 9 2); "
      'let da0 : Pl.Frame Float := [("decile", Pl.Col.f64 ((gI (5 * s + 1) m 6 13 0).map (fun (o : Option Int) => o.map Float.ofInt))), '
      '("total_count", (if ftc then Pl.Col.f64 (tc.map (fun (o : Option Int) => o.map Float.ofInt)) else Pl.Col.int tc)), '
      '("defaults", Pl.Col.f64 (gF (5 * s + 3) m 80 2 (if z then DFZ else DF)))]; '
      'let da : Pl.Frame Float := (if (hsh s 80) % 3 == 0 then da0 ++ [("avg_pd", Pl.Col.f64 (gF (5 * s + 4) m 30 2 DF))] else da0); '
      "(dd, da, ve)); "
      "let mk := fun (s : Nat) => (let p := mk5 s; tR p.1 ++ tR p.2.1 ++ [if p.2.2 then 1 else 0] ++ tR (OUT (metrics_run_05_cumulative_lift sb pf p.1 p.2.1 p.2.2))); ")


def cls5(s, EX):
    f = flav5(s)
    return 99 if s in EX else 2 if f[5] else 3 if f[6] else 0


CLS5 = "let cls := fun (s : Nat) => (if EX.contains s then 99 else if (s % 8 != 5) && (hsh s 82) % 12 == 0 then 2 else if s % 8 == 5 then 3 else 0 : Nat); "
FAM = {0: "kept", 2: "rejected", 3: "kept zeros"}

BODY = "CH.map (fun (c : Nat × Nat × Nat) => dg (((List.range' c.1 c.2.1).filter (fun (s : Nat) => cls s == c.2.2)).flatMap mk))"


def build(name, unit, first, count, per, windows, tok, lets_of, cls, need_acc=False):
    """windows[class] divides `per`. tok(s, acc) -> tokens (raises: the seed goes to EX)."""
    s_ = Suite(name, generator=GENR)
    stat = {"generated": 0, "kept": 0, "rejected": 0, "dropped_rejected_raises": [], "raises_kept": [], "zeros": 0}
    for a in range(first, first + count, per):
        acc: dict = {}
        res, EX = {}, set()
        for seed in range(a, a + per):
            stat["generated"] += 1
            try:
                res[seed] = tok(seed, acc)
            except Exception as e:  # noqa: BLE001
                EX.add(seed)
                k = cls(seed, set())
                (stat["dropped_rejected_raises"] if k == 2 else stat["raises_kept"]).append(seed)
                print(f"[{name} seed {seed}] Python raises {type(e).__name__}: {str(e)[:120]} (class {k})")
        chunks, cases = [], []
        for k, w in windows.items():
            assert per % w == 0
            for lo in range(a, a + per, w):
                part = [x for x in range(lo, lo + w) if cls(x, EX) == k]
                if not part:
                    continue
                st = "rejected" if k == 2 else "kept"
                stat[st] += len(part)
                if k == 3:
                    stat["zeros"] += len(part)
                chunks.append(f"({lo}, {w}, {k})")
                cases.append((f"{FAM[k]} seeds {part[0]}..{part[-1]} ({len(part)})", unit,
                              cmp.digest([t for x in part for t in res[x]]), {"fz": st, "covers": len(part), "family": k}))
        ex_ = "let EX : List Nat := [" + ", ".join(str(x) for x in sorted(EX)) + "]; "
        s_.ints(ex_ + lets_of(acc) + f"let CH : List (Nat × Nat × Nat) := [{', '.join(chunks)}]; ", BODY, cases, gen=True, table=False)
    s_.write()
    return stat


# ------------------------------------------------------------------ real data (judge/scenarios/real_metrics, whole files)
SCEN = HERE.parents[3] / "judge" / "scenarios" / "real_metrics"
CA = None


def real_frames():
    """The real import (proc_import_csv, as run :103-104) and the locals of run after steps 01-04 (the real source
    from `roc_stats = sas_compat.roc_association(` to `# listing-only: PROC PRINT decile_analysis`)."""
    V = sc.proc_import_csv(SCEN / "risk_scores_validation.csv", guessingrows=20)
    i = next(k for k, l in enumerate(L) if "roc_stats = sas_compat.roc_association(" in l)
    j = next(k for k in range(i, len(L)) if "# listing-only: PROC PRINT decile_analysis" in L[k])
    ns = dict(vars(mc))
    ns.update(logit_scored_valid=V, valid_exists=V.height > 0)
    ex(compile(textwrap.dedent("".join(L[i:j])), f"mc:{i + 1}-{j}", "exec"), ns)
    return V, ns


B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
DEC = ("let hx := fun (c : Char) => (if c.toNat <= 57 then c.toNat - 48 else c.toNat - 87); "
       "let HX := fun (s : String) => (let cs := s.toList; (List.range (cs.length / 16)).map (fun (i : Nat) => "
       "some (Float.ofBits (((cs.drop (16 * i)).take 16).foldl (fun (a : Nat) (c : Char) => a * 16 + hx c) 0).toUInt64))); "
       "let FL := fun (s : String) => s.toList.flatMap (fun (c : Char) => (let v := (if c.toNat <= 90 then c.toNat - 65 else c.toNat - 71); "
       "(List.range 5).map (fun (j : Nat) => if (v / 2 ^ j) % 2 == 1 then some (1.0 : Float) else some 0.0))); ")


GAPDEC = ("let GAP := fun (s : String) (tail : Nat) => (let st := s.toList.foldl (fun (st : Nat × List (Option Float)) (c : Char) => "
          "(if c.toNat >= 97 then (st.1 * 26 + (c.toNat - 97), st.2) else (0, (some (1.0 : Float)) :: (List.replicate (st.1 * 26 + (c.toNat - 65)) "
          "(some (0.0 : Float)) ++ st.2)))) ((0 : Nat), ([] : List (Option Float))); (List.replicate tail (some (0.0 : Float)) ++ st.2).reverse); ")


def gaps(xs):
    """0/1 flags -> (text, tail): for each 1 the number of 0s before it (since the previous 1) in base 26, the last digit
    upper case ('A' + d), the others lower case ('a' + d); tail = the 0s after the last 1."""
    assert set(xs) <= {0.0, 1.0}
    out, g = [], 0
    for x in xs:
        if x == 1.0:
            ds = []
            while True:
                ds.append(g % 26)
                g //= 26
                if g == 0:
                    break
            ds.reverse()
            out.append("".join(chr(97 + d) for d in ds[:-1]) + chr(65 + ds[-1]))
            g = 0
        else:
            g += 1
    return "".join(out), g


def hexs(xs):
    return "".join(f"{cmp.fbits(x):016x}" for x in xs)


def flags32(xs):
    assert len(xs) % 5 == 0 and set(xs) <= {0.0, 1.0}
    return "".join(B32[sum((1 << j) for j in range(5) if xs[i + j] == 1.0)] for i in range(0, len(xs), 5))


def real_suite():
    V, ns = real_frames()
    Vs = ns["logit_scored_valid"]  # sorted by step 02 (the frame steps 03-05 read in run)
    assert Vs.height == 45000 and Vs["default_flag"].null_count() == 0 and Vs["pd_logistic"].null_count() == 0
    s_ = Suite("fz10c_real", generator=GENR)
    W = 60
    pds = Vs["pd_logistic"].to_list()
    starts = {"import order rows 0..": 0, "sorted last rows": ("s", 45000 - W)}
    for t in (0.3, 0.5, 0.7):  # sorted windows centred on thresholds of step 03
        k = next(i for i, p in enumerate(pds) if p >= t)
        starts[f"sorted around {t} (row {k})"] = ("s", max(0, k - W // 2))
    TT = TS + [u(0.5, 0), u(0.5, 1)]
    lets = DEC + ("let C := fun (F : Pl.Frame Float) (t : Float) => (let r := confusion_metrics t \"x\" F; dg (tR F ++ tR r.1 ++ tR r.2.1 ++ tR r.2.2)); "
                  f"let TT : List Float := [{', '.join(lt.lean_float(t) for t in TT)}]; ")
    cases, Fs = [], []
    for w, (lab, st) in enumerate(starts.items()):
        src, a = (Vs, st[1]) if isinstance(st, tuple) else (V, st)
        F = src.select("default_flag", "pd_logistic").slice(a, W)
        lets += (f"let F{w} : Pl.Frame Float := [(\"default_flag\", Pl.Col.f64 (FL {lt.lean_str(flags32(F['default_flag'].to_list()))})), "
                 f"(\"pd_logistic\", Pl.Col.f64 (HX {lt.lean_str(hexs(F['pd_logistic'].to_list()))}))]; ")
        Fs.append(f"F{w}")
        cases.append((f"real {lab} ({W} rows) input check", "input-check", cmp.digest(cmp.tokens(cmp.canon_frame(F))), {"fz": "kept"}))
        for t in TT:
            r = mc.confusion_metrics(t, "x", F)
            cases.append((f"real {lab} ({W} rows) confusion_metrics t={t!r}", UCM,
                          cmp.digest(cmp.tokens(cmp.canon_frame(F)) + [x for d in r for x in cmp.tokens(cmp.canon_frame(d))]), {"fz": "kept"}))
        n3 = dict(vars(mc))
        n3["logit_scored_valid"] = F
        ex(C03, n3)
        cases.append((f"real {lab} ({W} rows) step 03", U03, cmp.digest(cmp.tokens(cmp.canon_frame(F)) + cmp.tokens(cmp.canon_frame(n3["threshold_analysis"]))), {"fz": "kept"}))
    body = (f"[{', '.join(Fs)}].flatMap (fun (F : Pl.Frame Float) => [dg (tR F)] ++ TT.map (C F) ++ [dg (tR F ++ tR (metrics_run_03_thresholds F))])")
    s_.ints(lets, body, cases, gen=False, table=False)
    # step 05 on the whole real input: decile_data (45,000 rows; the unit reads default_flag only, asserted) and
    # decile_analysis (10 rows, all its columns), valid_exists true (as in run) and false
    dd_full, da = ns["decile_data"], ns["decile_analysis"]
    dd = dd_full.select("default_flag")
    best: dict = {}
    cases, body = [], []
    for ve in (True, False):
        o1 = run05(dd_full, da, ve, best)
        o2 = run05(dd, da, ve, {})
        assert t14.canon(o1) == t14.canon(o2)
        cases.append((f"real whole real_metrics step 05 valid_exists={ve}", U05,
                      cmp.digest(cmp.tokens(t14.canon(dd)) + cmp.tokens(t14.canon(da)) + cmp.tokens(t14.canon(o1))), {"fz": "kept"}))
        body.append(f"dg (tR dd ++ tR da ++ tR (metrics_run_05_cumulative_lift sb pf dd da {'true' if ve else 'false'}))")
    da_l = da.with_columns(pl.col("decile").cast(pl.Float64))
    gtxt, tail = gaps(dd["default_flag"].to_list())
    lets = (GAPDEC + tables(best) + f"let dd : Pl.Frame Float := [(\"default_flag\", Pl.Col.f64 (GAP {lt.lean_str(gtxt)} {tail}))]; "
            + lt.lean_frame_let("da", da_l))
    # transcription check of the input: the digest of decile_data's column as Lean decoded it (not a unit case)
    cases.append(("real whole real_metrics decile_data input check", "input-check", cmp.digest(cmp.tokens(t14.canon(dd))), {"fz": "kept"}))
    body.append("dg (tR dd)")
    s_.ints(lets, "[" + ", ".join(body) + "]", cases, gen=False, table=False)
    s_.write()


def main():
    first = 7_100_000
    cm = build("fz10c_cm", UCM, first, 2400, 2400, {0: 50, 2: 400}, lambda s, acc: tok_cm(s), lambda acc: LF + CLS_CM + MK_CM, cls_cm)
    th = build("fz10c_th", U03, first, 2400, 2400, {0: 50, 2: 400}, lambda s, acc: tok_th(s), lambda acc: LF + CLS_CM + MK_TH, cls_cm)
    lf = build("fz10c_lift", U05, first, 2600, 2600, {0: 50, 2: 200, 3: 200}, lambda s, acc: tok05(s, acc),
               lambda acc: tables(acc) + L5.replace("OUT (", "(") + CLS5, cls5)
    nz = build("fz10c_lift_nz", U05, first, 2600, 2600, {3: 200}, lambda s, acc: tok05(s, acc, nz=True),
               lambda acc: tables(acc) + f14.NZ + L5.replace("OUT (metrics_run_05_cumulative_lift sb pf p.1 p.2.1 p.2.2)", 'nz ["cum_defaults", "cum_capture_rate", "cum_lift"] (metrics_run_05_cumulative_lift sb pf p.1 p.2.1 p.2.2)') + CLS5, cls5)
    real_suite()
    for name, unit, st, note in [
        ("fz10c_cm", UCM, cm, "one case = one digest over the kept (or rejected) seeds of a window of 50 (400) seeds: input frame, confusion, "
         "conf_matrix, metrics of each; 0..45 rows; default_flag clean Float64 {null,0,1} / Int64 {-1..2,null} / wild Float64 (NaN, +-inf, 2, "
         "0.5, -1, -0.0, 1e300, random) / Boolean (rejected); pd_logistic Float64 70 % edges (null, NaN, +-inf, +-0, 1, 1e300, 1e-300, "
         "5e-324, 0.25, 2, -1, each of 0.3..0.7 and one ulp either side) / Int64 / random; columns in either order, extra Float64 and "
         "String columns; threshold 85 % from (0.3..0.7 and +-1 ulp, +-0, NaN, +-inf, 1, 5e-324, 2, -1, 0.45), else random"),
        ("fz10c_th", U03, th, "the same frames as fz10c_cm (seeds 7100000..), result of step 03 (five calls, concat); one case = one digest "
         "over the kept (rejected) seeds of a window of 50 (400)"),
        ("fz10c_lift", U05, lf, "one case = one digest over the seeds of one class in a window of 50 / 200 (decile_data, decile_analysis, "
         "valid_exists, cumulative_lift of each); decile_data 0..8 rows of {null,0,1}, one seed in 8 with NaN, +inf, 2, -0.0; decile_analysis 0..12 "
         "rows: decile 0..12 with nulls and duplicates, unsorted (Int64 in Python, Float64 in Lean: R-F2I); total_count -2..6 with nulls, one "
         "seed in 10 in [-2^41, 2^41); defaults from (null, NaN, 0, 1, 2, 3, +-inf, 1e300, 0.5) and 20 % random, one seed in 8 also -0.0 "
         "(family zeros); one seed in 3 an extra avg_pd column; valid_exists false one seed in 4; rejected = Float64 total_count; "
         "sas_best / float = lookup tables recorded from the real functions"),
    ]:
        (WORK / f"{name}.fuzz.json").write_text(json.dumps({"fuzzer": FUZZER, "generator": GENR, "blueprint": BP, "units": {unit: {
            "seeds": f"{first}..{first + st['generated'] - 1}", "generated": st["generated"], "kept": st["kept"],
            "python_raises_inside_precondition": st["raises_kept"], "note": note, "stat": st}}}, indent=1))
        print(name, {k: (v if not isinstance(v, list) else (len(v), v[:8])) for k, v in st.items()})
    print("nz", {k: (v if not isinstance(v, list) else (len(v), v[:8])) for k, v in nz.items()})
    for nm in ("fz10c_cm", "fz10c_th", "fz10c_lift", "fz10c_lift_nz", "fz10c_real"):
        c = json.loads((WORK / f"{nm}.inputs.json").read_text())
        print(nm, "inputs:", [len(i) for x in c for i in x["inputs"]], c[0]["item"], c[0]["decl"])


if __name__ == "__main__":
    main()
