"""Fuzz of def:fe_run_06_split after port commit 4a757fb (T0, 2026-11-19): the split file is used only
when it names exactly (7n+9)//10 distinct ids, all among the input's; otherwise a seeded draw
(random.Random(42).sample over the sorted distinct ids).

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz9_split_gen.py build [S0 COUNT]
      -> diffeval/work/fz9_split.inputs.json (eval_decl calls: item def:zz_carrier_e, decl zz_carrier_e)
         diffeval/work/fz9_split.expected.json
  (eval_decl each input; write the outputs, one line per input, to diffeval/work/fz9_split.out.txt)
  ... python diffeval/units/fz9_split_gen.py compare

One case = one seed s. The inputs are built INSIDE Lean from the seed (kit.hsh) and mirrored here:
  n = 4 + hsh(s,0) % 57 rows; frame columns row_id (Float64) and k (Int64 row number), in one of two
  orders; row_id per row: null (6%), v + 0.5 (2%), 0.0 (1%), -0.0 (1%), +inf (1%), else v, with
  v = hsh % M + 1 and M one of 10^6 (distinct mostly), n//2 + 1 (repeated), 2n (mixed).
  split table, one numeric column row_id, by mode:
    0 attempt to fit: the distinct non-null input ids (first occurrence, Python ==), rotated, the
      first n_train of them (a non-finite id becomes null: input_best32 returns finite values only)
    1 ids picked from the input's row_id cells, count n_train + d (d in -2..2, at least 1)
    2 n_train ids not among the input's (x.25)
    3 mode 0 with the last id replaced by the first (a repeated id)
Expected value: the REAL port lines feature_engineering.py:352-370 executed verbatim (module namespace,
so _split_draw and random are the real ones) on the real CSV bytes of the split table (read_csv +
input_best32, asserted equal to the Lean table) and on the frame. NaN is never generated: with a NaN
row_id and a file that does not fit, Python's draw depends on the set's iteration order (see the
precondition's comment).
Output per seed: [dg(tR train ++ tR validation), dg(tR frame ++ tA table)].
"""
from __future__ import annotations

import io
import json
import math
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import kit  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402

WORK = HERE.parent / "work"
A, B = 352, 370
_lines = Path(fe.__file__).read_text().splitlines(keepends=True)
_src = textwrap.dedent("".join(_lines[A - 1:B]))
assert _src.startswith("file_ids = (") and "credit_validation = " in _src and "_split_draw(input_ids, n_train)" in _src, _src
SRC = compile(_src, f"{fe.__file__}:{A}-{B}", "exec")
inf = float("inf")
FIT0 = 950000


