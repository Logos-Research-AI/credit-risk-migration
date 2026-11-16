"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md), by port-translator-11 (assigned by port-translator-1:
no reviewer on the ring; the author is port-translator-9):
  def:train_run_05_association   credit_risk/train.py:279-312
  def:train_run_13_roc           credit_risk/train.py:681-690

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_train_05_13_gen.py
  (eval_decl each input of diffeval/work/fz_tr0513.inputs.json on def:zz_carrier_t, ONE input per call)
  python3 diffeval/fuzz_collect.py 11 fz_tr0513 ; compare.py ; python3 diffeval/fuzz_receipt.py fz_tr0513

Both units are wrappers over association_table / roc_association, fuzzed directly in fz_t1_gen.py
(port-translator-3). The column generators of that file are reused unchanged (YC: default_flag,
SC: pd_logistic, built INSIDE Lean from the seed and mirrored by kit.gF / gI): Float64 with null, NaN,
-0.0, 2, 0.5; Int64 with nulls; Boolean; Null dtype; scores on a grid with offsets of the size of
_SE_EPS (1e-13 scale) and _TIE_EPS (1e-9 scale), edges, random; rows 0..40. What this file adds is
the wrapper: the FRAME. FR s holds the two columns under their names, alone or with a third column
"x" (Int64) before / between them, in three orders chosen by the seed (the wrapper must pick the
columns by name). One case digests 25 seeds ("covers").

  step 13  train frame FR s, validation frame FR (s + 500000); result: both one-row frames (labels
           "Training Set" / "Validation Set"). Expected: source lines 681-690 executed verbatim.
           math.fsum = the Lean `let` FS of fz_t1_gen (CPython's algorithm), whose Python mirror is
           asserted equal to math.fsum on every list the port passes in this run.
  step 05  result: ("printed_association.csv", the 4 x 6 table of text cells). Expected: source lines
           279-312 executed verbatim, write_sas_csv replaced by a recorder of (frame, file name).
           The formatters, two parts:
           A (suite cases "05A", the bulk): fmt_wd and sas_d12_3 are replaced ON BOTH SIDES by the
             same injective text of their arguments ("9.1:<bits>", "d:<bits>", "n" for None). The
             Python stand-in still calls the real function first (so a raise would be seen). This
             checks which statistic goes to which cell with which width, for every generated value;
             a typed table of the real texts for 2,000 seeds would be about 1 MB of eval input.
           B (cases "05B"): the real fmt_wd / sas_d12_3 as typed lookup tables (an argument that
             Python never passed gives "?"), on the seeds with at most 5 rows of a short range.

Preconditions rendered in Python:
  train_run_05_association_precond  distinct names, one common length (true of any pl.DataFrame),
      both columns present (always here), association_table_precond = equal lengths and each dtype
      in Float64 / Int64 / Boolean / Null (fz_t1_gen.pre_pairs)
  train_run_13_roc_precond          the same frame clauses for both frames, and
      roc_association_precond on each (fz_t1_gen.pre_roc: pre_pairs and not (s10 + s01 < 0))
A seed whose two generated columns have different lengths (1 in 25) cannot be a pl.DataFrame: the
precondition rejects it (common length) and Python raises: dropped, as in fz_t1_gen.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import b4_gen as b4  # noqa: E402
import fz_t1_gen as t1  # noqa: E402  (also puts the checked math.fsum in place)
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

ITEM, DECL = "def:zz_carrier_t", "zz_carrier_t"
U05, U13 = "train_run_05_association", "train_run_13_roc"
w, ts, raw = b4.w, b4.ts, b4.raw
h = t1.h
D, CH = 500000, 25
S13, S05, SB = 20000, 30000, 40000
N13, N05, NB = 2300, 2200, 400
NANB = 0x7FF8000000000000

LINES = Path(train.__file__).read_text().splitlines(keepends=True)
SRC05 = textwrap.dedent("".join(LINES[278:312]))
SRC13 = textwrap.dedent("".join(LINES[680:690]))
assert SRC05.startswith("assoc = sas_compat.association_table(") and SRC05.rstrip().endswith('formats={})')
assert SRC13.startswith("roc_train = sas_compat.roc_association(") and SRC13.rstrip().endswith(")") and "Validation Set" in SRC13


def equal_len(s: int) -> bool:
    return h(s, 1003) % 25 != 0


def frame(s: int) -> pl.DataFrame:
    y, p = t1.y_col(s).alias("default_flag"), t1.s_col(s).alias("pd_logistic")
    x = pl.Series("x", kit.gI(s, t1.nn(s), 0, 5, 0), dtype=pl.Int64)
    k = h(s, 1010) % 3
    return pl.DataFrame([y, p] if k == 0 else [p, x, y] if k == 1 else [x, y, p])


FR = ("let FR := fun (s : Nat) => (match h s 1010 % 3 with "
      '| 0 => [("default_flag", YC s), ("pd_logistic", SC s)] '
      '| 1 => [("pd_logistic", SC s), ("x", Pl.Col.int (gI s (nn s) 0 5 0)), ("default_flag", YC s)] '
      '| _ => [("x", Pl.Col.int (gI s (nn s) 0 5 0)), ("default_flag", YC s), ("pd_logistic", SC s)] : Pl.Frame Float); '
      "let EQ := fun (s : Nat) => h s 1003 % 25 != 0; ")
TT = ("let tt := fun (t : Tabular.Table Float) => (t.length : Int) :: t.flatMap (fun (r : Tabular.Row Float) => (r.length : Int) :: "
      "r.flatMap (fun (p : String × Tabular.Cell Float) => ts p.1 ++ (match p.2 with | .str (some s) => 1 :: ts s | .str none => [0] | .num _ => [9] : List Int))); ")
ENC = ('let en := fun (x : Option Float) => (match x with | none => "n" | some v => toString v.toBits.toNat); '
       'let FW := fun (x : Option Float) (a b : Int) => toString a ++ "." ++ toString b ++ ":" ++ en x; '
       'let D3 := fun (x : Option Float) => "d:" ++ en x; ')


def en(x) -> str:
    if x is None:
        return "n"
    x = float(x)
    return str(NANB if x != x else raw(x))


def pre05(df: pl.DataFrame) -> bool:
    return (len(set(df.columns)) == df.width and {"default_flag", "pd_logistic"} <= set(df.columns)
            and t1.pre_pairs(df["default_flag"], df["pd_logistic"]))


def pre13(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return all(len(set(f.columns)) == f.width and {"default_flag", "pd_logistic"} <= set(f.columns)
               and t1.pre_roc(f["default_flag"], f["pd_logistic"]) for f in (a, b))


def run13(a: pl.DataFrame, b: pl.DataFrame) -> int:
    ns = dict(vars(train))
    ns.update(risk_scores_train=a, risk_scores_validation=b)
    exec(compile(SRC13, "train.py:681-690", "exec"), ns)  # noqa: S102
    return w(b4.frame_tok(ns["roc_train"]) + b4.frame_tok(ns["roc_valid"]))


def run05(df: pl.DataFrame, real: dict | None) -> int:
    """real None: part A (injective stand-ins); a dict: part B, records the real texts."""
    got: list = []
    o_w, o_d, o_csv = sc.fmt_wd, sc.sas_d12_3, sc.write_sas_csv

    def f_w(x, a, b):
        r = o_w(x, a, b)
        if real is None:
            return f"{a}.{b}:{en(x)}"
        assert real["w"].setdefault((None if x is None else raw(x), a, b), r) == r and float(x if x is not None else 0) == float(x if x is not None else 0)
        return r

    def f_d(x):
        r = o_d(x)
        if real is None:
            return "d:" + en(x)
        assert real["d"].setdefault(None if x is None else raw(x), r) == r
        return r

    sc.fmt_wd, sc.sas_d12_3, sc.write_sas_csv = f_w, f_d, (lambda df_, path, formats: got.append((df_, Path(path).name, formats)))
    try:
        ns = dict(vars(train))
        ns.update(fit_scored=df, output_dir=Path("out"))
        exec(compile(SRC05, "train.py:279-312", "exec"), ns)  # noqa: S102
    finally:
        sc.fmt_wd, sc.sas_d12_3, sc.write_sas_csv = o_w, o_d, o_csv
    (pa, name, formats), = got
    assert formats == {} and all(t == pl.String for t in pa.dtypes)
    toks = ts(name) + [pa.height]
    for row in pa.iter_rows():
        toks.append(pa.width)
        for cname, cell in zip(pa.columns, row):
            toks += ts(cname) + ([0] if cell is None else [1] + ts(cell))
    return w(toks)


def chunked(seeds: list[int], value) -> list[tuple[list[int], int]]:
    """seeds grouped by their chunk of CH consecutive seed numbers -> (kept seeds of the chunk, digest)"""
    out = []
    for a0 in range(seeds[0] - (seeds[0] % CH), seeds[-1] + 1, CH):
        c = [s for s in seeds if a0 <= s < a0 + CH]
        out.append((c, w([value[s] for s in c])))
    return out


def main() -> None:
    st = Suite("fz_tr0513")
    st.item, st.decl = ITEM, DECL
    fuzz = {"fuzzer": "port-translator-11", "generator": "diffeval/units/fz_train_05_13_gen.py", "units": {}}
    base = t1.BASE + t1.COLS + b4.OF + b4.TS + b4.TCOL + FR

    # ---------------- step 13
    val, raises, rej, dropped = {}, [], [], 0
    for s in range(S13, S13 + N13):
        if not (equal_len(s) and equal_len(s + D)):
            dropped += 1
            continue
        a, b = frame(s), frame(s + D)
        ok = pre13(a, b)
        try:
            v = run13(a, b)
        except Exception as e:  # noqa: BLE001
            (raises if ok else [None]).append(s)
            print("13 raises", s, ok, type(e).__name__, e)
            continue
        if not ok:
            rej.append(s)
        val[s] = v
    assert not rej and not raises, (rej[:5], raises[:5])
    kept13 = sorted(val)
    chs = chunked(kept13, val)
    lets = base + t1.FS_LET + (
        "let tf := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2); "
        f"let R := fun (s : Nat) => let r := train_run_13_roc (α := Float) FS (FR s) (FR (s + {D})); W (tf r.1 ++ tf r.2); ")
    body = (f"(List.range {len(chs)}).map (fun (i : Nat) => W (((List.range' ({S13} + {CH} * i) {CH}).filter "
            f"(fun (s : Nat) => EQ s && EQ (s + {D}))).map R))")
    st.ints(lets, body, [(f"13 seeds {S13 + CH * i}..{S13 + CH * i + CH - 1}", U13, v, {"fz": "kept", "covers": len(c)})
                         for i, (c, v) in enumerate(chs)], gen=True, use_kit=False)
    fuzz["units"][U13] = {"seeds": f"{S13}..{S13 + N13 - 1}", "generated": N13, "kept": len(kept13),
                          "python_raises_inside_precondition": raises,
                          "note": f"{t1.POOLS}; frames: the two columns alone or with a third Int64 column before / between, three orders; "
                                  f"validation frame from seed + {D}; {dropped} seeds dropped (a frame with columns of unequal length: "
                                  "precondition rejects, Python raises)"}
    print(U13, "generated", N13, "kept", len(kept13), "dropped", dropped)

    # ---------------- step 05, part A
    val, raises, dropped = {}, [], 0
    for s in range(S05, S05 + N05):
        if not equal_len(s):
            dropped += 1
            continue
        df = frame(s)
        assert pre05(df)
        try:
            val[s] = run05(df, None)
        except Exception as e:  # noqa: BLE001
            raises.append(s)
            print("05 raises inside precondition", s, type(e).__name__, e)
    keptA = sorted(val)
    chs = chunked(keptA, val)
    R05 = "let R := fun (s : Nat) => let r := train_run_05_association (α := Float) FW D3 (FR s); W (ts r.1 ++ tt r.2); "
    body = (f"(List.range {len(chs)}).map (fun (i : Nat) => W (((List.range' ({S05} + {CH} * i) {CH}).filter EQ).map R))")
    st.ints(base + TT + ENC + R05, body,
            [(f"05A seeds {S05 + CH * i}..{S05 + CH * i + CH - 1}", U05, v, {"fz": "kept", "covers": len(c)}) for i, (c, v) in enumerate(chs)],
            gen=True, use_kit=False)
    dropA, raisesA = dropped, raises

    # ---------------- step 05, part B: the real formatters as typed tables, small frames
    seedsB = [s for s in range(SB, SB + NB) if equal_len(s) and t1.nn(s) <= 5]
    k0 = 0
    keptB = 0
    while k0 < len(seedsB):
        k1 = k0
        best = None
        while k1 < len(seedsB):
            real = {"w": {}, "d": {}}
            vals = {s: run05(frame(s), real) for s in seedsB[k0:k1 + 1]}
            tw = ", ".join(f"({'none' if k[0] is None else f'some {k[0]}'}, {k[1]}, {k[2]}, {json.dumps(v)})" for k, v in real["w"].items())
            td = ", ".join(f"({'none' if k is None else f'some {k}'}, {json.dumps(v)})" for k, v in real["d"].items())
            text = (f"let TW : List (Option UInt64 × Int × Int × String) := [{tw}]; let TD : List (Option UInt64 × String) := [{td}]; "
                    'let FW := fun (x : Option Float) (a b : Int) => (match TW.find? (fun (e : Option UInt64 × Int × Int × String) => '
                    'e.1 == x.map Float.toBits && e.2.1 == a && e.2.2.1 == b) with | some e => e.2.2.2 | none => "?"); '
                    'let D3 := fun (x : Option Float) => (match TD.lookup (x.map Float.toBits) with | some s => s | none => "?"); ')
            if best is not None and len(text) > 2600:
                break
            best = (k1 + 1, text, vals)
            k1 += 1
        k1, text, vals = best
        c = seedsB[k0:k1]
        body = f"[W (([{', '.join(map(str, c))}] : List Nat).map R)]"
        st.ints(base + TT + text + R05, body, [(f"05B seeds {c[0]}..{c[-1]} (real fmt_wd / sas_d12_3 tables)", U05, w([vals[s] for s in c]),
                                               {"fz": "kept", "covers": len(c)})], gen=True, use_kit=False)
        keptB += len(c)
        k0 = k1
        if len(st.inputs) >= 5:
            break
    fuzz["units"][U05] = {"seeds": f"{S05}..{S05 + N05 - 1} (A), {SB}.. (B)", "generated": N05 + keptB, "kept": len(keptA) + keptB,
                          "python_raises_inside_precondition": raisesA,
                          "note": f"{t1.POOLS}; frames as for step 13; part A ({len(keptA)} seeds): fmt_wd / sas_d12_3 replaced on both sides by "
                                  f"the same injective text of their arguments; part B ({keptB} seeds, at most 5 rows): the real fmt_wd / sas_d12_3 "
                                  f"as typed tables; {dropA} seeds dropped (unequal column lengths)"}
    print(U05, "A kept", len(keptA), "dropped", dropA, "B kept", keptB)
    st.write()
    (HERE.parent / "work" / "fz_tr0513.fuzz.json").write_text(json.dumps(fuzz, indent=1))
    print("math.fsum calls checked:", t1.FSUM_CALLS[0])
    for i, inp in enumerate(st.inputs):
        print(i, len(inp["text"]), "chars", len([c for c in st.cases if c["input"] == i]), "cases")


if __name__ == "__main__":
    main()
