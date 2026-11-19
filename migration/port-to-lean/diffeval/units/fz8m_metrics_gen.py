"""Fuzz 2026-11-18 (fifth port diff), by a non-author: def:metrics_run_06_psi (+ precondition, a training
credit_risk_score of text nulls) and def:metrics_run_07_calibration (+ precondition, a validation frame with no row).
(prefix fz8m: another fuzzer's fz7_* files live beside these; nothing here writes an fz7_ name)

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz8m_metrics_gen.py
      -> work/fz8m_psi.json / .inputs.json / .fuzz.json / .in<k>.txt, work/fz8m_cal.* (same)
  eval_decl each input on def:zz_carrier_e / zz_carrier_e (text exactly as in work/<suite>.in<k>.txt), save the
  outputs one per line as work/<suite>.out.txt; compare.py; fuzz_receipt.py

One seed s = one case, built INSIDE Lean from kit.hsh and mirrored here (kit.gF / kit.gI / kit.hsh).
PSI: training frame SZ[hsh(s,9001)%10] rows (0 rows: rejected class), validation SZV[hsh(s,9002)%12] rows (0 in 2 of 12:
header-only), column credit_risk_score by mode from hsh(s,9003)%8 / hsh(s,9004)%8: edge pool 60 %, six levels each exact / one
ulp either side with nulls (ties on every cut), forty levels, and (training only) a String column of nulls; with 1 in 2 the
frames also carry default_flag and pd_logistic (Float64) before the score, as the frames of `run` do.
CAL: rows NS[hsh(s,9101)%15], pd_logistic by mode hsh(s,9102)%5 (edge pool, grid k/8 with ties, random floats, all null,
constant 0.5), default_flag by mode hsh(s,9103)%4 (edge pool, 0/1, all null, 0/1 with nulls), credit_risk_score extra.
Expected: the real lines of metrics_calculation.py cut by marker text and executed on the same frames.
Classes: kept = the rendered precondition admits; rejected = Python returns and Lean is compared too.
"""
from __future__ import annotations

import json
import math
import struct
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402
from credit_risk import metrics_calculation as mc  # noqa: E402

WORK = HERE.parent / "work"
nan, inf = float("nan"), float("inf")
h = kit.hsh
u = math.nextafter
L = Path(mc.__file__).read_text().splitlines(keepends=True)


def cut(a, b, extra=0):
    i = next(k for k, ln in enumerate(L) if a in ln)
    j = next(k for k in range(i, len(L)) if b in L[k])
    return compile(textwrap.dedent("".join(L[i:j + 1 + extra])), f"mc:{i + 1}-{j + 1}", "exec")


S06 = cut("train_scores_sorted = ", 'otherwise(pl.lit("Significant change"))', 1)
S07 = cut("calibration_data = logit_scored_valid.with_columns(", '.sort("pred_bin", maintain_order=True)', 1)


def run(code, **env):
    ns = dict(vars(mc)); ns.update(env); exec(code, ns); return ns


def pre_rank(x, k, desc):
    nn = x.len() - x.null_count()
    for r in x.rank("average", descending=desc).to_list():
        if r is not None and not (-2**63 <= math.floor(r * float(k) / float(nn + 1)) < 2**63):
            return False
    return True


def dgf(df):
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def fb(bits):
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


# ------------------------------------------------------------------ PSI
SZ = [0, 1, 2, 3, 5, 9, 10, 11, 20, 37]
SZV = [0, 0, 1, 2, 3, 5, 9, 10, 11, 20, 37, 37]
E = [None, nan, inf, -inf, 0.0, -0.0, 1e300, -1e300, 1e-300, 5e-324, 700.0, u(700.0, inf), u(700.0, -inf), 650.0, 2.0**53, 1.0, 4.0]
X3 = [None, 0.0, 1.0]


def md(x):
    return 0 if x < 3 else 1 if x < 5 else 2 if x < 7 else 3


def col_py(s, n, m):
    if m == 0:
        return pl.Series("credit_risk_score", kit.gF(s, n, 60, 3, E), dtype=pl.Float64, nan_to_null=False)
    if m == 1:
        a, b = kit.gI(s, n, 10, 6, 0), kit.gI(s + 1, n, 0, 3, 0)
        return pl.Series("credit_risk_score", [None if x is None else
                                               fb(b4.raw(float(600 + 10 * x)) + y - 1) for x, y in zip(a, b)], dtype=pl.Float64)
    if m == 2:
        return pl.Series("credit_risk_score", [None if x is None else float(500 + 7 * x) for x in kit.gI(s, n, 5, 40, 0)], dtype=pl.Float64)
    return pl.Series("credit_risk_score", [None] * n, dtype=pl.String)


