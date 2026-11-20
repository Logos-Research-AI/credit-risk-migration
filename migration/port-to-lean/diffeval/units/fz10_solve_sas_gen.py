"""Fidelity pass 2026-11-20 (label train-b): def:_solve_sas, through the existing generator fz5_solve_sas_gen.py
(unchanged; see its docstring for the cases, the stand-in routines and the in-Lean sweep). The REAL
sas_compat._solve_sas / _kept of port HEAD run on the Python side.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_solve_sas_gen.py
      writes work/fz10_solve_sas.inputs.json: [{"item","decl","start","count","input","expected_chunks"}]
  ... fz10_solve_sas_gen.py --show K   prints the eval_decl input K
  ... fz10_solve_sas_gen.py --cmp      reads work/fz10_solve_sas.out.txt (one output line per input) and checks that
                                       every chunk flag is 0.0 (the Lean digest of 10 seeds x 2 solvers equals Python's)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz5_solve_sas_gen as g  # noqa: E402

RANGES = [(0, 500), (500, 1500)]
W = HERE.parent / "work"


def main():
    if sys.argv[1:2] == ["--show"]:
        print(json.loads((W / "fz10_solve_sas.inputs.json").read_text())[int(sys.argv[2])]["input"])
        return
    if sys.argv[1:2] == ["--cmp"]:
        ins = json.loads((W / "fz10_solve_sas.inputs.json").read_text())
        outs = (W / "fz10_solve_sas.out.txt").read_text().splitlines()
        tot = bad = 0
        for c, o in zip(ins, outs):
            vals = [float(x) for x in o.strip().strip("[]").split(",")]
            assert len(vals) == c["count"] // 10, (len(vals), c["count"])
            for k, v in enumerate(vals):
                tot += 10
                if v != 0.0:
                    bad += 1
                    print("DIFF chunk seeds", c["start"] + 10 * k, "..", c["start"] + 10 * k + 9, "lean digest", v)
        print(json.dumps({"seeds": tot, "differing_chunks": bad, "inputs": len(ins), "outputs": len(outs)}))
        return
    out = []
    for a, n in RANGES:
        text, exp = g.lean_input(a, n)
        out.append({"item": "def:_solve_sas", "decl": "_solve_sas", "start": a, "count": n, "input": text, "expected_chunks": exp})
        print(a, n, len(text), g.stats(a, n))
    (W / "fz10_solve_sas.inputs.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
