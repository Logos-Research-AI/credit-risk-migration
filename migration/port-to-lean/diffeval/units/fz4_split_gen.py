"""Fuzz of def:fe_run_06_split and def:fe_run_06_split_precond (update 2026-11-17; the unit was
written by another translator; nothing on the blueprint is changed).

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz4_split_gen.py
      -> diffeval/work/fz4_split.{json,inputs.json,fuzz.json}
  (eval_decl each input on def:zz_carrier_f / zz_carrier_f; write the outputs, one line per input, to
   diffeval/work/fz4_split.out.txt) ... python diffeval/compare.py diffeval/work/fz4_split.json diffeval/work/fz4_split.out.txt

One case = one seed s. Everything is built INSIDE Lean from the seed (kit.hsh / kit.gI mirrored):
  split file   n_i rows (1..40) of TEXT drawn from the pool T (numbers, fractions, exponents,
               padded, signs, 'NA', '', '.', inf, 1e400, 32+ digit strings, non-ASCII digits ...);
               optionally one extra column (text or number) before or after row_id.
  features     n_f rows (0 and 1 included), columns row_id (Float64, drawn from a pool made of the
               values the texts read to, their ulp neighbours, null, NaN, +-inf, +-0.0), k (Int64, the
               row number) and x (Float64), in one of three layouts.
Expected value: the REAL port lines feature_engineering.py:343-350 executed verbatim on the real
CSV bytes (pl.read_csv(BytesIO) with infer_schema=False) and on the features frame. The Lean unit
takes the table AFTER sas_compat.input_best32 (RULEBOOK 2.6): its row_id column is the Float64
column the real read + input_best32 produce. The Lean side holds that as the lookup VT (text
index -> the real sas_compat.input_best32 of that text, computed here by running the real function
on the pool); the generator asserts, per case, that the real read of the CSV gives exactly the
ids the lookup gives (so nothing is typed into the comparison).
Precondition def:fe_run_06_split_precond rendered by `precond(...)`: split table not empty (>= 1
row); one cell kind per column; distinct names; column row_id present and numeric; every non-null
id finite; features: distinct names, common length, 0 < height, row_id present and Float64.
Output: one digest per block of 25 seeds of tR train ++ tR validation, one digest per block of the
generated inputs, plus per-seed digests for the first 200 seeds (to localise a block).
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_f", "zz_carrier_f")

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat  # noqa: E402

nan, inf = float("nan"), float("inf")
UNIT = "fe_run_06_split"
SUITE = "fz4_split"
A, B = 343, 350
up = lambda x: math.nextafter(x, inf)   # noqa: E731
dn = lambda x: math.nextafter(x, -inf)  # noqa: E731

T = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "1.0", "2.0", "2.5", "1.5", "0.5", ".5", "5.", "+4", "-1", "-0", "0",
     "0.0", "00007", " 3", "3 ", "  4.0  ", "1e0", "1E1", "2.5e0", "1e-1", "0.1", "1e15", "9007199254740992", "9007199254740993",
     "12345678901234567890", "1e300", "1e400", "-1e400", "5e-324", "1e-400", "inf", "-inf", "Infinity", "nan", "NaN", "NA", "", ".",
     "-", "+", "abc", "1 2", "1,5", "0x10", "1_0", "１２", "3.0000000000000004", "2.9999999999999996", "3\t", "1.5.", "--1",
     "1e", "e5", "٣", "1234567890123456789012345678901234567", "1" + "0" * 31, "1" + "0" * 32, "1" + "0" * 30 + ".5",
     "0." + "0" * 29 + "1", "1e+2", "1e-0", " 7", "7 ", "1d2", "1D2", "0b1", "1.0e", "١", "1e5 ", "TRUE", "5", "5", "3"]
NI = [1, 1, 2, 3, 5, 9, 17, 40]
NF = [0, 1, 1, 2, 3, 5, 9, 20]


def in32(t: str):
    out = pl.DataFrame({"row_id": [t]}).select(sas_compat.input_best32(pl.col("row_id")))["row_id"].to_list()[0]
    return out


VT = [in32(t) for t in T]
RP = [None, nan, inf, -inf, 0.0, -0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 100.0, 1.5, 2.5, 0.5]
for v in VT:
    if v is not None:
        RP += [v, up(v), dn(v)]
RP += [9007199254740992.0, up(9007199254740992.0), 1e15, 3.0000000000000004, 2.9999999999999996]
RP = list(dict.fromkeys([("nan" if (isinstance(x, float) and x != x) else cmp.fbits(x) if x is not None else None) for x in RP]))
# rebuild list of floats from the dedup key (bits) so that the Lean pool and the Python pool are the same
RPF = []
for k in RP:
    RPF.append(None if k is None else nan if k == "nan" else lt.from_bits(k))
RP = RPF


def lopt(pool: list) -> str:
    return "[" + ", ".join("none" if x is None else f"some {lt.lean_float(x)}" for x in pool) + "]"


def pick(pool: list, s: int, n: int) -> list:
    return [None if i is None else pool[i] for i in kit.gI(s, n, 0, len(pool), 0)]


def shape(s: int):
    u = kit.hsh(s, 91)
    return dict(ni=NI[u % 8], nf=NF[(u // 8) % 8], lay=(u // 64) % 3, ex=(u // 256) % 3, first=(u // 1024) % 2)


def ids_idx(s: int, n: int) -> list:
    return kit.gI(2 * s, n, 0, len(T), 0)


def features(s: int) -> pl.DataFrame:
    sh = shape(s)
    n = sh["nf"]
    rid = pl.Series("row_id", pick(RP, 2 * s + 1, n), dtype=pl.Float64, nan_to_null=False)
    k = pl.Series("k", list(range(n)), dtype=pl.Int64)
    x = pl.Series("x", pick(RP, 2 * s + 7, n), dtype=pl.Float64, nan_to_null=False)
    return pl.DataFrame([[rid, k, x], [x, k, rid], [k, rid]][sh["lay"]])


def csv_bytes(s: int) -> tuple[bytes, list]:
    sh = shape(s)
    idx = ids_idx(s, sh["ni"])
    import csv
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    ex = sh["ex"]
    hdr = ["row_id"] if ex == 0 else (["row_id", "g"] if sh["first"] else ["g", "row_id"])
    w.writerow(hdr)
    for j, i in enumerate(idx):
        t = T[i]
        w.writerow([t] if ex == 0 else ([t, "q"] if sh["first"] else ["q", t]))
    return buf.getvalue().encode(), idx


import textwrap  # noqa: E402

_src = textwrap.dedent("".join(Path(fe.__file__).read_text().splitlines(keepends=True)[A - 1:B]))
assert "input_best32" in _src and "credit_validation" in _src, _src
SRC = compile(_src, f"{fe.__file__}:{A}-{B}", "exec")


def python(s: int):
    data, idx = csv_bytes(s)
    ns = dict(vars(fe))
    ns["split_ids"] = io.BytesIO(data)
    ns["credit_features"] = features(s)
    try:
        exec(SRC, ns)  # noqa: S102
        return ns["credit_train"], ns["credit_validation"], ns["train_ids"], idx, None
    except Exception as ex:  # noqa: BLE001
        return None, None, None, idx, ex


def precond(s: int, train_ids: list, idx: list) -> bool:
    df = features(s)
    sh = shape(s)
    ids = [VT[i] for i in idx]
    return (len(idx) >= 1 and all(x is None or math.isfinite(x) for x in ids)
            and len(set(df.columns)) == len(df.columns) and df.height > 0 and df.schema.get("row_id") == pl.Float64)


def toks(df: pl.DataFrame) -> list[int]:
    return cmp.tokens(cmp.canon_frame(df))


def toks_ids(s: int) -> list[int]:
    """Mirror of the generated inputs: the id column of the split table, the features frame."""
    sh = shape(s)
    idx = ids_idx(s, sh["ni"])
    ids = [VT[i] for i in idx]
    t = cmp.tokens(cmp.canon_series_for_tokens(ids)) if False else None
    return toks(features(s)) + toks(pl.DataFrame({"row_id": pl.Series(ids, dtype=pl.Float64, nan_to_null=False)}))


def pre() -> str:
    return (
        f"let T : List (Option Float) := {lopt(VT)}; let RP : List (Option Float) := {lopt(RP)}; "
        "let pk := fun (P : List (Option Float)) (s n : Nat) => ((gI s n 0 P.length.toUInt64 0).map (fun (o : Option Int) => "
        "(match o with | some i => P.getD i.toNat none | none => none))); "
        "let sh := fun (s : Nat) => (let u := (hsh s 91).toNat; ([1, 1, 2, 3, 5, 9, 17, 40].getD (u % 8) 1, [0, 1, 1, 2, 3, 5, 9, 20].getD ((u / 8) % 8) 0, (u / 64) % 3, (u / 256) % 3, (u / 1024) % 2)); "
        "let mkT := fun (s : Nat) => (let h := sh s; let ids := pk T (2 * s) h.1; "
        "(ids.map (fun (o : Option Float) => (let c := (\"row_id\", Tabular.Cell.num o); "
        "if h.2.2.2.1 == 0 then [c] else if h.2.2.2.2 == 1 then [c, (\"g\", Tabular.Cell.str (some \"q\"))] else [(\"g\", Tabular.Cell.str (some \"q\")), c] : Tabular.Row Float))) : Tabular.Table Float); "
        "let mkF := fun (s : Nat) => (let h := sh s; let n := h.2.1; "
        "let rid := (\"row_id\", Pl.Col.f64 (pk RP (2 * s + 1) n)); let k := (\"k\", Pl.Col.int ((List.range n).map (fun (i : Nat) => some (i : Int)))); "
        "let x := (\"x\", Pl.Col.f64 (pk RP (2 * s + 7) n)); "
        "(if h.2.2.1 == 0 then [rid, k, x] else if h.2.2.1 == 1 then [x, k, rid] else [k, rid] : Pl.Frame Float)); "
        "let U := fun (s : Nat) => (let r := fe_run_06_split (mkT s) (mkF s); tR r.1 ++ tR r.2); "
        "let G := fun (s : Nat) => (tR (mkF s) ++ tA (mkT s)); "
    )


# the generated inputs are checked through tR of the features and tA of the table: mirror of tA
def toks_table(s: int) -> list[int]:
    sh = shape(s)
    ids = [VT[i] for i in ids_idx(s, sh["ni"])]
    rows = []
    for v in ids:
        c = ["row_id", "num", None if v is None else cmp.fbits(v)]
        if sh["ex"] == 0:
            rows.append([c])
        elif sh["first"]:
            rows.append([c, ["g", "str", "q"]])
        else:
            rows.append([["g", "str", "q"], c])
    return cmp.tokens({"type": "table", "rows": rows})


def toks_gen(s: int) -> list[int]:
    return toks(features(s)) + toks_table(s)


S0, BLOCKS, K = 100000, 100, 25
PERSEED = 200


def build():
    s = Suite(SUITE)
    st = {"generated": 0, "kept": 0, "rejected": 0, "raises_inside_precond": [], "raises_outside": 0, "mismatch_ids": []}
    res, gen_, per = [], [], []
    outside = {}
    for b in range(BLOCKS):
        rt, gt = [], []
        for j in range(K):
            seed = S0 + b * K + j
            tr, va, tids, idx, ex = python(seed)
            st["generated"] += 1
            ok = precond(seed, tids, idx)
            if ex is not None:
                if ok:
                    st["raises_inside_precond"].append(seed)
                else:
                    st["raises_outside"] += 1
                continue
            if tids is not None and tids.to_list() != [VT[i] for i in idx] and not all(
                    (a is None and c is None) or (a is not None and c is not None and cmp.fbits(a) == cmp.fbits(c))
                    for a, c in zip(tids.to_list(), [VT[i] for i in idx], strict=False)):
                st["mismatch_ids"].append(seed)
            if not ok:
                st["rejected"] += 1
                outside[seed] = (shape(seed)["nf"],)
                continue
            st["kept"] += 1
            t = toks(tr) + toks(va)
            rt += t
            gt += toks_gen(seed)
            if seed < S0 + PERSEED:
                per.append((seed, cmp.digest(t), cmp.digest(toks_gen(seed))))
    # kept seeds are decided in Lean by the same test: seeds whose features frame is empty are skipped
    # (precondition: 0 < height); everything else is kept.
    for b in range(BLOCKS):
        rt, gt = [], []
        for j in range(K):
            seed = S0 + b * K + j
            if shape(seed)["nf"] == 0:
                continue
            tr, va, tids, idx, ex = python(seed)
            assert ex is None and precond(seed, tids, idx), seed
            rt += toks(tr) + toks(va)
            gt += toks_gen(seed)
        name = f"seeds {S0 + b * K}..{S0 + b * K + K - 1}"
        res.append((name, UNIT, cmp.digest(rt), {"fz": "kept", "covers": K}))
        gen_.append((name + " / generated inputs", UNIT + " (input)", cmp.digest(gt), {"fz": "kept", "covers": K}))
    body = [f"(List.range {BLOCKS}).map (fun (b : Nat) => dg ((List.range {K}).flatMap (fun (j : Nat) => let sd := {S0} + b * {K} + j; if (sh sd).2.1 == 0 then [] else U sd)))",
            f"(List.range {BLOCKS}).map (fun (b : Nat) => dg ((List.range {K}).flatMap (fun (j : Nat) => let sd := {S0} + b * {K} + j; if (sh sd).2.1 == 0 then [] else G sd)))"]
    pcs = []
    for seed, d1, d2 in per:
        if shape(seed)["nf"] == 0:
            continue
        pcs.append((f"seed {seed}", UNIT, d1, {"fz": "kept"}))
    body.append(f"(((List.range {PERSEED}).map (fun (i : Nat) => {S0} + i)).filter (fun (sd : Nat) => (sh sd).2.1 != 0)).map (fun (sd : Nat) => dg (U sd))")
    s.ints(pre(), "(" + " ++ ".join(body) + ")", res + gen_ + pcs, gen=True, table=True)
    s.notes = {UNIT: "seeded fuzz: split table and features frame generated inside Lean; expected = real lines 343-350 on real CSV bytes"}
    s.write()
    fz = {"fuzzer": "fuzz-agent", "blueprint": "5365851c-5549-44b7-9207-4bd4c422031d", "generator": "diffeval/units/fz4_split_gen.py",
          "generated": st["generated"], "kept": st["kept"], "rejected": st["rejected"],
          "python_raises_inside_precondition": st["raises_inside_precond"], "mismatch_ids": st["mismatch_ids"]}
    (suite_mod.WORK / f"{SUITE}.fuzz.json").write_text(json.dumps(fz, indent=1))
    print(st)
    print("input chars:", [len(i["text"]) for i in s.inputs], "pool sizes", len(T), len(RP))


if __name__ == "__main__":
    build()
