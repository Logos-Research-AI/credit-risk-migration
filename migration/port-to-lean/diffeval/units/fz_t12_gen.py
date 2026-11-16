"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md), by port-translator-3 on a unit it reviewed:
metrics_run_01_roc_auc (metrics_calculation.py:109-152).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t12_gen.py
      -> diffeval/work/fz_t12.json, fz_t12.inputs.json, fz_t12.fuzz.json
  eval_decl each input on def:zz_carrier_m; python3 diffeval/fuzz_collect.py 3 fz_t12; compare.py; fuzz_receipt.py

One seed gives one frame logit_scored_valid with the columns default_flag and pd_logistic (in that
order, or reversed in one seed of four), built inside Lean (kit.GEN) and mirrored here.
Expected: lines 114-152 of the source executed on the frame (t12_gen.run_slice, which t12_gen
asserts equal to the locals of the real run on the scenario files). A case is the digest of
(roc_stats, auc_summary) over the seeds of a block of 25 (field "covers").

math.fsum: the algorithm of CPython written as a Lean `let`, its Python mirror asserted equal to
math.fsum on every list the port passes (fz_t1_gen).

Precondition def:metrics_run_01_roc_auc_precond, rendered in Python:
  distinct names, columns of one length    true of every pl.DataFrame
  0 < height                               df.height > 0
  default_flag, pd_logistic Float64        the two dtypes
  roc_association_precond                  fz_t1_gen.pre_roc on the two columns
Rejected inputs on which Python returns (no row; an Int64 flag or probability column) are sent to
Lean too, marked "rejected".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import t12_gen as t12  # noqa: E402  (run_slice: lines 114-152)
import fz_t1_gen as f1  # noqa: E402  (pools, generators, py_fsum check, pre_roc)
import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

ITEM, DECL = "def:zz_carrier_m", "zz_carrier_m"
U = "metrics_run_01_roc_auc"
SEED0, CH, NCH = 20000, 25, 112
h, nn, NS, EY, ES, J2, LV, OS, OG = f1.h, f1.nn, f1.NS, f1.EY, f1.ES, f1.J2, f1.LV, f1.OS, f1.OG

LETS = (
    b4.W + "let h := fun (s k : Nat) => (hsh s k).toNat; "
    + f"let NS : List Nat := {NS}; let ES : List (Option Float) := {f1.olist(ES)}; "
    + "let nn := fun (s : Nat) => NS.getD (h s 1000 % 12) 0; "
    + f"let EY : List (Option Float) := {f1.olist(EY)}; let J : List Float := [{', '.join(f1.lf(j) for j in J2)}]; let LV : List UInt64 := {LV}; "
    + "let YC := fun (s : Nat) => let n := nn s; (if h s 1001 % 12 == 11 then Pl.Col.int (gI s n 8 3 0) else Pl.Col.f64 (gF s n 100 1 EY) : Pl.Col Float); "
    + f"let SC := fun (s : Nat) => let n := nn s; let a := s + {OS}; (match h s 1002 % 12 with "
      "| 0 | 1 | 2 | 3 => Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some a, some b => some (Float.ofInt a / 100.0 + J.getD b.toNat 0.0) | _, _ => none : Option Float)) "
      f"(gI a n 4 (LV.getD (h s 1004 % 5) 1) 0) (gI (s + {OG}) n 0 {len(J2)} 0)) "
      "| 4 | 5 | 6 | 7 => Pl.Col.f64 (gF a n 50 3 ES) | 8 | 9 => Pl.Col.f64 (gF a n 0 1 ES) | 10 => Pl.Col.int (gI a n 5 4 1) "
      "| _ => Pl.Col.f64 (List.replicate n none) : Pl.Col Float); "
    + "let FR := fun (s : Nat) => (if h s 1006 % 4 == 0 then [(\"pd_logistic\", SC s), (\"default_flag\", YC s)] else [(\"default_flag\", YC s), (\"pd_logistic\", SC s)] : Pl.Frame Float); "
    + "let OK := fun (s : Nat) => nn s != 0 && h s 1001 % 12 != 11 && h s 1002 % 12 != 10; "
    + f1.FS_LET
    + f"let M := fun (s : Nat) => let r := {U} (α := Float) FS (FR s); W [dg (tR r.1), dg (tR r.2)]; "
)


def y_col(s: int) -> pl.Series:
    n = nn(s)
    if h(s, 1001) % 12 == 11:
        return pl.Series(kit.gI(s, n, 8, 3, 0), dtype=pl.Int64)
    return pl.Series(kit.gF(s, n, 100, 1, EY), dtype=pl.Float64, nan_to_null=False)