def fr_py(s, n, m):
    cs = [col_py(s, n, m)]
    if h(s, 9005) % 2 == 0:
        cs = [pl.Series("default_flag", kit.gF(s + 7, n, 30, 1, X3), dtype=pl.Float64, nan_to_null=False),
              pl.Series("pd_logistic", kit.gF(s + 8, n, 30, 1, X3), dtype=pl.Float64, nan_to_null=False)] + cs
    return pl.DataFrame(cs)


def psi_args(s):
    nt, nv = SZ[h(s, 9001) % 10], SZV[h(s, 9002) % 12]
    mt, mv = md(h(s, 9003) % 8), md(h(s, 9004) % 8)
    if mv == 3:
        mv = 2
    return fr_py(s, nt, mt), fr_py(s + 500000, nv, mv), (nt, nv, mt, mv)


def psi_one(s):
    t, v, info = psi_args(s)
    nt = info[0]
    cls = 2 if (nt == 1 and info[2] == 3) else (0 if nt > 0 else 1)
    try:
        ns = run(S06, logit_scored_train=t, logit_scored_valid=v)
    except Exception as ex:  # noqa: BLE001
        return cls, None, f"{type(ex).__name__}: {ex}", info
    return cls, cmp.digest(cmp.tokens(cmp.canon_frame(ns["psi_calculation"])) + cmp.tokens(cmp.canon_frame(ns["psi_summary"]))), "", info


EL = "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in E) + "]"
PSI_LETS = (
    b4.W + f"let SZ : List Nat := {SZ}; let SZV : List Nat := {SZV}; let E : List (Option Float) := {EL}; "
    "let X3 : List (Option Float) := [none, some 0.0, some 1.0]; "
    "let MD := fun (x : Nat) => if x < 3 then (0 : Nat) else if x < 5 then 1 else if x < 7 then 2 else 3; "
    "let COL := fun (s n m : Nat) => (if m == 0 then Pl.Col.f64 (gF s n 60 3 E) "
    "else if m == 1 then Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some a, some b => "
    "some (Float.ofBits ((Float.ofInt (600 + 10 * a)).toBits + b.toNat.toUInt64 - 1)) | _, _ => none : Option Float)) (gI s n 10 6 0) (gI (s + 1) n 0 3 0)) "
    "else if m == 2 then Pl.Col.f64 ((gI s n 5 40 0).map (fun (o : Option Int) => o.map (fun (a : Int) => Float.ofInt (500 + 7 * a)))) "
    "else Pl.Col.str (List.replicate n (none : Option String)) : Pl.Col Float); "
    "let FR := fun (s n m : Nat) => (if (hsh s 9005).toNat % 2 == 0 then "
    "[(\"default_flag\", Pl.Col.f64 (gF (s + 7) n 30 1 X3)), (\"pd_logistic\", Pl.Col.f64 (gF (s + 8) n 30 1 X3)), (\"credit_risk_score\", COL s n m)] "
    "else [(\"credit_risk_score\", COL s n m)] : Pl.Frame Float); "
    "let ONE := fun (s : Nat) => let nt := SZ.getD ((hsh s 9001).toNat % 10) 0; let nv := SZV.getD ((hsh s 9002).toNat % 12) 0; "
    "let mt := MD ((hsh s 9003).toNat % 8); let mv0 := MD ((hsh s 9004).toNat % 8); let mv := if mv0 == 3 then 2 else mv0; "
    "let r := metrics_run_06_psi (FR s nt mt) (FR (s + 500000) nv mv); "
    "((if nt == 1 && mt == 3 then 2 else if nt > 0 then 0 else 1 : Nat), dg (tR r.1 ++ tR r.2)); ")


