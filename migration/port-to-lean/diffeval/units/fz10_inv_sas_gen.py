"""Fidelity pass 2026-11-20 (label train-b): def:_inv_sas through the cases, stand-in routines and Lean lets of the
existing generator fz5_inv_sas_gen.py (loaded unchanged, its trailing main() call cut off). The REAL
sas_compat._inv_sas (and _kept) of port HEAD run on the Python side with np.linalg.solve / np.linalg.inv replaced
by the doubles solveG / invG; c @ x inside _kept is numpy's own (the Lean dotG is numpy's order for <= 4 terms,
checked on every call: `dotbad` must be 0).

Change against fz5: the verdict is computed inside Lean. Per chunk of 10 seeds, the per-seed digest dg(tokens of
the result) (full 64 bits, float bits, NaN canonical) is folded with mx; the input embeds the expected chunk
digests and the output is 0.0 for a chunk that equals Python, else the Lean chunk digest mod 2^52.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_inv_sas_gen.py
      writes work/fz10_inv_sas.inputs.json
  ... --show K   prints input K;   ... --cmp   reads work/fz10_inv_sas.out.txt
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
SRC = (HERE / "fz5_inv_sas_gen.py").read_text()
g: dict = {"__file__": str(HERE / "fz5_inv_sas_gen.py"), "__name__": "fz5_inv_sas_gen"}
exec(compile(SRC.rsplit("\nmain()", 1)[0], "fz5_inv_sas_gen.py", "exec"), g)  # noqa: S102

W = HERE.parent / "work"
RANGES = [(0, 700), (700, 700), (1400, 700)]
OFF = 14695981039346656037


def seed_dg(s):
    return g["dg"](g["toks"](g["run_py"](g["genCase"](s))))


def chunks(lo, n):
    out = []
    for c in range(n // 10):
        h = OFF
        for i in range(10):
            d = seed_dg(lo + c * 10 + i)
            h = (((h ^ d) * 1099511628211) & g["M64"])
            h = h ^ (h >> 32)
        out.append(h)
    return out


def lean_input(lo, n, exp):
    body = (f"let EXP : List UInt64 := [{', '.join(str(x) for x in exp)}]; "
            "let sd := fun (s : Nat) => dg (let res := _inv_sas invG solveG dotG (Np.NDArray.d2 (genCase s)); "
            "res.length.toUInt64 :: res.flatMap (fun (r : List Float) => r.length.toUInt64 :: r.map Float.toBits)); "
            f"(List.range {n // 10}).map (fun (c : Nat) => let h : UInt64 := ((List.range 10).map (fun (i : Nat) => sd ({lo} + c * 10 + i))).foldl mx 14695981039346656037; "
            "[if h == EXP.getD c 0 then 0.0 else Float.ofNat (h.toNat % 4503599627370496)])")
    return "(fun (_ : List (List Float)) => " + g["LETS"] + body + ")" + g["TAIL"]


def main():
    if sys.argv[1:2] == ["--show"]:
        print(json.loads((W / "fz10_inv_sas.inputs.json").read_text())[int(sys.argv[2])]["input"])
        return
    if sys.argv[1:2] == ["--cmp"]:
        ins = json.loads((W / "fz10_inv_sas.inputs.json").read_text())
        outs = (W / "fz10_inv_sas.out.txt").read_text().splitlines()
        tot = bad = 0
        for c, o in zip(ins, outs):
            vals = [float(x) for x in o.replace("[", " ").replace("]", " ").replace(",", " ").split()]
            assert len(vals) == c["count"] // 10
            for k, v in enumerate(vals):
                tot += 10
                if v != 0.0:
                    bad += 1
                    print("DIFF chunk seeds", c["start"] + 10 * k, "lean digest", v)
        print(json.dumps({"seeds": tot, "differing_chunks": bad, "inputs": len(ins), "outputs": len(outs)}))
        return
    out = []
    for lo, n in RANGES:
        exp = chunks(lo, n)
        t = lean_input(lo, n, exp)
        out.append({"item": "def:_inv_sas", "decl": "_inv_sas", "start": lo, "count": n, "input": t, "expected_chunks": exp})
        print(lo, n, len(t), "dot check", g["calls"])
    (W / "fz10_inv_sas.inputs.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
