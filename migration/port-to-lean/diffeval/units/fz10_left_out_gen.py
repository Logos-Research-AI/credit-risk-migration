"""Fidelity pass 2026-11-20 (label train-b): def:_left_out (sas_compat.py:814-817, port HEAD 4a757fb).

Cases: those of fz5_left_out_gen.py (loaded unchanged): seed s has n = 0..7 names from a pool with repeats
("Intercept", "age", "x", "", "age"), a cov of R x C >= n x n (R, C = n .. n + 2) with entries from the edge pool
0.0, -0.0, NaN, inf, -inf, 5e-324, -5e-324, 1.0, 1e-300 (60 %) or random exponents; the precondition
def:_left_out_precond (cov 2-D with a row i holding an entry i for every name position i) holds by construction.

No carrier item exists and none may be added; _left_out takes no function argument and the only items that call it
(train_run_03_fit_global_rsquare, run_py_py_py) return Tabular.Table values that eval_decl cannot print. So the
cases are evaluated through _left_out itself, packed: one eval_decl input is ONE LogisticFit holding the cases
s0 .. s0+k-1 side by side (fz5_left_out_gen.super_input): row (case j, i) = 1.0 repeated offset(j) times, then the
case's own cov row i (C entries), so that entry (g, g) of the packed cov, g = offset(j) + i, is the case's cov[i][i].
Names carry Python's verdict: position g is named "x" when the REAL sas_compat._left_out of case j (its own names
and cov, as a LogisticFit with numpy arrays) lists position i, else "y<8 s + i>". The label string is embedded in the
input; the matrix is built inside Lean from hsh. Lean equals Python on all cases iff the output is exactly the list
of N copies of "x", N = the number of positions Python leaves out (a "y.." in the output: Lean left out a position
Python keeps; fewer "x": Lean kept one Python leaves out). Python is also run on the packed fit and must give the
same list (checked here).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_left_out_gen.py
      writes work/fz10_left_out.inputs.json (seeds 0..1999, 10 inputs of 200); --show K; --cmp
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz5_left_out_gen as lo5  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

W = HERE.parent / "work"
K, N = 200, 2000


def labels(s0, k):
    lab = []
    for s in range(s0, s0 + k):
        n, R, C, names, cov, lo, toks = lo5.case(s)
        fit = sc.LogisticFit(list(names), np.zeros(n), cov, 0.0, 0, True)
        pos = [i for i in range(n) if float(cov[i, i]) == 0.0]
        assert [names[i] for i in pos] == sc._left_out(fit)  # pyright: ignore[reportPrivateUsage]
        lab += ["1" if i in pos else "0" for i in range(n)]
    return "".join(lab)


def packed_python(s0, k, lab):
    """the REAL _left_out on the packed fit (the same values the Lean builds)"""
    cases = [lo5.case(s) for s in range(s0, s0 + k)]
    offs, o = [], 0
    for c in cases:
        offs.append(o)
        o += c[0]
    width = max([offs[j] + cases[j][2] for j in range(k)] + [0])
    rows, names, g = [], [], 0
    for j, c in enumerate(cases):
        n, R, C, nm, cov = c[0], c[1], c[2], c[3], c[4]
        for i in range(n):
            r = [1.0] * offs[j] + [float(v) for v in cov[i]]
            rows.append(r + [0.0] * (width - len(r)))
            names.append("x" if lab[g] == "1" else f"y{8 * (s0 + j) + i}")
            g += 1
    cov = np.array(rows, dtype=np.float64).reshape(len(rows), width) if rows else np.zeros((0, 0))
    return sc._left_out(sc.LogisticFit(names, np.zeros(len(names)), cov, 0.0, 0, True))  # pyright: ignore[reportPrivateUsage]


def lean_input(s0, k, lab):
    gf = kit.GEN.split("let gI")[0]
    return ("(" + gf + "let E : List (Option Float) := [" + ", ".join(f"some {lt.lean_float(e)}" for e in lo5.E) + "]; "
            f'let LAB : List Char := "{lab}".toList; '
            "let cs := fun (s : Nat) => "
            "let n := ((hsh s 1 >>> 20) % 8).toNat; let R := n + ((hsh s 2 >>> 20) % 3).toNat; let C := n + ((hsh s 3 >>> 20) % 3).toNat; "
            "let v := (gF (s + 1000) (R * C) 60 20 E).map (fun (o : Option Float) => o.getD 0.0); "
            "(n, (List.range R).map (fun (i : Nat) => (List.range C).map (fun (j : Nat) => v.getD (i * C + j) 0.0))); "
            f"let all := (List.range {k}).map (fun (j : Nat) => cs ({s0} + j)); "
            f"let offs := (List.range {k}).map (fun (j : Nat) => ((all.take j).map (fun p => p.1)).foldl (fun a b => a + b) 0); "
            f"let nms : List String := (List.range {k}).flatMap (fun (j : Nat) => (List.range (all.getD j (0, [])).1).map (fun (i : Nat) => "
            f'if LAB.getD (offs.getD j 0 + i) (Char.ofNat 48) == (Char.ofNat 49) then "x" else "y" ++ toString (8 * ({s0} + j) + i))); '
            f"let rws : List (List Float) := (List.range {k}).flatMap (fun (j : Nat) => (List.range (all.getD j (0, [])).1).map (fun (i : Nat) => List.replicate (offs.getD j 0) 1.0 ++ ((all.getD j (0, [])).2.getD i []))); "
            "({ names := nms, beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 rws, loglik := 0.0, n_iter := 0, converged := true } : LogisticFit Float))")


def main():
    if sys.argv[1:2] == ["--show"]:
        print(json.loads((W / "fz10_left_out.inputs.json").read_text())[int(sys.argv[2])]["input"])
        return
    if sys.argv[1:2] == ["--cmp"]:
        ins = json.loads((W / "fz10_left_out.inputs.json").read_text())
        outs = (W / "fz10_left_out.out.txt").read_text().splitlines()
        tot = bad = 0
        for c, o in zip(ins, outs):
            got = json.loads(o)
            tot += c["count"]
            if got != ["x"] * c["n_left_out"]:
                bad += 1
                print("DIFF input", c["start"], "expected", c["n_left_out"], "x; got", got)
        print(json.dumps({"cases": tot, "differing_inputs": bad, "inputs": len(ins), "outputs": len(outs)}))
        return
    out = []
    from collections import Counter
    st = Counter()
    for s0 in range(0, N, K):
        lab = labels(s0, K)
        assert packed_python(s0, K, lab) == ["x"] * lab.count("1")
        t = lean_input(s0, K, lab)
        out.append({"item": "def:_left_out", "decl": "_left_out", "start": s0, "count": K, "positions": len(lab),
                    "n_left_out": lab.count("1"), "input": t})
        print(s0, len(t), len(lab), lab.count("1"))
    for s in range(N):
        n, R, C, names, cov, lo, toks = lo5.case(s)
        st[f"n={n}"] += 1
        st["some left out" if lo else "none left out"] += 1
        st["R>n"] += R > n
        st["C>n"] += C > n
        st["diag -0.0"] += any(float(cov[i, i]) == 0.0 and np.signbit(cov[i, i]) for i in range(n))
        st["diag NaN"] += any(cov[i, i] != cov[i, i] for i in range(n))
    print(dict(st))
    (W / "fz10_left_out.inputs.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
