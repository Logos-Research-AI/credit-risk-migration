"""Fuzz of def:train_run_12_risk_scores (+ _precond) after the fifth port diff (2026-11-18), through def:zz_carrier_e.
Blueprint 5365851c-5549-44b7-9207-4bd4c422031d. Nothing is changed on the blueprint.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_t12_gen.py
      -> work/fz5_t12.json, fz5_t12.inputs.json (suite; every input is for item def:zz_carrier_e, decl zz_carrier_e)

Frames are built INSIDE Lean from seeds (kit.GEN) and mirrored here (kit.gF / gI / hsh). Seed s gives the training frame
(seed s) and the validation frame (seed s + 500000). Frame of seed t:
  rows n from [0,0,1,1,2,3,5,8,13,25] (n = 0: header only: columns, no row);
  pd_logistic class c = h(t,1001) % 18: 0..11, 17 Float64 (pool by h(t,1002) % 4: edge list EP, edges of the grade
  thresholds, random exponents near 1, k/100 grid with 15% null); 12 Float64 all null; 13 dtype Null; 14 Int64; 15 String;
  16 absent.  Kept = Float64 only (the precondition); the others are sent as "rejected" and compared too.
  extra columns: default_flag Float64 (3 in 4), row_id Int64 (1 in 2), name String (1 in 3), and with 1 in 3 one column
  named like a column the step writes (base_score, score_range, credit_risk_score, risk_grade, recommendation,
  base_rate, interest_rate) of dtype Float64 / String / Int64; pd_logistic inserted at a random position.
Expected: the real lines of train.py for the training and validation blocks (exec'd on the frames).
"""
from __future__ import annotations

import inspect
import json
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
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train as tr  # noqa: E402

ITEM, DECL = "def:zz_carrier_e", "zz_carrier_e"
U = "train_run_12_risk_scores"
M64 = (1 << 64) - 1
h0 = kit.hsh
nan, inf = float("nan"), float("inf")
SEED0, CH, NCH = 800000, 25, 150
VOFF = 500000

SRC = inspect.getsource(tr).splitlines()
_a = next(i for i, l in enumerate(SRC) if l.strip() == "risk_scores_train = logit_scored_train.with_columns(")
_b = [i for i, l in enumerate(SRC) if l.strip() == ")  # format interest_rate percent8.2 -> applied at export"][1]
SLICE = compile(textwrap.dedent("\n".join(SRC[_a:_b + 1])), f"train.py:{_a + 1}-{_b + 1}", "exec")
LINES = (_a + 1, _b + 1)


def run_slice(tr_df: pl.DataFrame, va_df: pl.DataFrame):
    env = {"pl": pl, "sas_compat": sc, "logit_scored_train": tr_df, "logit_scored_valid": va_df}
    exec(SLICE, env)
    return env["risk_scores_train"], env["risk_scores_validation"]


def fl(b):
    return struct.unpack("<d", struct.pack("<Q", b & M64))[0]