def s_col(s: int) -> pl.Series:
    n, a, k = nn(s), s + OS, h(s, 1002) % 12
    if k < 4:
        g, j = kit.gI(a, n, 4, LV[h(s, 1004) % 5], 0), kit.gI(s + OG, n, 0, len(J2), 0)
        return pl.Series([None if x is None else float(x) / 100.0 + J2[b] for x, b in zip(g, j, strict=True)],
                         dtype=pl.Float64, nan_to_null=False)
    if k < 8:
        return pl.Series(kit.gF(a, n, 50, 3, ES), dtype=pl.Float64, nan_to_null=False)
    if k < 10:
        return pl.Series(kit.gF(a, n, 0, 1, ES), dtype=pl.Float64, nan_to_null=False)
    if k == 10:
        return pl.Series(kit.gI(a, n, 5, 4, 1), dtype=pl.Int64)
    return pl.Series([None] * n, dtype=pl.Float64)


def frame(s: int) -> pl.DataFrame:
    y, p = y_col(s).alias("default_flag"), s_col(s).alias("pd_logistic")
    return pl.DataFrame([p, y] if h(s, 1006) % 4 == 0 else [y, p])


def pre(df: pl.DataFrame) -> bool:
    return (df.height > 0 and df.schema["default_flag"] == pl.Float64 and df.schema["pd_logistic"] == pl.Float64
            and f1.pre_roc(df.get_column("default_flag"), df.get_column("pd_logistic")))


def dig(df: pl.DataFrame) -> int:
    env = t12.run_slice(df)
    return b4.w([cmp.digest(cmp.tokens(cmp.canon_frame(env["roc_stats"]))), cmp.digest(cmp.tokens(cmp.canon_frame(env["auc_summary"])))])


def main() -> None:
    st = Suite("fz_t12")
    st.item, st.decl = ITEM, DECL
    kept, rej, raises, dropped = {}, {}, [], 0
    stats = {"no pair (auc_summary has no row)": 0, "AUC present": 0}
    for s in range(SEED0, SEED0 + CH * NCH):
        df = frame(s)
        ok = pre(df)
        try:
            v = dig(df)
        except Exception as ex:  # noqa: BLE001
            v = None
            why = f"{type(ex).__name__}: {ex}"
        assert ok == (nn(s) != 0 and h(s, 1001) % 12 != 11 and h(s, 1002) % 12 != 10), s  # the Lean filter OK
        if ok and v is not None:
            kept[s] = v
            a = t12.run_slice(df)["auc_summary"]
            stats["no pair (auc_summary has no row)"] += a.height == 0
            stats["AUC present"] += a.height == 1 and a["AUC"][0] is not None
        elif ok:
            raises.append(s)
            print("PYTHON RAISES INSIDE THE PRECONDITION", s, why)
        elif v is not None:
            rej[s] = v
        else:
            dropped += 1
            print("rejected and raises", s, why[:100])
    assert not raises and not dropped, "the Lean-side seed lists assume neither"
    kc, rc = [], []
    for i in range(NCH):
        r = range(SEED0 + CH * i, SEED0 + CH * i + CH)
        k_, r_ = [x for x in r if x in kept], [x for x in r if x in rej]
        kc.append((f"kept seeds of {r[0]}..{r[-1]}", U, b4.w([kept[x] for x in k_]), {"fz": "kept", "covers": len(k_)}))
        rc.append((f"rejected seeds of {r[0]}..{r[-1]} (no row, or an Int64 column)", U, b4.w([rej[x] for x in r_]), {"fz": "rejected", "covers": len(r_)}))
    body = "(List.range {n}).map (fun (i : Nat) => W (((List.range' ({a} + {c} * i) {c}).filter (fun (s : Nat) => {f})).map M))"
    st.ints(LETS, body.format(n=NCH, a=SEED0, c=CH, f="OK s"), kc, gen=True)
    st.ints(LETS, body.format(n=NCH, a=SEED0, c=CH, f="!(OK s)"), rc, gen=True)
    st.notes = {U: "fuzz 2026-11-16"}
    st.write()
    fuzz = {"fuzzer": "port-translator-3", "generator": "diffeval/units/fz_t12_gen.py", "units": {U: {
        "seeds": f"{SEED0}..{SEED0 + CH * NCH - 1}", "generated": CH * NCH, "kept": len(kept),
        "python_raises_inside_precondition": raises,
        "note": "frames of 0..40 rows with default_flag and pd_logistic (reversed order in 1 seed of 4); flags Float64 from "
                "{0, 1, null, NaN, -0.0, 2, 0.5}; probabilities: grid of 1..12 levels plus offsets of the size of the two eps, or 50% edges "
                "(null, NaN, +-inf, +-0.0, 0.5 -+ each eps and one ulp either side, +-1e300, 1e-300, 5e-324), or random, or all null; "
                f"rejected and sent: no row, Int64 flag or probability column ({len(rej)} inputs); kept: {stats}; one case digests a block of {CH} seeds"}}}
    (HERE.parent / "work" / "fz_t12.fuzz.json").write_text(json.dumps(fuzz, indent=1))
    print("kept", len(kept), "rejected and returns", len(rej), stats, "fsum calls", f1.FSUM_CALLS[0])
    for i, inp in enumerate(st.inputs):
        print(i, len(inp["text"]), "chars")


if __name__ == "__main__":
    main()
