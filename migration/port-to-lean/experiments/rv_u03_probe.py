"""Review of def:train_run_03_fit_global_rsquare (update 2026-11-17, changes d and e) by
port-translator-3, who did not write it. Inputs of the reviewer, not the author's.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/rv_u03_probe.py
      -> experiments/rv_u03_probe.inputs.json (the eval_decl inputs, item def:zz_carrier_t, blueprint 5365851c-...)
         experiments/rv_u03_probe.expected.json (what the port's lines give)
  ... python experiments/rv_u03_probe.py check
      -> takes the Lean outputs from the reviewer's session record (fuzz_collect.eval_results) and
         compares; writes experiments/rv_u03_probe.out.txt

Python side: the source lines train.py:154-268 executed as they stand, on a hand-made fit frame of
4 rows and hand-made step lists. Formatters = an injective encoding of their arguments (bits of
the float). np.linalg.solve and chi2_sf are replaced by exact stand-ins (sums and products of
small dyadic numbers, so no rounding and no dependence on the order of summation); `@` is numpy's,
exact on these data. math.log and math.exp are the real ones.
Lean side: the unit on the same arguments, the same encoding, the same stand-ins for solve and
chi2, plain sums for matmul / matvec / dot. The result is returned whole, as the characters of
one text: file name, then every row, every column name and every cell.
Scenarios:
  empty   no step                                   -> 1 file
  only0   one step with q == 0                      -> 3 files, two with no row
  mixed   q=1 (a), q=2 (b then a), q=0, q=1 (b)     -> 3 files
  intcol  as the first step of mixed, column a Int64 (Python runs; is the unit right there?)
"""
from __future__ import annotations

import json
import math
import struct
import sys
import textwrap
import types
from pathlib import Path

import numpy as np
import polars as pl

from credit_risk import train

HERE = Path(__file__).resolve().parent
FIRST, LAST = 154, 268
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"


def bits(x) -> str:
    return "N" if x is None else str(struct.unpack("<Q", struct.pack("<d", float(x)))[0])


def solve_py(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return np.array([float(b[i]) + sum(float(a[j, i]) * (j + 1) for j in range(a.shape[0])) for i in range(len(b))])


def run_slice(steps, frame, n_obs, y, m2ll0, ybar):
    src = Path(train.__file__).read_text().splitlines()
    assert src[FIRST - 1].strip() == 'fs_step: list[str] = ["0"]' and "printed_rsquare.csv" in src[LAST - 1]
    code = textwrap.dedent("\n".join(src[FIRST - 1:LAST]))
    writes = []
    proxy = types.SimpleNamespace(
        fmt_wd=lambda x, w, d: f"w{bits(x)}/{w}/{d}", sas_d12_3=lambda x: "t" + bits(x),
        sas_pvalue=lambda x: "p" + bits(x), chi2_sf=lambda x, df: float(x * 0.5 + df),
        write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())))

    class NP:
        linalg = types.SimpleNamespace(solve=solve_py)

        def __getattr__(self, k):
            return getattr(np, k)

    ns = {"sas_compat": proxy, "np": NP(), "pl": pl, "math": math, "output_dir": Path("out"),
          "stepwise": types.SimpleNamespace(steps=steps), "m2ll0": m2ll0, "n_obs": n_obs, "fit_frame": frame,
          "y_train": np.asarray(y, dtype=np.float64), "ybar": ybar}
    exec(compile(code, "train.py:154-268", "exec"), ns)  # noqa: S102
    return writes


def text(writes) -> str:
    out = []
    for name, df in writes:
        rows = [",".join(f"{c}={'<null>' if v is None else v}" for c, v in zip(df.columns, r, strict=True)) for r in df.rows()]
        out.append(name + "#" + ";".join(rows))
    return "\n".join(out)


def fl(x: float) -> str:
    return f"({x!r})" if x < 0 else repr(float(x))


def step_py(k, names, beta, cov, ll):
    fit = types.SimpleNamespace(names=names, beta=np.array(beta, dtype=np.float64), cov=np.array(cov, dtype=np.float64), loglik=ll)
    return types.SimpleNamespace(step=k, fit=fit)


def step_lean(k, names, beta, cov, ll) -> str:
    nm = "[" + ", ".join(f'"{n}"' for n in names) + "]"
    b = "[" + ", ".join(fl(v) for v in beta) + "]"
    c = "[" + ", ".join("[" + ", ".join(fl(v) for v in row) + "]" for row in cov) + "]"
    return f"S {k} {nm} {b} {c} {fl(ll)}"