def shape(s):
    u = kit.hsh(s, 0)
    n = 4 + u % 57
    idm = (u >> 8) % 3
    M = [10**6, n // 2 + 1, 2 * n][idm]
    if s >= FIT0:  # family "fits": mode 0 on distinct present ids (the file fits, or the draw on a near miss)
        return dict(n=n, M=10**6, lay=(u >> 16) % 2, fm=0, d=0, off=(u >> 40) % 1000)
    return dict(n=n, M=M, lay=(u >> 16) % 2, fm=(u >> 24) % 4, d=((u >> 32) % 5) - 2, off=(u >> 40) % 1000)


def ids(s):
    sh = shape(s)
    out = []
    for i in range(sh["n"]):
        u = kit.hsh(s, 1000 + i)
        r = (u >> 8) % 100 if s < FIT0 else 99
        v = (u >> 20) % sh["M"] + 1
        out.append(None if r < 6 else float(v) + 0.5 if r < 8 else 0.0 if r < 9 else -0.0 if r < 10 else inf if r < 11 else float(v))
    return out


def distinct(xs):
    acc = []
    for x in xs:
        if x is not None and not any(y == x for y in acc):
            acc.append(x)
    return acc


def fin(x):
    return x if (x is not None and math.isfinite(x)) else None


def file_vals(s):
    sh = shape(s)
    n, fm = sh["n"], sh["fm"]
    nt = (7 * n + 9) // 10
    xs = ids(s)
    if fm in (0, 3):
        D = distinct(xs)
        if not D:
            return [None]
        o = sh["off"] % len(D)
        L = [fin(x) for x in (D[o:] + D[:o])[:nt]]
        if fm == 3 and len(L) >= 2:
            L[-1] = L[0]
        return L
    if fm == 1:
        c = max(1, nt + sh["d"])
        return [fin(xs[kit.hsh(s, 2000 + j) % n]) for j in range(c)]
    return [float(kit.hsh(s, 3000 + j) % 1000) + 0.25 for j in range(nt)]


def frame(s):
    sh = shape(s)
    rid = pl.Series("row_id", ids(s), dtype=pl.Float64)
    k = pl.Series("k", list(range(sh["n"])), dtype=pl.Int64)
    return pl.DataFrame([rid, k] if sh["lay"] == 0 else [k, rid])


def csv_bytes(vals):
    return ("row_id\n" + "".join(("" if v is None else repr(v)) + "\n" for v in vals)).encode()


def python(s):
    vals = file_vals(s)
    ns = dict(vars(fe))
    ns["split_ids"] = io.BytesIO(csv_bytes(vals))
    ns["credit_features"] = frame(s)
    exec(SRC, ns)  # noqa: S102
    # the read file, before the fit test, equals the Lean table's ids bit for bit
    read = pl.read_csv(io.BytesIO(csv_bytes(vals)), columns=["row_id"], infer_schema=False).select(
        fe.sas_compat.input_best32(pl.col("row_id"))).get_column("row_id").to_list()
    assert [None if x is None else cmp.fbits(x) for x in read] == [None if x is None else cmp.fbits(x) for x in vals], (s, read, vals)
    nt = (7 * shape(s)["n"] + 9) // 10
    D = distinct(ids(s))
    fits = len(vals) == nt and len(distinct(vals)) == nt and None not in vals and all(any(y == x for y in D) for x in vals)
    return ns["credit_train"], ns["credit_validation"], fits


def toks(df):
    return cmp.tokens(cmp.canon_frame(df))


def toks_table(vals):
    return cmp.tokens({"type": "table", "rows": [[["row_id", "num", None if v is None else cmp.fbits(v)]] for v in vals]})


LEAN_PRE = (
    "let hsh := fun (s i : Nat) => let z : UInt64 := s.toUInt64 * 0x9E3779B97F4A7C15 + i.toUInt64 * 0xD1B54A32D192ED03 + 1; "
    "let z := (z ^^^ (z >>> 30)) * 0xBF58476D1CE4E5B9; let z := (z ^^^ (z >>> 27)) * 0x94D049BB133111EB; z ^^^ (z >>> 31); "
    "let inf : Float := 1.0 / 0.0; "
    "let fin := fun (o : Option Float) => (match o with | some x => (if x.isFinite then some x else none) | none => none : Option Float); "
    "let sh := fun (s : Nat) => (let u := (hsh s 0).toNat; let n := 4 + u % 57; "
    "if s ≥ 950000 then (n, 1000000, (u >>> 16) % 2, 0, 2, (u >>> 40) % 1000) else "
    "(n, [1000000, n / 2 + 1, 2 * n].getD ((u >>> 8) % 3) 1, (u >>> 16) % 2, (u >>> 24) % 4, ((u >>> 32) % 5 : Nat), (u >>> 40) % 1000)); "
    "let ids := fun (s : Nat) => (let h := sh s; (List.range h.1).map (fun (i : Nat) => (let u := (hsh s (1000 + i)).toNat; "
    "let r := (if s ≥ 950000 then 99 else (u >>> 8) % 100); let v : Float := Float.ofNat ((u >>> 20) % h.2.1 + 1); "
    "(if r < 6 then none else if r < 8 then some (v + 0.5) else if r < 9 then some 0.0 else if r < 10 then some (-0.0) "
    "else if r < 11 then some inf else some v : Option Float)))); "
    "let distinct := fun (xs : List (Option Float)) => xs.foldl (fun (acc : List Float) (o : Option Float) => "
    "(match o with | some x => (if acc.any (fun (y : Float) => y == x) then acc else acc ++ [x]) | none => acc)) []; "
    "let fv := fun (s : Nat) => (let h := sh s; let n := h.1; let fm := h.2.2.2.1; let nt := (7 * n + 9) / 10; let xs := ids s; "
    "if fm == 0 || fm == 3 then (let D := distinct xs; if D.isEmpty then [none] else "
    "(let o := h.2.2.2.2.2 % D.length; let L := ((D.drop o ++ D.take o).take nt).map (fun (x : Float) => fin (some x)); "
    "if fm == 3 && L.length >= 2 then L.set (L.length - 1) (L.headD none) else L)) "
    "else if fm == 1 then (let c := max 1 ((nt + h.2.2.2.2.1 : Nat) - 2); "
    "(List.range c).map (fun (j : Nat) => fin (xs.getD ((hsh s (2000 + j)).toNat % n) none))) "
    "else (List.range nt).map (fun (j : Nat) => some (Float.ofNat ((hsh s (3000 + j)).toNat % 1000) + 0.25))); "
    "let mkT := fun (s : Nat) => ((fv s).map (fun (o : Option Float) => ([(\"row_id\", Tabular.Cell.num o)] : Tabular.Row Float)) : Tabular.Table Float); "
    "let mkF := fun (s : Nat) => (let h := sh s; let rid := (\"row_id\", Pl.Col.f64 (ids s)); "
    "let k := (\"k\", Pl.Col.int ((List.range h.1).map (fun (i : Nat) => some (i : Int)))); "
    "(if h.2.2.1 == 0 then [rid, k] else [k, rid] : Pl.Frame Float)); "
)


def lean_input(seeds, agg=False):
    assert seeds == list(range(seeds[0], seeds[0] + len(seeds)))
    body = ("(" + LEAN_PRE + "(" + f"((List.range {len(seeds)}).map (fun (i : Nat) => {seeds[0]} + i))" +
            ".flatMap (fun (s : Nat) => (let r := fe_run_06_split (mkT s) (mkF s); "
            "[zz_e_dg (zz_e_tR r.1 ++ zz_e_tR r.2), zz_e_dg (zz_e_tR (mkF s) ++ zz_e_tA (mkT s))]))))")
    if agg:  # one digest of the per-seed result digests, one of the per-seed input digests
        body = (f"(let L : List Int := {body}; "
                f"let ev : List UInt64 := (List.range {len(seeds)}).map (fun (j : Nat) => (L.getD (2 * j) 0).toNat.toUInt64); "
                f"let od : List UInt64 := (List.range {len(seeds)}).map (fun (j : Nat) => (L.getD (2 * j + 1) 0).toNat.toUInt64); "
                "[zz_e_dg ev, zz_e_dg od])")
    return body


def build(s0=900000, count=600, per=50, agg=0, name="fz9_split"):
    seeds = list(range(s0, s0 + count))
    exp, stats = {}, {"cases": 0, "fits": 0, "draw": 0, "n": [99, 0], "modes": [0, 0, 0, 0], "with_null_file_id": 0,
                      "repeated_input_ids": 0, "null_input_ids": 0}
    for s in seeds:
        sh = shape(s)
        tr, va, fits = python(s)
        vals = file_vals(s)
        exp[s] = [cmp.digest(toks(tr) + toks(va)), cmp.digest(toks(frame(s)) + toks_table(vals)), int(fits), tr.height, va.height]
        stats["cases"] += 1
        stats["fits" if fits else "draw"] += 1
        stats["n"] = [min(stats["n"][0], sh["n"]), max(stats["n"][1], sh["n"])]
        stats["modes"][sh["fm"]] += 1
        stats["with_null_file_id"] += int(None in vals)
        x = [v for v in ids(s) if v is not None]
        stats["repeated_input_ids"] += int(len(distinct(x)) < len(x))
        stats["null_input_ids"] += int(None in ids(s))
    inputs = [{"item": "def:zz_carrier_e", "decl": "zz_carrier_e", "seeds": seeds[i:i + per],
               "agg": bool(agg), "text": lean_input(seeds[i:i + per], bool(agg))} for i in range(0, len(seeds), per)]
    WORK.mkdir(exist_ok=True)
    (WORK / f"{name}.inputs.json").write_text(json.dumps(inputs, indent=1))
    (WORK / f"{name}.expected.json").write_text(json.dumps({"expected": exp, "stats": stats}, indent=1))
    print(stats, "inputs", len(inputs), "chars", len(inputs[0]["text"]))


def compare(name="fz9_split"):
    out_path = WORK / f"{name}.out.txt"
    inputs = json.loads((WORK / f"{name}.inputs.json").read_text())
    exp = json.loads((WORK / f"{name}.expected.json").read_text())["expected"]
    lines = [ln for ln in out_path.read_text().splitlines() if ln.strip()]
    assert len(lines) == len(inputs), (len(lines), len(inputs))
    res = {"compared": 0, "equal": 0, "diff_result": [], "diff_input": [], "errors": []}
    for inp, ln in zip(inputs, lines, strict=True):
        if ln.startswith("ERROR"):
            res["errors"].append(inp["seeds"][0])
            continue
        got = json.loads(ln)
        if inp.get("agg"):
            e0 = cmp.digest([exp[str(s)][0] for s in inp["seeds"]])
            e1 = cmp.digest([exp[str(s)][1] for s in inp["seeds"]])
            res["compared"] += len(inp["seeds"])
            if got[1] != e1:
                res["diff_input"].append(inp["seeds"][0])
            elif got[0] != e0:
                res["diff_result"].append(inp["seeds"][0])
            else:
                res["equal"] += len(inp["seeds"])
            continue
        assert len(got) == 2 * len(inp["seeds"])
        for j, s in enumerate(inp["seeds"]):
            e = exp[str(s)]
            res["compared"] += 1
            if got[2 * j + 1] != e[1]:
                res["diff_input"].append(s)
            elif got[2 * j] != e[0]:
                res["diff_result"].append(s)
            else:
                res["equal"] += 1
    (WORK / f"{name}.result.json").write_text(json.dumps(res, indent=1))
    print(res)


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(*(int(a) for a in sys.argv[2:6]), *sys.argv[6:7])
    else:
        compare(*sys.argv[2:3])