def gen_psi(S0=70000, BLOCK=3000, NBLOCK=1):
    st = Suite("fz8m_psi")
    st.item, st.decl = "def:zz_carrier_e", "zz_carrier_e"
    gen = kept = rej = strn = emptyv = kn1 = 0
    raised = []
    for b in range(NBLOCK):
        s0 = S0 + b * BLOCK
        dig = {0: [], 1: [], 2: []}
        for s in range(s0, s0 + BLOCK):
            cls, d, msg, (nt, nv, mt, mv) = psi_one(s)
            gen += 1
            if d is None:
                raised.append((s, cls, msg))
                continue
            dig[cls].append(d)
            if cls in (0, 2):
                strn += mt == 3
                emptyv += nv == 0
        kept += len(dig[0]); rej += len(dig[1]); kn1 += len(dig[2])
        assert not any(c == 0 for _, c, _ in raised), raised[:3]
        body = (f"(let RS := (List.range {BLOCK}).map (fun (i : Nat) => ONE ({s0} + i)); "
                "[0, 1, 2].map (fun (c : Nat) => W ((RS.filter (fun (p : Nat × Int) => p.1 == c)).map (fun (p : Nat × Int) => p.2))))")
        rng = f"seeds {s0}..{s0 + BLOCK - 1}"
        st.ints(PSI_LETS, body, [
            (f"{rng}: kept ({len(dig[0])})", "metrics_run_06_psi", b4.w(dig[0]), {"fz": "kept", "covers": len(dig[0])}),
            (f"{rng}: rejected, training frame without rows ({len(dig[1])})", "metrics_run_06_psi", b4.w(dig[1]), {"fz": "rejected", "covers": len(dig[1])}),
            (f"{rng}: kept, one training row of text null ({len(dig[2])}): KNOWN DIFFERENCE, see note", "metrics_run_06_psi", b4.w(dig[2]), {"fz": "kept", "covers": len(dig[2]), "expect_diff": True, "note": "Pl.Expr.lt of a Null literal and a one-row String column is an empty column in the prelude, a one-row column in polars"}),
        ], gen=True)
    st.write()
    for i, inp in enumerate(st.inputs):
        (WORK / f"fz8m_psi.in{i}.txt").write_text(inp["text"])
    (WORK / "fz8m_psi.fuzz.json").write_text(json.dumps({
        "fuzzer": "fuzzer-metrics-06-07-fifth", "generator": "diffeval/units/fz8m_metrics_gen.py",
        "blueprint": "5365851c-5549-44b7-9207-4bd4c422031d",
        "units": {"metrics_run_06_psi": {
            "seeds": f"{S0}..{S0 + NBLOCK * BLOCK - 1}", "generated": gen, "kept": kept,
            "python_raises_inside_precondition": [s for s, c, _ in raised if c == 0],
            "note": f"kept class = precondition admits and not (one training row of text nulls); that case ({kn1} inputs) is its own case marked expect_diff. Text-null training inputs in all: {strn}, with a validation frame of no row: {emptyv}; "
                    f"rejected (no training row) returned by Python and compared too: {rej}; Python raised on {len(raised)} (not sent)"}}}))
    print(f"psi: generated {gen}, kept {kept}, rejected {rej}, text-null train {strn}, empty valid {emptyv}, raised {len(raised)}")


# ------------------------------------------------------------------ CALIBRATION
NS = [0, 1, 2, 3, 4, 5, 8, 9, 10, 13, 19, 20, 21, 24, 40]
PE = [None, nan, inf, -inf, 0.0, -0.0, 0.5, u(0.5, 0), u(0.5, 1), 1.0, 1e300, 5e-324, 0.25, 0.75, -1.0, 2.0]
YE = [None, nan, 0.0, 1.0, -0.0, 2.0, 0.5]


def pd_py(s, n, m):
    if m == 0:
        return kit.gF(s, n, 70, 2, PE)
    if m == 1:
        return [None if a is None else float(a) / 8.0 for a in kit.gI(s, n, 10, 9, 0)]
    if m == 2:
        return kit.gF(s, n, 0, 3, PE)
    if m == 3:
        return [None] * n
    return [0.5] * n


def y_py(s, n, m):
    if m == 0:
        return kit.gF(s, n, 40, 1, YE)
    if m == 1:
        return [None if a is None else float(a) for a in kit.gI(s, n, 0, 2, 0)]
    if m == 2:
        return [None] * n
    return [None if a is None else float(a) for a in kit.gI(s, n, 10, 2, 0)]


def cal_frame(s):
    n = NS[h(s, 9101) % 15]
    pm, ym = h(s, 9102) % 5, h(s, 9103) % 4
    return pl.DataFrame({
        "default_flag": pl.Series(y_py(s + 1, n, ym), dtype=pl.Float64, nan_to_null=False),
        "pd_logistic": pl.Series(pd_py(s + 2, n, pm), dtype=pl.Float64, nan_to_null=False),
        "credit_risk_score": pl.Series(kit.gF(s + 3, n, 30, 1, X3), dtype=pl.Float64, nan_to_null=False)}), (n, pm, ym)


def cal_one(s):
    df, info = cal_frame(s)
    cls = 0 if pre_rank(df["pd_logistic"], 20, False) else 1
    try:
        ns = run(S07, logit_scored_valid=df)
    except Exception as ex:  # noqa: BLE001
        return cls, None, f"{type(ex).__name__}: {ex}", info
    # R-F2I: the Lean keeps the Int64 pred_bin in alpha (a Float64 column of integral values), by the rulebook;
    # the Python Int64 column is cast to Float64 here so that every other column and every bin value is compared bit for bit
    return cls, dgf(ns["calibration_plot"].with_columns(pl.col("pred_bin").cast(pl.Float64))), "", info


