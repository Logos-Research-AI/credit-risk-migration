"""Fidelity pass 2026-11-20, third attempt (label train-b): def:train_run_03_fit_global_rsquare evaluated in Lean
through the carrier def:zz_carrier_fid_2 (decl zz_carrier_fid_2), against the Python suite of fz10_train_run_03_gen.py
(CURRENT train.py:163-292, port HEAD 4a757fb, real sas_compat._kept / _solve_sas / _left_out / global_wald).

The Lean case of seed s is fz3_s03_gen's `mk` with the two differences of fz10_train_run_03_gen.py:
  - X28 frame: for hsh(s, 900) % 3 != 0, column d := a + b (when d is in the frame) and, when hsh(s, 901) % 2 == 0,
    column c := a; computed on the generated cells (float add), as x28_frame does;
  - stepwise.final := the last step's fit (none when there is no step), as py_case passes it.
Per chunk of seeds, each input returns  [W (iw of the kept seeds), ow of each kept seed..., ow of each linalg seed...]
  iw = digest of the generated inputs (generator mirror), ow = digest of the unit's output pairs (W (len :: TDN ...)).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_train_run_03_gen.py --inputs A B CH
      writes work/fz10c_train_run_03.inputs.json (one input per chunk of CH seeds) and work/fz10c_train_run_03.exp.json
  ... --cmp OUT.txt      compares the eval outputs (one line per input) with the expected lists
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz3_s03_gen as f3  # noqa: E402
import fz10_train_run_03_gen as g  # noqa: E402
import t18_gen as t  # noqa: E402

W = HERE.parent / "work"

OLD_FF = ('let ff : Pl.Frame Float := cols.map (fun (c : String) => (c, Pl.Col.f64 ((colv s (P4.idxOf c) n).map some))); ')
NEW_FF = ('let bv := fun (c : String) => colv s (P4.idxOf c) n; let x28 : Bool := (hsh s 900) % 3 != 0; '
          'let cv := fun (c : String) => (if x28 && c == "d" then List.zipWith (fun (x y : Float) => x + y) (bv "a") (bv "b") '
          'else if x28 && c == "c" && (hsh s 901) % 2 == 0 then bv "a" else bv c); '
          'let ff : Pl.Frame Float := cols.map (fun (c : String) => (c, Pl.Col.f64 ((cv c).map some))); ')
OLD_SW = ("let SWof := fun (sts : List (List String × List Float × List (List Float) × Float)) => ({ steps := sts.mapIdx ")
NEW_SW = ("let SWof := fun (sts : List (List String × List Float × List (List Float) × Float)) => (let sl : List (StepwiseStep Float) := sts.mapIdx ")
OLD_SWE = (" } : StepwiseStep Float)) } : StepwiseResult Float); ")
NEW_SWE = (" } : StepwiseStep Float)); ({ steps := sl, final := sl.getLast?.map (fun (z : StepwiseStep Float) => z.fit) } : StepwiseResult Float)); ")

assert f3.LEAN_PRE.count(OLD_FF) == 1 and f3.LEAN_PRE.count(OLD_SW) == 1 and f3.LEAN_PRE.count(OLD_SWE) == 1
PRE = f3.LEAN_PRE.replace(OLD_FF, NEW_FF).replace(OLD_SW, NEW_SW).replace(OLD_SWE, NEW_SWE)
assert PRE.count(f3.LEAN_TRIP) == 1
PRE = PRE.replace(f3.LEAN_TRIP, "")  # trip / blk are not used here
CLS = {"dropped": "0", "kept": "1", "rejected": "2", "linalg": "3"}


def case_x28(s):
    c = f3.case(s)
    c["frame"], _ = g.x28_frame(s, c["frame"])
    return c


def lean_input(a, b, cls):
    ks = (f'let cl : String := "{cls}"; let ids := fun (c : Char) => ((List.range cl.length).zip cl.toList).filterMap '
          f'(fun (p : Nat × Char) => if p.2 == c then some ({a} + p.1) else none); ')
    return "(" + PRE + ks + "([W ((ids '1').map iw)] ++ (ids '1').map ow ++ (ids '3').map ow))"


def main():
    if sys.argv[1] == "--all":
        # one input per chunk of CH seeds, every seed (no class string): [iw s, ow s] for s in A .. A+CH-1;
        # only the kept and linalg seeds are compared (the others are outside the precondition)
        a, ch = int(sys.argv[2]), int(sys.argv[3])
        print("(" + PRE + f"((List.range {ch}).flatMap (fun (i : Nat) => [iw ({a} + i), ow ({a} + i)])))")
        return
    if sys.argv[1] in ("--sweep", "--sweepcmp"):
        # one input over seeds A..B-1: per chunk of CH seeds, W [iw s, ow s for s kept (1) or linalg (3)]
        a, b, ch = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
        py = json.loads((W / "fz10_train_run_03.py.json").read_text())
        cls = "".join(CLS[py[str(s)]["cls"]] for s in range(a, b))
        if sys.argv[1] == "--sweep":
            mask = sum(1 << (s - a) for s in range(a, b) if cls[s - a] in "13")
            print("(" + PRE + f"let MASK : Nat := {hex(mask)}; "
                  f"((List.range (({b - a} + {ch} - 1) / {ch})).map (fun (j : Nat) => W (((List.range {ch}).filter (fun (i : Nat) => "
                  f"j * {ch} + i < {b - a} && MASK.testBit (j * {ch} + i))).flatMap (fun (i : Nat) => "
                  f"[iw ({a} + j * {ch} + i), ow ({a} + j * {ch} + i)])))))")
            return
        exp = []
        for lo in range(a, b, ch):
            ss = [s for s in range(lo, min(b, lo + ch)) if cls[s - a] in "13"]
            exp.append((lo, t.w([x for s in ss for x in (f3.in_digest(case_x28(s)), py[str(s)]["digest"])]), len(ss)))
        got = json.loads(Path(sys.argv[5]).read_text().strip())
        assert len(got) == len(exp), (len(got), len(exp))
        bad = [(lo, n) for (lo, e, n), g_ in zip(exp, got) if e != g_]
        print(f"seeds {a}..{b - 1}: chunks {len(exp)}, compared seeds {sum(n for _, _, n in exp)} "
              f"(kept {cls.count('1')}, linalg {cls.count('3')}), chunk flags differing {len(bad)}: {bad}")
        return
    if sys.argv[1] == "--cmpall":
        from collections import Counter
        py = json.loads((W / "fz10_train_run_03.py.json").read_text())
        a = int(sys.argv[3])
        got = json.loads(Path(sys.argv[2]).read_text().strip())
        st, bad = Counter(), []
        for k in range(len(got) // 2):
            s = a + k
            v = py[str(s)]
            iw = f3.in_digest(case_x28(s))
            if got[2 * k] != iw:
                bad.append((s, "input digest", got[2 * k], iw))
            if v["cls"] in ("kept", "linalg"):
                st[v["cls"]] += 1
                if got[2 * k + 1] != v["digest"]:
                    bad.append((s, v["cls"], "output digest", got[2 * k + 1], v["digest"]))
            else:
                st[v["cls"] + "_not_compared"] += 1
        print(a, a + len(got) // 2, dict(st), "differences", len(bad))
        for x in bad:
            print(x)
        return
    if sys.argv[1] == "--inputs":
        a, b, ch = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
        py = json.loads((W / "fz10_train_run_03.py.json").read_text())
        inputs, exp = [], []
        for lo in range(a, b, ch):
            hi = min(b, lo + ch)
            cls = "".join(CLS[py[str(s)]["cls"]] for s in range(lo, hi))
            kept = [s for s in range(lo, hi) if cls[s - lo] == "1"]
            lin = [s for s in range(lo, hi) if cls[s - lo] == "3"]
            inputs.append(lean_input(lo, hi, cls))
            exp.append({"lo": lo, "hi": hi, "kept": kept, "linalg": lin,
                        "values": [t.w([f3.in_digest(case_x28(s)) for s in kept])] + [py[str(s)]["digest"] for s in kept + lin]})
        (W / "fz10c_train_run_03.inputs.json").write_text(json.dumps(
            [{"item": "def:zz_carrier_fid_2", "decl": "zz_carrier_fid_2", "inputs": inputs}]))
        (W / "fz10c_train_run_03.exp.json").write_text(json.dumps(exp))
        print(len(inputs), "inputs; chars per input", max(len(x) for x in inputs))
    elif sys.argv[1] == "--one":
        print(json.loads((W / "fz10c_train_run_03.inputs.json").read_text())[0]["inputs"][int(sys.argv[2])])
    elif sys.argv[1] == "--cmp":
        exp = json.loads((W / "fz10c_train_run_03.exp.json").read_text())
        lines = [ln.strip() for ln in Path(sys.argv[2]).read_text().splitlines() if ln.strip()]
        assert len(lines) == len(exp), (len(lines), len(exp))
        nk = nl = nin = 0
        bad = []
        for e, ln in zip(exp, lines):
            got = json.loads(ln)
            if len(got) != len(e["values"]):
                bad.append((e["lo"], "length", len(got), len(e["values"])))
                continue
            if got[0] != e["values"][0]:
                bad.append((e["lo"], "input digest"))
            nin += 1
            for s, x, y in zip(e["kept"] + e["linalg"], got[1:], e["values"][1:]):
                if x != y:
                    bad.append((s, "output digest", x, y))
            nk += len(e["kept"])
            nl += len(e["linalg"])
        print("chunks", nin, "kept compared", nk, "linalg compared", nl, "differences", len(bad))
        for x in bad:
            print(x)


if __name__ == "__main__":
    main()
