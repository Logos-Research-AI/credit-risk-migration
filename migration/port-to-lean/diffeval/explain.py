"""Check that each diagnosis accounts for the WHOLE difference (nothing else hides behind it).

A case that is a recorded limit (`lim(...)` in prelude_suites.py / diag_suite.py) carries
`under_diagnosis`: the value the prelude must return if the limit is the only difference. Here the
Lean output is compared again, this time with that value: equal = the diagnosis is complete.
(For an XPASS case the value under the diagnosis is also the Python value.) A difference that has
no recorded diagnosis is listed with its full comparison, so that it cannot hide in a table.

  uv run python migration/diffeval/explain.py      -> receipts/explained.tsv
     (case, primitive, status, diagnosis, lean_equals_value_under_diagnosis, paths that differ from Python)
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import compare as cmp
from receipts import DIAG, NOTES, SUITES

HERE = Path(__file__).parent


def main():
    rows = ["case\tprimitive\tstatus\tdiagnosis\tlean_equals_value_under_diagnosis\tdiffers_from_python_at"]
    bad = 0
    for name in SUITES + DIAG:
        suite = json.loads((HERE / "work" / f"{name}.json").read_text())
        outputs = [ln.strip() for ln in (HERE / "work" / f"{name}.out.txt").read_text().splitlines() if ln.strip()]
        results = cmp.compare_suite(suite, outputs)
        under = copy.deepcopy(suite)
        for c in under["cases"]:
            if "under_diagnosis" in c:
                c["expected"] = c["under_diagnosis"]
            c.pop("expect_diff", None)
        again = cmp.compare_suite(under, outputs)
        for case, r, r2 in zip(suite["cases"], results, again, strict=True):
            if r["status"] == "PASS":
                continue
            where = "; ".join(f"{p}: python {e} lean {g}" for p, e, g in r["diffs"][:4]) + (f"; ... {len(r['diffs']) - 4} more" if len(r["diffs"]) > 4 else "")
            if "under_diagnosis" in case:
                ok = "yes" if r2["status"] == "PASS" else "NO"
                diag = r["note"]
            else:
                ok = "no diagnosis recorded"
                diag = NOTES.get(r["primitive"], "UNEXPLAINED") if r["status"] in ("FAIL", "ERROR") else r["note"]
            bad += ok == "NO"
            rows.append("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in (r["id"], r["primitive"], r["status"], diag, ok, where)))
    (HERE / "receipts" / "explained.tsv").write_text("\n".join(rows) + "\n")
    print("\n".join(r[:230] for r in rows))
    print(len(rows) - 1, "cases that are not PASS;", bad, "diagnoses that do NOT account for the whole difference")


if __name__ == "__main__":
    main()
