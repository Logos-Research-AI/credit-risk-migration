"""Fidelity pass 2026-11-20, third attempt, label metrics: receipted re-run of the fz7_m composition fuzz
(diffeval/units/fz7_metrics_gen.py: metrics steps 01, 02, 04-10 of metrics_calculation.run composed as `run` composes
them, step 03 as the threshold_analysis input of 09) against the CURRENT port (HEAD 4a757fb), on def:zz_carrier_fid_2.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_m_gen.py [first count]
      -> work/fz10c_m.{json,inputs.json,fuzz.json}

The generator, the pools, the Python side (the REAL source of run cut by markers, executed with the module globals)
and the Lean composition are fz7_metrics_gen's, imported unchanged. Changed here only: the carrier (def:zz_carrier_fid_2),
the seeds (8_200_000..), and the case: one case = the digest (dgi) of the per-seed digests of a block of 25 seeds (each
seed digest is fz7's: dgi of the 12 unit digests of that seed), so that an input returns a short list. Seeds on which
Python raises in any unit are listed in EX and left out of the fold (none expected: fz7 had none).
Steps 01 / 02 / 04 are evaluated on their widened preconditions (lead, 2026-11-18: a validation frame with no row is
admitted): fz7's pre_roc / pre_rank render the current _precond items, and its generator gives 0-row frames (NS[0]).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
_argv, sys.argv = sys.argv, [sys.argv[0]]
import fz7_metrics_gen as f7  # noqa: E402
import suite as suite_mod  # noqa: E402
import compare as cmp  # noqa: E402
from suite import WORK, Suite  # noqa: E402

sys.argv = _argv
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
GENR = "diffeval/units/fz10c_m_gen.py"
B = 25


def main():
    first, count = (int(x) for x in (_argv[1:3] or [8_200_000, 2000]))
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")
    s = Suite("fz10c_m", generator=GENR)
    stat = {u_: {"kept": 0, "rejected": 0, "raises-kept": [], "raises-rejected": 0, "upstream": 0} for u_ in f7.UNITS}
    flav = {"empty_V": 0, "empty_T": 0}
    best: dict = {}
    seed_dg, EX = {}, []
    for seed in range(first, first + count):
        res, (nv, nt) = f7.python_seed(seed, best, None)
        flav["empty_V"] += nv == 0
        flav["empty_T"] += nt == 0
        for unit, (status, _) in zip(f7.UNITS, res):
            stt = stat[unit]
            if status in ("kept", "rejected"):
                stt[status] += 1
            elif status == "raises-kept":
                stt["raises-kept"].append(seed)
            elif status == "raises-rejected":
                stt["raises-rejected"] += 1
            else:
                stt["upstream"] += 1
        if any(d is None for _, d in res):
            EX.append(seed)
        else:
            seed_dg[seed] = cmp.digest([d for _, d in res])
    cases = []
    for b in range(count // B):
        lo = first + b * B
        part = [x for x in range(lo, lo + B) if x in seed_dg]
        cases.append((f"block seeds {lo}..{lo + B - 1} ({len(part)} seeds, all 12 unit results each)", "metrics",
                      cmp.digest([seed_dg[x] for x in part]), {"fz": "kept", "covers": len(part)}))
    # sas_best / float: fz7's two lookup tables (recorded from the real functions) folded into one, to shorten the input:
    # SB2 maps the bits of x to the bits of float(sas_best(x, 8)) where that text is not empty; sb x renders those bits as
    # decimal text ("" for every other x: the empty texts of the record, none included), pf reads the bits back. The
    # unit uses the pair only through _into_float (def:_into_float: emptiness of the text, then parse_float), so
    # pf (sb x) and the emptiness of sb x are those of the real functions on every recorded x.
    sb2 = [(k, cmp.fbits(float(v))) for k, v in best.items() if v]
    assert all(k is not None for k, _ in sb2)
    cases.append(("lookup table input check", "input-check", cmp.digest([t for k, r in sb2 for t in (k, r)]), {"fz": "kept"}))
    ex_ = "let EX : List Nat := [" + ", ".join(map(str, EX)) + "]; "
    body = (f"((List.range {count // B}).map (fun (b : Nat) => dgi (((List.range' ({first} + {B} * b) {B}).filter "
            "(fun (i : Nat) => !EX.contains i)).map (fun (i : Nat) => dgi (one i))))) ++ "
            "[dg (SB2.flatMap (fun (p : UInt64 × UInt64) => [p.1, p.2]))]")
    lets = f7.lean_lets(best)
    i, j = lets.index("let SB : "), lets.index("let sd8 := ")
    lets = (lets[:i] + "let SB2 : List (UInt64 × UInt64) := [" + ", ".join(f"({k}, {r})" for k, r in sb2) + "]; "
            'let sb := fun (x : Option Float) (_ : Int) => (match x with | none => "" | some v => (match SB2.lookup v.toBits with '
            '| some r => toString r | none => "")); let pf := fun (s : String) => Float.ofBits s.toNat!.toUInt64; ' + lets[j:])
    s.ints(ex_ + lets, body, cases, gen=True, table=True)
    s.write()
    (WORK / "fz10c_m.fuzz.json").write_text(json.dumps({"generator": GENR, "blueprint": BP, "seeds": f"{first}..{first + count - 1}",
                                                       "units": stat, "flavours": flav, "python_raises_seeds": EX}, indent=1))
    for k, v in stat.items():
        print(k, {a: (b_ if not isinstance(b_, list) else (len(b_), b_[:5])) for a, b_ in v.items()})
    print(flav, "EX", EX[:10])
    c = json.loads((WORK / "fz10c_m.inputs.json").read_text())
    print("inputs", [len(i) for x in c for i in x["inputs"]], c[0]["item"])


if __name__ == "__main__":
    main()
