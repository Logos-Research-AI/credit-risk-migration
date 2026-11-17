"""Fuzz pass 2026-11-16: one row per unit in receipts/fuzz_2026-11-16.tsv, from a compared suite.

  cd migration/port-to-lean && python3 diffeval/fuzz_receipt.py <suite> [<suite> ...]

Reads work/<suite>.json (cases), work/<suite>.result.json (compare.py) and work/<suite>.fuzz.json,
which the generator writes:
  {"fuzzer": "port-translator-7", "generator": "diffeval/units/fz_<...>_gen.py",
   "units": {"<unit>": {"seeds": "1000..3499", "generated": 2500, "kept": 2210,
                        "python_raises_inside_precondition": [<seed>, ...],   # defects, no Lean needed
                        "note": "pools: ...; what one case is",
                        "all_differences_are_recorded_limit": "<which limit, and how shown>"   # optional}}}
Every case of the suite carries the extra fields "fz": "kept" | "rejected" (the precondition,
evaluated in Python, admits the generated input or not) and "covers": how many generated inputs
the case digests (default 1). Generated inputs on which Python raises are not sent to Lean.
Row: unit, fuzzer, seeds, generated, kept, share kept, compared in Lean (kept), differences (kept),
rejected inputs where Python does not raise and Lean equals Python (narrowings), Python raises
inside the precondition (defects), status, note, blueprint id evaluated on, generator. A row of the same unit and generator
is replaced.
"""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# the receipts file: fuzz_2026-11-16.tsv unless FUZZ_RECEIPTS names another file of receipts/
# (update 2026-11-17: FUZZ_RECEIPTS=fuzz_2026-11-17.tsv)
TSV = HERE / "receipts" / os.environ.get("FUZZ_RECEIPTS", "fuzz_2026-11-16.tsv")
# the blueprint id the suite was evaluated on: key "blueprint" of work/<suite>.fuzz.json; rows without it ran
# on the id in use before the owner's re-base of 2026-11-16 (the new id is 5365851c-5549-44b7-9207-4bd4c422031d)
OLD = "b41b22d4-720d-4290-b593-39ceab961986"
HEAD = "unit\tfuzzer\tseeds\tgenerated\tkept\tshare_kept\tcompared_kept\tdifferences\tnarrowings\tpython_raises_inside_precondition\tstatus\tnote\tblueprint\tgenerator"


def main() -> int:
    rows = TSV.read_text().splitlines()[1:] if TSV.exists() else []
    for suite in sys.argv[1:]:
        s = json.loads((HERE / "work" / f"{suite}.json").read_text())
        res = json.loads((HERE / "work" / f"{suite}.result.json").read_text())
        fz = json.loads((HERE / "work" / f"{suite}.fuzz.json").read_text())
        if len(res) != len(s["cases"]):
            raise SystemExit(f"{suite}: stale result, rerun compare.py")
        agg: dict[str, dict] = {}
        for c, r in zip(s["cases"], res):
            a = agg.setdefault(r["primitive"], {"kept": 0, "diff": 0, "narrow": 0, "err": 0, "ids": []})
            n = c.get("covers", 1)
            if r["status"] == "ERROR":
                a["err"] += 1
            if c.get("fz", "kept") == "kept":
                a["kept"] += n
                if r["status"] not in ("PASS", "ULP"):
                    a["diff"] += 1
                    a["ids"].append(c["id"])
            elif r["status"] in ("PASS", "ULP"):
                a["narrow"] += n
        for unit, u in fz["units"].items():
            a = agg.get(unit, {"kept": 0, "diff": 0, "narrow": 0, "err": 0, "ids": []})
            raises = u.get("python_raises_inside_precondition", [])
            status = "ERROR" if a["err"] else "DIFF" if a["diff"] or raises else "PASS"
            # every difference traced to a limit recorded in RULEBOOK section 6: say which, and how it was shown
            if status == "DIFF" and not raises and u.get("all_differences_are_recorded_limit"):
                status = "KNOWN-LIMIT"
                u = {**u, "note": u.get("note", "") + "; ALL differences: " + u["all_differences_are_recorded_limit"]}
            note = u.get("note", "") + (f"; differing cases: {a['ids'][:5]}" if a["ids"] else "")
            share = f"{u['kept'] / u['generated']:.3f}" if u["generated"] else "-"
            row = "\t".join(
                str(x).replace("\t", " ").replace("\n", " ")
                for x in (unit, fz["fuzzer"], u["seeds"], u["generated"], u["kept"], share, a["kept"], a["diff"],
                          a["narrow"], len(raises), status, note, fz.get("blueprint", OLD), fz["generator"])
            )
            rows = [x for x in rows if not (x.split("\t")[0] == unit and x.split("\t")[-1] == fz["generator"])] + [row]
            print(row[:200])
    TSV.write_text("\n".join([HEAD, *rows]) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
