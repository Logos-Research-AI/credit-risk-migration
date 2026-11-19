"""Fuzz of def:_left_out (and def:_left_out_precond) by a non-author, blueprint 5365851c-...
  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_left_out_gen.py [detail S0 K]
Case s: n = (hsh(s,1)>>20)%8 names, name i = POOL[(hsh(s+5,i)>>20)%5]; R = n + (hsh(s,2)>>20)%3 rows,
C = n + (hsh(s,3)>>20)%3 columns (R,C >= n: inside the precondition; R = 0 or C = 0 occur at n = 0);
cov entries gF(s+1000, R*C, 60, 20, E) read row-major (E: 0.0, -0.0, NaN, inf, -inf, 5e-324, -5e-324, 1.0, 1e-300).
Result tokens: [count, then tS of each name]. Chunks of 100 cases are folded into one digest.
"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import kit, compare as cmp, leanterm as lt
from credit_risk import sas_compat as sc

POOL = ["Intercept", "age", "x", "", "age"]
nan, inf = float("nan"), float("inf")
E = [0.0, -0.0, nan, inf, -inf, 5e-324, -5e-324, 1.0, 1e-300]
h = kit.hsh
def tS(s): return [len(s)] + [ord(c) for c in s]
def case(s):
    n = (h(s, 1) >> 20) % 8
    R = n + (h(s, 2) >> 20) % 3
    C = n + (h(s, 3) >> 20) % 3
    names = [POOL[(h(s + 5, i) >> 20) % 5] for i in range(n)]
    v = kit.gF(s + 1000, R * C, 60, 20, list(E))
    cov = np.array(v, dtype=np.float64).reshape(R, C)
    fit = sc.LogisticFit(names, np.zeros(n), cov, 0.0, 0, True)
    lo = sc._left_out(fit)
    toks = [len(lo)] + [t for x in lo for t in tS(x)]
    return n, R, C, names, cov, lo, toks
def chunk_digest(s0, k):
    toks = []
    for s in range(s0, s0 + k):
        toks += case(s)[6]
        toks.append(999)
    return cmp.digest(toks)

LET = ('let pool : List String := ["Intercept", "age", "x", "", "age"]; '
       'let E : List (Option Float) := [' + ", ".join(f"some {lt.lean_float(e)}" for e in E) + ']; '
       'let one := fun (s : Nat) => '
       'let n := ((hsh s 1 >>> 20) % 8).toNat; let R := n + ((hsh s 2 >>> 20) % 3).toNat; let C := n + ((hsh s 3 >>> 20) % 3).toNat; '
       'let v := (gF (s + 1000) (R * C) 60 20 E).map (fun (o : Option Float) => o.getD 0.0); '
       'let rows : List (List Float) := (List.range R).map (fun (i : Nat) => (List.range C).map (fun (j : Nat) => v.getD (i * C + j) 0.0)); '
       'let nm : List String := (List.range n).map (fun (i : Nat) => pool.getD ((hsh (s + 5) i >>> 20) % 5).toNat ""); '
       'let fit : LogisticFit Float := { names := nm, beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 rows, loglik := 0.0, n_iter := 0, converged := true }; '
       'let lo := _left_out fit; '
       '(lo.length.toUInt64 :: lo.flatMap tS : List UInt64); ')
def term(s0, k):
    return (f"({kit.KIT_NOTABLE}{kit.GEN}{LET}"
            f"[dg ((List.range {k}).flatMap (fun (k : Nat) => one ({s0} + k) ++ [999]))])")
def detail(s0, k):
    return (f"({kit.KIT_NOTABLE}{kit.GEN}{LET}"
            f"(List.range {k}).map (fun (k : Nat) => dg (one ({s0} + k))))")
if __name__ == "__main__":
    if sys.argv[1:2] == ["detail"]:
        s0, k = int(sys.argv[2]), int(sys.argv[3])
        print(json.dumps({"input": detail(s0, k), "expected": [cmp.digest(case(s)[6]) for s in range(s0, s0 + k)]}))
    else:
        N, K = 2000, 100
        out = [{"s0": s0, "k": K, "input": term(s0, K), "expected": chunk_digest(s0, K)} for s0 in range(0, N, K)]
        (HERE.parent / "work").mkdir(exist_ok=True)
        Path(HERE.parent / "work" / "fz5_left_out.chunks.json").write_text(json.dumps(out))
        from collections import Counter
        print(Counter(len(case(s)[5]) > 0 for s in range(N)), "chunks", len(out))
        print(Counter(case(s)[0] for s in range(N)))


# ---- second mode (the evaluable form): eval_decl can only run a decl of the item itself, so one input is one
# `LogisticFit`. `super s0 k` packs the cases s0..s0+k-1 into one fit: names = toString (8 s + i), row (case j, i) =
# 1.0 * (offset of case j) ++ the case's own cov row i, so that entry (global g, g) is the case's cov[i,i].
def super_input(s0, k):
    gf = kit.GEN.split("let gI")[0]  # hsh and gF
    return ("(" + gf + 'let E : List (Option Float) := [' + ", ".join(f"some {lt.lean_float(e)}" for e in E) + ']; '
            'let cs := fun (s : Nat) => '
            'let n := ((hsh s 1 >>> 20) % 8).toNat; let R := n + ((hsh s 2 >>> 20) % 3).toNat; let C := n + ((hsh s 3 >>> 20) % 3).toNat; '
            'let v := (gF (s + 1000) (R * C) 60 20 E).map (fun (o : Option Float) => o.getD 0.0); '
            '(n, (List.range R).map (fun (i : Nat) => (List.range C).map (fun (j : Nat) => v.getD (i * C + j) 0.0))); '
            f'let all := (List.range {k}).map (fun (j : Nat) => cs ({s0} + j)); '
            f'let offs := (List.range {k}).map (fun (j : Nat) => ((all.take j).map (fun p => p.1)).foldl (fun a b => a + b) 0); '
            f'let nms : List String := (List.range {k}).flatMap (fun (j : Nat) => (List.range (all.getD j (0, [])).1).map (fun (i : Nat) => toString (8 * ({s0} + j) + i))); '
            f'let rws : List (List Float) := (List.range {k}).flatMap (fun (j : Nat) => (List.range (all.getD j (0, [])).1).map (fun (i : Nat) => List.replicate (offs.getD j 0) 1.0 ++ ((all.getD j (0, [])).2.getD i []))); '
            '({ names := nms, beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 rws, loglik := 0.0, n_iter := 0, converged := true } : LogisticFit Float))')
def super_expected(s0, k):
    out = []
    for s in range(s0, s0 + k):
        n, R, C, names, cov, lo, toks = case(s)
        out += [8 * s + i for i in range(n) if float(cov[i, i]) == 0.0]
    return out
