"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md), by port-translator-12, reviewer of T14:
  def:metrics_run_04_deciles          credit_risk/metrics_calculation.py:214-283   suite fz_dec
  def:metrics_run_05_cumulative_lift  credit_risk/metrics_calculation.py:287-321   suite fz_lift

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t14_gen.py
  (eval_decl every input of work/fz_dec.inputs.json and work/fz_lift.inputs.json on def:zz_carrier_m)
  python3 diffeval/fuzz_collect.py 12 fz_dec fz_lift
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/fz_dec.json diffeval/work/fz_dec.out.txt
  python3 diffeval/fuzz_receipt.py fz_dec fz_lift

Inputs are built inside Lean from the seed with kit.GEN (gF, gI, hsh) and mirrored here with
kit.gF / kit.gI / kit.hsh. One case = one digest over the token streams of about 50 seeds (`covers`):
for each seed the input frame(s) and the result frame(s), so an input that is not the same bit for
bit on both sides fails the case too. Expected values: the source lines of the step executed
verbatim with the module's globals (t14_gen.run_slice / run05), on the mirrored frames.

Step 04, one seed s: n = NS[hsh(s, 77) % 16] rows (0 once in 16);
  default_flag = gF(3s, n, ..) from the clean pool {null, 0, 1} (always the pool), or when s % 4 == 0
  from the wild pool (null, 0, 1, NaN, +inf, -inf, 2, 0.5, -1, -0.0, 1e300) with 15 % random floats;
  pd_logistic = gF(3s + 1, n, 70 or 30 % pool, ..) from the pool PD (null, NaN, +-inf, 0, 0.5 and one
  ulp either side, 0.25, 0.75, 1, 0.1, 1e300, 1e-300, the smallest subnormal), which gives ties and
  empty deciles; when s % 8 == 3 the pool also holds -0.0 (the recorded prelude limit on min / max
  of zeros of both signs can then show: such seeds are their own cases, family "zeros").
Step 05, one seed s: decile_data has n = ND[hsh(s, 77) % 8] rows (0 once in 8), default_flag from
  the clean pool or, when s % 8 == 0, from (null, 0, 1, NaN, +inf, 2, -0.0), always the pool, so that
  the lookup tables of sas_best / float stay short; decile_analysis has m = NM[hsh(s, 78) % 8] rows
  (0, 1, 2, 3, 5, 10, 10, 12): decile = gI in 0..12 with 6 % null (duplicates, unsorted; Int64 in
  Python, Float64 in Lean, R-F2I), total_count = gI in -2..6 with 8 % null, defaults = gF from
  (null, NaN, 0, 1, 2, 3, +-inf, 1e300, 0.5) with 20 % random floats; when s % 8 == 5 the pool also holds
  -0.0 (family "zeros").
Suites fz_dec_nz / fz_lift_nz: the seeds of the family "zeros" again, with -0.0 replaced by 0.0 in
  min_pd, max_pd (step 04) and in cum_defaults, cum_capture_rate, cum_lift (step 05) on both sides.

Preconditions, rendered in Python from the Lean text of the _precond items:
  metrics_run_04_deciles_precond: distinct names and equal lengths (true by construction); height > 0
    (`df.height > 0`); Float64 default_flag and pd_logistic (dtype test); proc_rank_groups_precond
    pd 10 true: 10 is finite as a float, and floor(rank * 10 / (non-null count + 1)) lies in the
    Int64 range for every non-null rank (computed with polars rank("average", descending=True)).
  metrics_run_05_cumulative_lift_precond: distinct names, equal lengths (by construction);
    decile_data.height > 0; Float64 default_flag; decile Float64 in Lean = Int64 in Python (R-F2I,
    by construction); defaults Float64; total_count Int64 (dtype tests).
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
_argv, sys.argv = sys.argv, [sys.argv[0]]

import t14_gen as t14  # noqa: E402  (sets the carrier def:zz_carrier_m)

import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import WORK, Suite  # noqa: E402

nan, inf = float("nan"), float("inf")
U04, U05 = "metrics_run_04_deciles", "metrics_run_05_cumulative_lift"
SUB = 5e-324
NULLBITS = 7  # marker of a null in the pools (the float with bits 7 is not used)

