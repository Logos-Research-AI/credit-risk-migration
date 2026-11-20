"""Fidelity pass 2026-11-20 (label stale-compositions): def:run (feature_engineering.run) as a whole
against the CURRENT Python (port HEAD 4a757fb: split change T0 included).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_run_gen.py [calls] [per call]
      -> diffeval/work/fz10_run.{json,inputs.json,fuzz.json}

Built on diffeval/units/fz_run_gen.py (2026-11-16, port-translator-8): same frames (modes 0-15, pools
of every threshold, edge cells, text columns, names, no known income), same Python side (the REAL
feature_engineering.run on the written files, write_sas_csv recorded), same digests, same rendered
precondition, plus no file and a header-only file. What changes, for the split change of 4a757fb:
  split file, mode m = hsh(s, 397) % 4:
    0, 1  as in 2026-11-16: each id of 1..n+2 with probability 1/2 (else [1] or no id): almost never
          (7n+9)//10 distinct present ids, so the real run takes the seeded draw (_split_draw)
    2, 3  a file that FITS: (7n+9)//10 distinct ids among 1..n, the ids (i + r) % n + 1 for
          i < n_train, r = hsh(s, 398) % n (the file is used as given)
  The Lean `sp` is replaced by the same rule; `run` (and fe_run_06_split inside it: MT19937 in Lean)
  must reproduce the draw.
Carrier: def:zz_carrier_f / zz_carrier_f as in 2026-11-16. ON 2026-11-20 NO zz_carrier_* ITEM EXISTS on
5365851c and eval_decl refuses def:run itself (call-level refusal, see the receipt): the suite is
generated and its Python side run, the Lean side is NOT evaluated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = [sys.argv[0]] + sys.argv[1:]
import fz_run_gen as g  # noqa: E402

OLD_SP = ("let sp := fun (s : Nat) => (let v := (List.range (nn s + 2)).filter (fun (i : Nat) => h s (400 + i) 2 == 0); "
          "(if v.isEmpty then (if h s 399 4 == 0 then [] else [0]) else v)")
NEW_SP = ("let sp := fun (s : Nat) => (let n := nn s; let nt := (7 * n + 9) / 10; "
          "let v := (List.range (n + 2)).filter (fun (i : Nat) => h s (400 + i) 2 == 0); "
          "(if h s 397 4 ≥ 2 then (List.range nt).map (fun (i : Nat) => (i + h s 398 n) % n) "
          "else if v.isEmpty then (if h s 399 4 == 0 then [] else [0]) else v)")
assert g.LETS.count(OLD_SP) == 1
g.LETS = g.LETS.replace(OLD_SP, NEW_SP)
_old_split = g.split
SPLIT_MODES: dict[str, int] = {"fits": 0, "draw": 0}


def split(s: int) -> list[float]:
    n = g.ROWS[g.h(s, 98, 8)]
    if g.h(s, 397, 4) >= 2:
        nt = (7 * n + 9) // 10
        r = g.h(s, 398, n)
        return [float((i + r) % n + 1) for i in range(nt)]
    return _old_split(s)


g.split = split


def main() -> None:
    calls = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    sys.argv = [sys.argv[0], str(calls), str(per), "fz10_run"]
    # seeds 1_000_000.. (fz_run_gen.main uses base0 = 80000: patch through its source constant)
    src = Path(g.__file__).read_text()
    assert "base0 = 80000" in src
    g.main.__globals__["__fz10_base"] = 1_000_000
    import types
    code = compile(src.replace("base0 = 80000", "base0 = 1_000_000")
                   .replace('generator="port-to-lean/diffeval/units/fz_run_gen.py"', 'generator="port-to-lean/diffeval/units/fz10_run_gen.py"')
                   .replace('"fuzzer": "port-translator-8", "generator": "diffeval/units/fz_run_gen.py"',
                            '"fuzzer": "port-translator (stale-compositions 2026-11-20)", "generator": "diffeval/units/fz10_run_gen.py", "blueprint": "5365851c-5549-44b7-9207-4bd4c422031d"'),
                   g.__file__, "exec")
    ns = types.ModuleType("fz10_run_impl")
    ns.__dict__["__name__"] = "fz10_run_impl"
    ns.__dict__["__file__"] = g.__file__
    exec(code, ns.__dict__)
    ns.LETS = g.LETS
    ns.split = split
    ns.main()
    # split modes of the generated seeds (for the note)
    fits = sum(1 for s in range(1_000_000, 1_000_000 + calls * per) if g.h(s, 397, 4) >= 2)
    fz = HERE.parent / "work" / "fz10_run.fuzz.json"
    d = json.loads(fz.read_text())
    d["units"]["run"]["note"] += (f"; SPLIT (4a757fb): {fits} seeds with a file that fits ((7n+9)//10 distinct present ids, "
                                  f"used as given), {calls * per - fits} with the 2026-11-16 subsets (the real run draws, seed 42)")
    fz.write_text(json.dumps(d, indent=1))


if __name__ == "__main__":
    main()
