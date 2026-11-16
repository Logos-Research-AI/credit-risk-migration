"""Per-seed evaluation of the blocks of fz_run_py_py that differ (same lets, one case per seed).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_run_py_py_bisect.py 30925 31300 31375
"""
import json, shutil, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz_run_py_py_gen as g
from suite import Suite

def main():
    starts = [int(a) for a in sys.argv[1:]]
    seeds = [s for a in starts for s in range(a, a + g.CH)]
    base = Path(tempfile.mkdtemp(prefix="fz_bis_"))
    cases, keep = [], []
    for s in seeds:
        rec = g.pyrun(s, base / str(s))
        if rec["outcome"].startswith("raises") or not g.precond(s, rec):
            continue
        keep.append(s)
        cases.append((f"seed {s} ({rec['outcome']})", g.U, g.expected(rec), {"fz": "kept"}))
    shutil.rmtree(base, ignore_errors=True)
    # the doubles as in the main generator
    old = json.loads((HERE.parent / "work" / "fz_run_py_py.inputs.json").read_text())[0]["inputs"][0]
    lets_text = old[1:old.index("(let X : List Nat")]
    st = Suite("fz_run_py_py_bisect")
    st.item, st.decl = g.ITEM, g.DECL
    st.inputs.append({"mode": "ints", "item": st.item, "decl": st.decl, "carrier": "identity",
                      "text": "(" + lets_text + f"({keep} : List Nat).map E)"})
    for pos, c in enumerate(cases):
        st.cases.append({"id": f"{st.name}/{c[0]}", "primitive": c[1], "input": 0, "pos": pos, "kind": "int", "expected": c[2], **c[3]})
    st.write()
    print(st.inputs[0]["text"][-700:])

main()