PRE = (
    'let en := fun (x : Option Float) => (match x with | none => "N" | some v => toString v.toBits.toNat : String); '
    'let fw := fun (x : Option Float) (a b : Int) => "w" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
    'let d12 := fun (x : Option Float) => "t" ++ en x; let pv := fun (x : Option Float) => "p" ++ en x; '
    "let chi2 := fun (x : Float) (d : Int) => x * 0.5 + Float.ofInt d; "
    "let dot := fun (u v : List Float) => (List.zip u v).foldl (fun (s : Float) (p : Float × Float) => s + p.1 * p.2) 0.0; "
    "let matvec := fun (m : List (List Float)) (v : List Float) => m.map (fun r => dot r v); "
    "let matmul := fun (a b : List (List Float)) => a.map (fun r => (List.range (b.headD []).length).map "
    "(fun j => dot r (b.map (fun (br : List Float) => br.getD j 0.0)))); "
    "let solve := fun (a : List (List Float)) (b : List Float) => (List.range b.length).map (fun i => "
    "b.getD i 0.0 + ((List.range a.length).foldl (fun (s : Float) (j : Nat) => s + (a.getD j []).getD i 0.0 * Float.ofNat (j + 1)) 0.0)); "
    "let S := fun (k : Int) (nm : List String) (b : List Float) (c : List (List Float)) (ll : Float) => "
    "({ step := k, entered := none, removed := none, df := 1, number_in_model := 1, score_chisq := none, wald_chisq := none, "
    "p_value := 0.0, fit := { names := nm, beta := Np.NDArray.d1 b, cov := Np.NDArray.d2 c, loglik := ll, n_iter := 1, "
    "converged := true } } : StepwiseStep Float); "
    "let F := fun (ca : Pl.Col Float) => ([(\"a\", ca), (\"b\", Pl.Col.f64 [some 1.0, some 0.0, some 2.0, some 1.0]), "
    "(\"default_flag\", Pl.Col.f64 [some 0.0, some 1.0, some 0.0, some 1.0])] : Pl.Frame Float); "
    "let R := fun (st : List (StepwiseStep Float)) (ca : Pl.Col Float) => "
    "train_run_03_fit_global_rsquare (α := Float) fw d12 pv chi2 { steps := st } solve matmul matvec dot (F ca) 4 "
    "[0.0, 1.0, 0.0, 1.0] 6.0 0.5; "
    "let cs := fun (c : Tabular.Cell Float) => (match c with | .str (some s) => s | .str none => \"<null>\" | .num _ => \"<num>\" : String); "
    "let TX := fun (fs : List (String × Tabular.Table Float)) => ((String.intercalate \"\\n\" (fs.map (fun f => f.1 ++ \"#\" ++ "
    "String.intercalate \";\" (f.2.map (fun r => String.intercalate \",\" (r.map (fun p => p.1 ++ \"=\" ++ cs p.2))))))).toList.map "
    "(fun ch => (ch.toNat : Int))); "
)
AF = "(Pl.Col.f64 [some 0.0, some 1.0, some 1.0, some 2.0])"
AI = "(Pl.Col.int [some 0, some 1, some 1, some 2])"

S1 = (1, ["Intercept", "a"], [0.5, -0.25], [[1.0, 0.5], [0.25, 2.0]], -2.5)
S2 = (2, ["Intercept", "b", "a"], [0.5, 1.5, -0.25], [[1.0, 0.5, 0.25], [0.125, 2.0, -0.5], [4.0, 0.75, 1.0]], -2.0)
S3 = (3, ["Intercept"], [0.75], [[1.0]], -3.0)
S4 = (4, ["Intercept", "b"], [0.5, 2.0], [[1.0, 0.5], [0.25, 0.5]], -2.75)

SCEN = [
    ("empty", [], False),
    ("only0", [S3], False),
    ("mixed", [S1, S2, S3, S4], False),
    ("intcol", [S1], True),
]


def frame(intcol: bool) -> pl.DataFrame:
    a = pl.Series("a", [0, 1, 1, 2], dtype=pl.Int64) if intcol else pl.Series("a", [0.0, 1.0, 1.0, 2.0])
    return pl.DataFrame([a, pl.Series("b", [1.0, 0.0, 2.0, 1.0]), pl.Series("default_flag", [0.0, 1.0, 0.0, 1.0])])


def build():
    inputs, expected = [], []
    for name, steps, intcol in SCEN:
        w = run_slice([step_py(*s) for s in steps], frame(intcol), 4, [0.0, 1.0, 0.0, 1.0], 6.0, 0.5)
        expected.append({"scenario": name, "files": [n for n, _ in w], "text": text(w)})
        st = "[" + ", ".join(step_lean(*s) for s in steps) + "]"
        inputs.append("(" + PRE + f"TX (R {st} {AI if intcol else AF}))")
    return inputs, expected


def main():
    inputs, expected = build()
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.path.insert(0, str(HERE.parent / "diffeval"))
        import fuzz_collect

        res = fuzz_collect.eval_results("3")
        lines, bad = [], 0
        for inp, exp in zip(inputs, expected, strict=True):
            got = res.get(inp)
            if got is None:
                lines.append(f"{exp['scenario']}: NOT RUN")
                bad += 1
                continue
            lean = "".join(chr(int(v)) for v in got.strip("[]").split(",") if v.strip())
            if lean == exp["text"]:
                lines.append(f"{exp['scenario']}: EQUAL ({len(lean)} characters; files {exp['files']})")
            else:
                bad += 1
                lines.append(f"{exp['scenario']}: DIFFERENT")
                a, b = lean.replace("\n", ";").replace(";", ",").split(","), exp["text"].replace("\n", ";").replace(";", ",").split(",")
                lines.append(f"  cells lean {len(a)} python {len(b)}")
                for x, y in zip(a, b, strict=False):
                    if x != y:
                        lines.append(f"  lean {x} | python {y}")
        lines.append(f"blueprint {BLUEPRINT}; scenarios {len(inputs)}; not equal {bad}")
        (HERE / "rv_u03_probe.out.txt").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return
    (HERE / "rv_u03_probe.inputs.json").write_text(json.dumps({"blueprint": BLUEPRINT, "item": "def:zz_carrier_t", "inputs": inputs}, indent=1, ensure_ascii=False))
    (HERE / "rv_u03_probe.expected.json").write_text(json.dumps(expected, indent=1))
    for e, i in zip(expected, inputs, strict=True):
        print(e["scenario"], e["files"], len(e["text"]), "chars; input", len(i))
    print(inputs[0])
    for i in inputs[1:]:
        print("TAIL:", i[len("(" + PRE):])


main()