PEL = "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in PE) + "]"
YEL = "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in YE) + "]"
CAL_LETS = (
    b4.W + f"let NS : List Nat := {NS}; let PE : List (Option Float) := {PEL}; let YE : List (Option Float) := {YEL}; "
    "let X3 : List (Option Float) := [none, some 0.0, some 1.0]; "
    "let PD := fun (s n m : Nat) => (if m == 0 then gF s n 70 2 PE else if m == 1 then (gI s n 10 9 0).map (fun (o : Option Int) => o.map (fun (a : Int) => Float.ofInt a / 8.0)) "
    "else if m == 2 then gF s n 0 3 PE else if m == 3 then List.replicate n (none : Option Float) else List.replicate n (some (0.5 : Float)) : List (Option Float)); "
    "let YY := fun (s n m : Nat) => (if m == 0 then gF s n 40 1 YE else if m == 1 then (gI s n 0 2 0).map (fun (o : Option Int) => o.map (fun (a : Int) => Float.ofInt a)) "
    "else if m == 2 then List.replicate n (none : Option Float) else (gI s n 10 2 0).map (fun (o : Option Int) => o.map (fun (a : Int) => Float.ofInt a)) : List (Option Float)); "
    "let ONE := fun (s : Nat) => let n := NS.getD ((hsh s 9101).toNat % 15) 0; let pm := (hsh s 9102).toNat % 5; let ym := (hsh s 9103).toNat % 4; "
    "let fr : Pl.Frame Float := [(\"default_flag\", Pl.Col.f64 (YY (s + 1) n ym)), (\"pd_logistic\", Pl.Col.f64 (PD (s + 2) n pm)), "
    "(\"credit_risk_score\", Pl.Col.f64 (gF (s + 3) n 30 1 X3))]; "
    "(0, dg (tR (metrics_run_07_calibration fr))); ")


def gen_cal(S0=80000, BLOCK=3000, NBLOCK=1):
    st = Suite("fz8m_cal")
    st.item, st.decl = "def:zz_carrier_e", "zz_carrier_e"
    gen = kept = rej = empty = 0
    raised = []
    for b in range(NBLOCK):
        s0 = S0 + b * BLOCK
        res = [cal_one(s) for s in range(s0, s0 + BLOCK)]
        gen += BLOCK
        for s, (cls, d, msg, (n, pm, ym)) in zip(range(s0, s0 + BLOCK), res):
            if d is None:
                raised.append((s, cls, msg))
            elif cls == 0:
                kept += 1; empty += n == 0
            else:
                rej += 1
        assert not any(c == 0 for _, c, _ in raised), raised[:3]
        ok = [s for s, r in zip(range(s0, s0 + BLOCK), res) if r[1] is not None]
        ssx = f"(List.range {BLOCK}).map (fun (i : Nat) => {s0} + i)" if len(ok) == BLOCK else str(ok)
        body = f"(let SS : List Nat := {ssx}; [W (SS.map (fun (s : Nat) => (ONE s).2))])"
        nk = sum(1 for r in res if r[1] is not None and r[0] == 0)
        st.ints(CAL_LETS, body, [
            (f"seeds {s0}..{s0 + BLOCK - 1}: the {len(ok)} on which Python returns", "metrics_run_07_calibration",
             b4.w([r[1] for r in res if r[1] is not None]), {"fz": "kept", "covers": nk}),
        ], gen=True)
    st.write()
    for i, inp in enumerate(st.inputs):
        (WORK / f"fz8m_cal.in{i}.txt").write_text(inp["text"])
    (WORK / "fz8m_cal.fuzz.json").write_text(json.dumps({
        "fuzzer": "fuzzer-metrics-06-07-fifth", "generator": "diffeval/units/fz8m_metrics_gen.py",
        "blueprint": "5365851c-5549-44b7-9207-4bd4c422031d",
        "units": {"metrics_run_07_calibration": {
            "seeds": f"{S0}..{S0 + NBLOCK * BLOCK - 1}", "generated": gen, "kept": kept,
            "python_raises_inside_precondition": [s for s, c, _ in raised if c == 0],
            "note": f"kept with no row: {empty}; one case = fold of the digests over the seeds of a block on which Python returns "
                    f"({rej} rejected by the proc_rank_groups clause, Python returned, folded in too); Python raised on {len(raised)} (not sent)"}}}))
    print(f"cal: generated {gen}, kept {kept}, rejected-returned {rej}, empty {empty}, raised {len(raised)} {raised[:2]}")


if __name__ == "__main__":
    gen_psi()
    gen_cal()