FC = [None, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
FW = [None, 0.0, 1.0, nan, inf, -inf, 2.0, 0.5, -1.0, -0.0, 1e300, 1.0, 0.0]
PD = [None, nan, inf, -inf, 0.0, 0.5, math.nextafter(0.5, 1.0), math.nextafter(0.5, 0.0), 0.25, 0.75, 1.0, 0.1, 0.1, 1e300, 1e-300, SUB]
PZ = PD + [-0.0, -0.0, 0.0]
NS = [0, 1, 1, 2, 2, 3, 4, 5, 7, 10, 11, 13, 20, 24, 37, 60]
FV = [None, 0.0, 1.0, nan, inf, 2.0, -0.0, 1.0, 0.0]
DF = [None, nan, 0.0, 1.0, 2.0, 3.0, inf, -inf, 1e300, 0.5, None]
DFZ = DF + [-0.0, -0.0, -0.0]
ND = [1, 1, 2, 3, 4, 5, 3, 0]
NM = [0, 1, 2, 3, 5, 10, 10, 12]


def bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def pool(name: str, E: list) -> str:
    return f"let {name} := ob [{', '.join(str(NULLBITS) if x is None else str(bits(x)) for x in E)}]; "


OB = "let ob := fun (v : List Nat) => v.map (fun (b : Nat) => if b == 7 then (none : Option Float) else some (Float.ofBits b.toUInt64)); "
# a case = the seeds of one class inside a window (start, length, class); the class of a seed is
# computed inside Lean by `cls` (9 = rejected by the precondition: no row)
# nz names frame: -0.0 replaced by 0.0 in the named Float64 columns (the suites fz_*_nz: evidence that the
# differences of the family "zeros" are signs of zero in those columns and nothing else)
NZ = ("let nz := fun (names : List String) (fr : Pl.Frame Float) => (fr.map (fun (p : String × Pl.Col Float) => "
      "if names.contains p.1 then (p.1, (match p.2 with | .f64 v => Pl.Col.f64 (v.map (fun (o : Option Float) => "
      "o.map (fun (x : Float) => if x == 0.0 then 0.0 else x))) | c => c : Pl.Col Float)) else p) : Pl.Frame Float); ")
NZ04, NZ05 = ["min_pd", "max_pd"], ["cum_defaults", "cum_capture_rate", "cum_lift"]


def nzp(df: pl.DataFrame, names: list[str]) -> pl.DataFrame:
    return df.with_columns([pl.when(pl.col(c) == 0.0).then(0.0).otherwise(pl.col(c)).alias(c) for c in names])


BODY = ("CH.map (fun (c : Nat × Nat × Nat) => dg (((List.range' c.1 c.2.1).filter (fun (s : Nat) => cls s == c.2.2)).flatMap mk))")
L04 = (OB + pool("FC", FC) + pool("FW", FW) + pool("PD", PD) + pool("PZ", PZ) +
       f"let NS : List Nat := {NS}; "
       "let mk := fun (s : Nat) => (let n := NS.getD ((hsh s 77) % 16).toNat 0; "
       "let fl := if s % 4 == 0 then gF (3 * s) n 85 2 FW else gF (3 * s) n 100 2 FC; "
       "let pd := gF (3 * s + 1) n (if s % 3 == 0 then 30 else 70) 3 (if s % 8 == 3 then PZ else PD); "
       "let fr : Pl.Frame Float := [(\"default_flag\", Pl.Col.f64 fl), (\"pd_logistic\", Pl.Col.f64 pd)]; "
       "let r := metrics_run_04_deciles fr; tR fr ++ tR r.1 ++ tR r.2); "
       "let cls := fun (s : Nat) => if NS.getD ((hsh s 77) % 16).toNat 0 == 0 then 9 else if s % 8 == 3 then 2 else if s % 4 == 0 then 1 else 0; ")


def cls04(s: int) -> int:
    return 9 if NS[kit.hsh(s, 77) % 16] == 0 else 2 if s % 8 == 3 else 1 if s % 4 == 0 else 0


def cls05(s: int) -> int:
    return 9 if ND[kit.hsh(s, 77) % 8] == 0 else 2 if s % 8 == 5 else 1 if s % 8 == 0 else 0


def f64(v: list) -> pl.Series:
    return pl.Series(v, dtype=pl.Float64, nan_to_null=False)


def gen04(s: int) -> pl.DataFrame:
    n = NS[kit.hsh(s, 77) % 16]
    fl = kit.gF(3 * s, n, 85, 2, FW) if s % 4 == 0 else kit.gF(3 * s, n, 100, 2, FC)
    pd_ = kit.gF(3 * s + 1, n, 30 if s % 3 == 0 else 70, 3, PZ if s % 8 == 3 else PD)
    return pl.DataFrame({"default_flag": f64(fl), "pd_logistic": f64(pd_)})


def pre04(df: pl.DataFrame) -> bool:
    if df.height == 0 or df.schema["default_flag"] != pl.Float64 or df.schema["pd_logistic"] != pl.Float64:
        return False
    x = df.get_column("pd_logistic")
    nn = x.len() - x.null_count()
    for r in x.rank("average", descending=True).to_list():
        if r is not None:
            g = math.floor(r * 10.0 / float(nn + 1))
            if not (-(2**63) <= g < 2**63):
                return False
    return True


L04NZ = (NZ + L04).replace("tR fr ++ tR r.1 ++ tR r.2)", 'tR fr ++ tR r.1 ++ tR (nz ["min_pd", "max_pd"] r.2))')
assert L04NZ != NZ + L04


def tok04(s: int, nz: bool = False) -> tuple[str, list[int] | None]:
    """-> (status, tokens): status kept / rejected / raises-kept / raises-rejected."""
    df = gen04(s)
    ok = pre04(df)
    try:
        ns = t14.run_slice(t14.S04, {"logit_scored_valid": df})
    except Exception as e:  # noqa: BLE001
        print(f"[04 seed {s}] Python raises {type(e).__name__}: {str(e)[:100]} (precondition {'admits' if ok else 'rejects'})")
        return ("raises-kept" if ok else "raises-rejected"), None
    da = nzp(ns["decile_analysis"], NZ04) if nz else ns["decile_analysis"]
    toks = cmp.tokens(t14.canon(df)) + cmp.tokens(t14.canon(ns["decile_data"])) + cmp.tokens(t14.canon(da))
    return ("kept" if ok else "rejected"), toks


# ---------------------------------------------------------------- step 05
def l05(tables: str, nz: bool = False) -> str:
    out = "tR (metrics_run_05_cumulative_lift sb pf dd da)"
    lets = l05_(tables)
    assert out in lets
    return (NZ + lets.replace(out, 'tR (nz ["cum_defaults", "cum_capture_rate", "cum_lift"] (metrics_run_05_cumulative_lift sb pf dd da))')) if nz else lets


def l05_(tables: str) -> str:
    return (OB + pool("FC", FC) + pool("FV", FV) + pool("DF", DF) + pool("DFZ", DFZ) +
            f"let ND : List Nat := {ND}; let NM : List Nat := {NM}; "
            f"let T : List (Option UInt64 × String) × List (String × UInt64) := {tables}; let SB := T.1; let PF := T.2; "
            + t14.SBPF +
            "let mk := fun (s : Nat) => (let n := ND.getD ((hsh s 77) % 8).toNat 0; let m := NM.getD ((hsh s 78) % 8).toNat 0; "
            "let dd : Pl.Frame Float := [(\"default_flag\", Pl.Col.f64 (gF (5 * s) n 100 2 (if s % 8 == 0 then FV else FC)))]; "
            "let da : Pl.Frame Float := [(\"decile\", Pl.Col.f64 ((gI (5 * s + 1) m 6 13 0).map (fun (o : Option Int) => o.map Float.ofInt))), "
            "(\"total_count\", Pl.Col.int (gI (5 * s + 2) m 8 9 2)), (\"defaults\", Pl.Col.f64 (gF (5 * s + 3) m 80 2 (if s % 8 == 5 then DFZ else DF)))]; "
            "tR dd ++ tR da ++ tR (metrics_run_05_cumulative_lift sb pf dd da)); "
            "let cls := fun (s : Nat) => if ND.getD ((hsh s 77) % 8).toNat 0 == 0 then 9 else if s % 8 == 5 then 2 else if s % 8 == 0 then 1 else 0; ")


def tables(best: dict) -> str:
    """(SB, PF): sas_best(x, 8) by the bits of x, float(text) by the text; from the real functions."""
    sb = ", ".join(f"({'none' if k is None else f'some {k}'}, {t14.lt.lean_str(v)})" for k, v in best.items())
    pf = ", ".join(f"({t14.lt.lean_str(v)}, {cmp.fbits(float(v))})" for v in sorted({v for v in best.values() if v}))
    return f"([{sb}], [{pf}])"


def gen05(s: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    n, m = ND[kit.hsh(s, 77) % 8], NM[kit.hsh(s, 78) % 8]
    dd = pl.DataFrame({"default_flag": f64(kit.gF(5 * s, n, 100, 2, FV if s % 8 == 0 else FC))})
    da = pl.DataFrame({"decile": pl.Series(kit.gI(5 * s + 1, m, 6, 13, 0), dtype=pl.Int64),
                       "total_count": pl.Series(kit.gI(5 * s + 2, m, 8, 9, 2), dtype=pl.Int64),
                       "defaults": f64(kit.gF(5 * s + 3, m, 80, 2, DFZ if s % 8 == 5 else DF))})
    return dd, da


def pre05(dd: pl.DataFrame, da: pl.DataFrame) -> bool:
    return (dd.height > 0 and dd.schema["default_flag"] == pl.Float64 and da.schema["decile"] == pl.Int64
            and da.schema["defaults"] == pl.Float64 and da.schema["total_count"] == pl.Int64)


def tok05(s: int, best: dict, nz: bool = False) -> tuple[str, list[int] | None]:
    dd, da = gen05(s)
    ok = pre05(dd, da)
    try:
        out, b = t14.run05(dd, da)
    except Exception as e:  # noqa: BLE001
        print(f"[05 seed {s}] Python raises {type(e).__name__}: {str(e)[:100]} (precondition {'admits' if ok else 'rejects'})")
        return ("raises-kept" if ok else "raises-rejected"), None
    for k, v in b.items():
        assert best.setdefault(k, v) == v
    if nz:
        out = nzp(out, NZ05)
    return ("kept" if ok else "rejected"), cmp.tokens(t14.canon(dd)) + cmp.tokens(t14.canon(da)) + cmp.tokens(t14.canon(out))


# ---------------------------------------------------------------- suites
FAM = {0: "", 1: "wild flags", 2: "zeros", 9: "no row"}


def build(name: str, unit: str, first: int, count: int, per_input: int, windows: dict[int, int], tok, lets, cls) -> dict:
    """tok(s, acc) -> (status, tokens); lets(acc) -> Lean lets of one input; cls(s) -> class of the seed
    (mirror of the Lean `cls`); windows[class] = length of the seed window of one case of that class."""
    s = Suite(name)
    stat = {"kept": 0, "rejected": 0, "raises-kept": [], "raises-rejected": 0}
    for a in range(first, first + count, per_input):
        acc: dict = {}
        res: dict[int, tuple[str, list[int]]] = {}
        end = min(a + per_input, first + count)
        for seed in range(a, end):
            st, toks = tok(seed, acc)
            assert toks is not None, (seed, st, "Python raises: give the Lean an exclusion list")
            assert (st == "rejected") == (cls(seed) == 9), (seed, st)
            stat[st] += 1
            res[seed] = (st, toks)
        chunks, cases = [], []
        for k, w in windows.items():
            for lo in range(a, end, w):
                # a window that does not divide the block runs over its end: those seeds are digested here
                # too (and again in the next block, where they are counted); `covers` counts the seeds of
                # this block only
                part = [x for x in range(lo, lo + w) if cls(x) == k]
                if not [x for x in part if x < end]:
                    continue
                for x in part:
                    if x not in res:
                        res[x] = tok(x, acc)
                st = "rejected" if k == 9 else "kept"
                chunks.append(f"({lo}, {w}, {k})")
                cases.append((f"{st}{' ' + FAM[k] if FAM[k] else ''} seeds {part[0]}..{part[-1]} ({len(part)})", unit,
                              cmp.digest([t for x in part for t in res[x][1]]),
                              {"fz": st, "covers": len([x for x in part if x < end])}))
        s.ints(lets(acc) + f"let CH : List (Nat × Nat × Nat) := [{', '.join(chunks)}]; ", BODY, cases, gen=True, table=False)
    s.write()
    return stat


def main() -> None:
    first, count = 1000, 2400
    st4 = build("fz_dec", U04, first, count, 800, {0: 80, 1: 200, 2: 400, 9: 800}, lambda s, acc: tok04(s), lambda acc: L04, cls04)
    st5 = build("fz_lift", U05, first, count, 600, {0: 70, 1: 300, 2: 300, 9: 300}, tok05, lambda acc: l05(tables(acc)), cls05)
    # the family "zeros" again, with the sign of zero cleared in the named columns on both sides
    # (step 05: also the rejected seeds, whose decile_analysis can hold -0.0 as well)
    build("fz_dec_nz", U04, first, count, 2400, {2: 400}, lambda s, acc: tok04(s, nz=True), lambda acc: L04NZ, cls04)
    build("fz_lift_nz", U05, first, count, 1200, {2: 300, 9: 600}, lambda s, acc: tok05(s, acc, nz=True),
          lambda acc: l05(tables(acc), nz=True), cls05)
    print("04", {k: (v if not isinstance(v, list) else v[:10]) for k, v in st4.items()})
    print("05", {k: (v if not isinstance(v, list) else v[:10]) for k, v in st5.items()})
    seeds = f"{first}..{first + count - 1}"
    def limit(name: str, text: str) -> str | None:
        """`text` when the evidence holds in the compared results on disk: every differing kept case of
        <name> is of the family zeros, and every case of <name>_nz (the same seeds with the sign of zero
        cleared in the named columns on both sides) is equal. None otherwise (no result yet, or stale)."""
        try:
            cs, rs = json.loads((WORK / f"{name}.json").read_text())["cases"], json.loads((WORK / f"{name}.result.json").read_text())
            cn, rn = json.loads((WORK / f"{name}_nz.json").read_text())["cases"], json.loads((WORK / f"{name}_nz.result.json").read_text())
        except FileNotFoundError:
            return None
        if [c["id"] for c in cs] != [r["id"] for r in rs] or [c["id"] for c in cn] != [r["id"] for r in rn]:
            return None
        bad = [c["id"] for c, r in zip(cs, rs) if c["fz"] == "kept" and r["status"] != "PASS"]
        if not bad or any(" zeros " not in b for b in bad) or any(r["status"] != "PASS" for r in rn):
            return None
        return text.format(k=len(rn))

    LIM = {"fz_dec": "recorded prelude limit, min / max of zeros of both signs (RULEBOOK section 6): only the family zeros differs, and "
                     "suite fz_dec_nz (the same seeds with -0.0 replaced by 0.0 in min_pd, max_pd on both sides) is equal, {k} of {k}",
           "fz_lift": "recorded prelude limit, the running sum starting at -0.0 (polars cum_sum starts from 0.0; RULEBOOK section 6): only "
                      "the family zeros differs, and suite fz_lift_nz (the zeros and the rejected seeds with -0.0 replaced by 0.0 in "
                      "cum_defaults, cum_capture_rate, cum_lift on both sides) is equal, {k} of {k}"}
    for name, unit, st, note in [
        ("fz_dec", U04, st4, "one case = one digest over about 50 seeds (input frame, decile_data, decile_analysis of each); 0 to 60 rows; "
                             "default_flag from {null, 0, 1}, one seed in 4 from a wild pool (NaN, +-inf, 2, 0.5, -1, -0.0, 1e300, random floats); "
                             "pd_logistic 70 or 30 % from a pool with ties (null, NaN, +-inf, 0, 0.5 +- 1 ulp, 0.25, 0.75, 1, 0.1, 1e300, 1e-300, "
                             "subnormal), else random floats; one seed in 8 also -0.0 (family zeros). Rejected = 0 rows"),
        ("fz_lift", U05, st5, "one case = one digest over about 50 seeds (decile_data, decile_analysis, cumulative_lift of each); decile_data 0 to 5 "
                              "rows of {null, 0, 1}, one seed in 8 with NaN, +inf, 2, -0.0; decile_analysis 0 to 12 rows: decile 0..12 with nulls "
                              "and duplicates, unsorted; total_count -2..6 with nulls; defaults from (null, NaN, 0, 1, 2, 3, +-inf, 1e300, "
                              "0.5) and random floats, one seed in 8 also -0.0 (family zeros); sas_best / float = lookup tables from the real functions. Rejected = decile_data with 0 rows"),
    ]:
        (WORK / f"{name}.fuzz.json").write_text(json.dumps({
            "fuzzer": "port-translator-12", "generator": "diffeval/units/fz_t14_gen.py",
            "units": {unit: {"seeds": seeds, "generated": count, "kept": st["kept"],
                             "python_raises_inside_precondition": st["raises-kept"], "note": note,
                             **({"all_differences_are_recorded_limit": limit(name, LIM[name])} if limit(name, LIM[name]) else {})}}}, indent=1))
    c = json.loads((WORK / "fz_dec.inputs.json").read_text()) + json.loads((WORK / "fz_lift.inputs.json").read_text())
    print("input sizes:", [len(i) for x in c for i in x["inputs"]])


if __name__ == "__main__":
    main()