def bt(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def ulps(v, ks=(-2, -1, 0, 1, 2)):
    return [fl(bt(v) + k) for k in ks]


EP = [None, nan, inf, -inf, 0.0, -0.0, 1.0, 2.0, -1.0, 0.5, 1e-300, 5e-324, 1e300, 0.10, 0.15, 0.25, 0.35]
EPG = [None] + [x for v in (0.10, 0.15, 0.25, 0.35, 0.50) for x in ulps(v)] + [0.0, 1.0]
EP2 = [None, nan, 0.5, 0.0, 1.0]
POOLS = [EP, EPG, EP2]
PES = [100, 70, 40]
NRL = [0, 0, 1, 1, 2, 3, 5, 8, 13, 25]
STRS = ["A", "B", "F", "zz", ""]
COLL = ["base_score", "score_range", "credit_risk_score", "risk_grade", "recommendation", "base_rate", "interest_rate"]


def h(t, k):
    return h0(t, k)


def pd_vals(t, n, m):
    if m < 3:
        return kit.gF(t + 7, n, PES[m] if m < 2 else 40, 1, POOLS[m] if m < 2 else EP2)
    return [None if g is None else g / 100.0 for g in kit.gI(t + 7, n, 15, 101, 0)]


def cls(t):
    return h(t, 1001) % 18


def kept_cls(c):
    return c < 13 or c == 17


def frame(t) -> pl.DataFrame:
    n = NRL[h(t, 1000) % 10]
    c = cls(t)
    m = h(t, 1002) % 4
    cols = []
    if h(t, 1010) % 4 != 0:
        cols.append(pl.Series("default_flag", kit.gF(t + 11, n, 50, 1, [None, 0.0, 1.0, nan]), dtype=pl.Float64, nan_to_null=False))
    if h(t, 1011) % 2 == 0:
        cols.append(pl.Series("row_id", kit.gI(t + 13, n, 10, 50, 0), dtype=pl.Int64))
    if h(t, 1012) % 3 == 0:
        cols.append(pl.Series("name", [None if g is None else STRS[g] for g in kit.gI(t + 17, n, 20, 5, 0)], dtype=pl.String))
    if h(t, 1013) % 3 == 0:
        nm, d = COLL[h(t, 1014) % 7], h(t, 1015) % 3
        if d == 0:
            cols.append(pl.Series(nm, kit.gF(t + 19, n, 30, 1, [None, 0.0, nan]), dtype=pl.Float64, nan_to_null=False))
        elif d == 1:
            cols.append(pl.Series(nm, [None if g is None else STRS[g] for g in kit.gI(t + 23, n, 20, 5, 0)], dtype=pl.String))
        else:
            cols.append(pl.Series(nm, kit.gI(t + 29, n, 10, 9, 3), dtype=pl.Int64))
    pdc = None
    if c < 12 or c == 17:
        pdc = pl.Series("pd_logistic", pd_vals(t, n, m), dtype=pl.Float64, nan_to_null=False)
    elif c == 12:
        pdc = pl.Series("pd_logistic", [None] * n, dtype=pl.Float64)
    elif c == 13:
        pdc = pl.Series("pd_logistic", [None] * n, dtype=pl.Null)
    elif c == 14:
        pdc = pl.Series("pd_logistic", kit.gI(t + 31, n, 20, 3, 1), dtype=pl.Int64)
    elif c == 15:
        pdc = pl.Series("pd_logistic", [None if g is None else STRS[g] for g in kit.gI(t + 37, n, 20, 5, 0)], dtype=pl.String)
    if pdc is not None:
        i = h(t, 1016) % (len(cols) + 1)
        cols = cols[:i] + [pdc] + cols[i:]
    return pl.DataFrame(cols) if cols else pl.DataFrame()


def pre(df: pl.DataFrame) -> bool:
    return "pd_logistic" in df.columns and df.schema["pd_logistic"] == pl.Float64


def tok(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def lf(x):
    return "none" if x is None else f"(FB {bt(x)})"


def llist(xs):
    return "[" + ", ".join(lf(x) for x in xs) + "]"


LETS = (
    b4.W
    + "let h := fun (s k : Nat) => (hsh s k).toNat; "
    + "let FB := fun (b : UInt64) => (some (Float.ofBits b) : Option Float); "
    + f"let EP : List (Option Float) := {llist(EP)}; let EPG : List (Option Float) := {llist(EPG)}; let EP2 : List (Option Float) := {llist(EP2)}; "
    + f"let NRL : List Nat := {NRL}; let PES : List UInt64 := {PES}; let STRS : List String := {json.dumps(STRS)}; "
    + "let COLL : List String := " + json.dumps(COLL) + "; "
    + "let SO := fun (v : List (Option Int)) => v.map (fun (o : Option Int) => o.map (fun (k : Int) => STRS.getD k.toNat \"\")); "
    + "let PV := fun (t n m : Nat) => (if m < 2 then gF (t + 7) n (PES.getD m 100) 1 (if m == 0 then EP else EPG) "
      "else if m == 2 then gF (t + 7) n 40 1 EP2 else (gI (t + 7) n 15 101 0).map (fun (o : Option Int) => o.map (fun (k : Int) => Float.ofInt k / 100.0)) : List (Option Float)); "
    + "let FR := fun (t : Nat) => let n := NRL.getD (h t 1000 % 10) 0; let c := h t 1001 % 18; let m := h t 1002 % 4; "
      "let c1 : List (String × Pl.Col Float) := (if h t 1010 % 4 != 0 then [(\"default_flag\", Pl.Col.f64 (gF (t + 11) n 50 1 [none, FB 0, FB 0x3FF0000000000000, FB 0x7FF8000000000000]))] else []); "
      "let c2 : List (String × Pl.Col Float) := c1 ++ (if h t 1011 % 2 == 0 then [(\"row_id\", Pl.Col.int (gI (t + 13) n 10 50 0))] else []); "
      "let c3 : List (String × Pl.Col Float) := c2 ++ (if h t 1012 % 3 == 0 then [(\"name\", Pl.Col.str (SO (gI (t + 17) n 20 5 0)))] else []); "
      "let c4 : List (String × Pl.Col Float) := c3 ++ (if h t 1013 % 3 == 0 then [(COLL.getD (h t 1014 % 7) \"\", "
      "(if h t 1015 % 3 == 0 then Pl.Col.f64 (gF (t + 19) n 30 1 [none, FB 0, FB 0x7FF8000000000000]) "
      "else if h t 1015 % 3 == 1 then Pl.Col.str (SO (gI (t + 23) n 20 5 0)) else Pl.Col.int (gI (t + 29) n 10 9 3) : Pl.Col Float))] else []); "
      "let pdc : List (String × Pl.Col Float) := (if c < 12 || c == 17 then [(\"pd_logistic\", Pl.Col.f64 (PV t n m))] "
      "else if c == 12 then [(\"pd_logistic\", Pl.Col.f64 (List.replicate n none))] else if c == 13 then [(\"pd_logistic\", Pl.Col.null n)] "
      "else if c == 14 then [(\"pd_logistic\", Pl.Col.int (gI (t + 31) n 20 3 1))] else if c == 15 then [(\"pd_logistic\", Pl.Col.str (SO (gI (t + 37) n 20 5 0)))] else []); "
      "let i := h t 1016 % (c4.length + 1); (c4.take i ++ pdc ++ c4.drop i : Pl.Frame Float); "
    + f"let OKC := fun (s : Nat) => (h s 1001 % 18 < 13 || h s 1001 % 18 == 17) && (h (s + {VOFF}) 1001 % 18 < 13 || h (s + {VOFF}) 1001 % 18 == 17); "
    + f"let M := fun (s : Nat) => let r := {U} (α := Float) (FR s) (FR (s + {VOFF})); W [dg (tR r.1), dg (tR r.2)]; "
    + f"let MI := fun (s : Nat) => W [dg (tR (FR s)), dg (tR (FR (s + {VOFF})))]; "
)


def main() -> None:
    st = Suite("fz5_t12")
    st.item, st.decl = ITEM, DECL
    kept, rej, raises, dropped = {}, {}, [], []
    inp = {}
    stats = {"cases": 0, "header only (both)": 0, "pd with null": 0, "pd NaN": 0, "pd on a grade edge": 0,
             "pd all null": 0, "collision column": 0}
    edges = {fl(bt(v) + k) for v in (0.10, 0.15, 0.25, 0.35, 0.50) for k in (-1, 0, 1)}
    for s in range(SEED0, SEED0 + CH * NCH):
        d1, d2 = frame(s), frame(s + VOFF)
        ok = pre(d1) and pre(d2)
        assert ok == (kept_cls(cls(s)) and kept_cls(cls(s + VOFF))), s
        inp[s] = b4.w([tok(d1), tok(d2)])
        try:
            r1, r2 = run_slice(d1, d2)
            v = b4.w([tok(r1), tok(r2)])
            why = ""
        except Exception as ex:  # noqa: BLE001
            v, why = None, f"{type(ex).__name__}: {str(ex)[:80]}"
        if ok and v is not None:
            kept[s] = v
            stats["cases"] += 1
            for d in (d1, d2):
                p = d.get_column("pd_logistic")
                stats["header only (both)"] += d.height == 0 and d is d2 and d1.height == 0
                stats["pd with null"] += p.null_count() > 0
                stats["pd NaN"] += any(x is not None and x != x for x in p.to_list())
                stats["pd on a grade edge"] += any(x in edges for x in p.to_list() if x is not None)
                stats["pd all null"] += d.height > 0 and p.null_count() == d.height
                stats["collision column"] += any(c in COLL for c in d.columns)
        elif ok:
            raises.append((s, why))
        elif v is not None:
            rej[s] = v
        else:
            dropped.append((s, why))
    assert not raises, raises[:5]
    kc, rc, ic = [], [], []
    for i in range(NCH):
        r = range(SEED0 + CH * i, SEED0 + CH * i + CH)
        k_, r_ = [x for x in r if x in kept], [x for x in r if x in rej]
        kc.append((f"kept seeds of {r[0]}..{r[-1]}", U, b4.w([kept[x] for x in k_]), {"fz": "kept", "covers": len(k_)}))
        rc.append((f"rejected seeds of {r[0]}..{r[-1]}", U, b4.w([rej[x] for x in r_]), {"fz": "rejected", "covers": len(r_)}))
        ic.append((f"inputs of seeds {r[0]}..{r[-1]}", U, b4.w([inp[x] for x in r]), {"fz": "inputs", "covers": len(r)}))
    body = "(List.range {n}).map (fun (i : Nat) => W (((List.range' ({a} + {c} * i) {c}).filter (fun (s : Nat) => {f})).map {m}))"
    st.ints(LETS, body.format(n=NCH, a=SEED0, c=CH, f="OKC s", m="M"), kc, gen=True)
    st.ints(LETS, body.format(n=NCH, a=SEED0, c=CH, f="!(OKC s)", m="M"), rc, gen=True)
    st.ints(LETS, body.format(n=NCH, a=SEED0, c=CH, f="true", m="MI"), ic, gen=True)
    st.notes = {U: "fuzz 2026-11-18, fifth diff"}
    st.write()
    (HERE.parent / "work" / "fz5_t12.fuzz.json").write_text(json.dumps({
        "kept": len(kept), "rejected_returns": len(rej), "rejected_python_raises": [list(x) for x in dropped],
        "stats": stats, "lines": LINES}, indent=1))
    print("lines", LINES, "kept", len(kept), "rejected returns", len(rej), "rejected raise", len(dropped), stats)
    for i, x in enumerate(st.inputs):
        print(i, len(x["text"]), "chars")


if __name__ == "__main__":
    main()
