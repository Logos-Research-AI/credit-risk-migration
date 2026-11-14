"""Receipts from the suite results (work/<suite>.result.json, written by compare.py).

  uv run python migration/diffeval/receipts.py
      -> receipts/prelude.tsv   (primitive, cases, differences, status, note); statuses PASS / KNOWN-LIMIT
         (a limit recorded in RULEBOOK section 6) / DIFF (any other difference) / ERROR
  uv run python migration/diffeval/receipts.py units <bundle> [<bundle> ...]
      -> receipts/units.tsv     (unit, cases, differences, status, note, generator): one row per
         unit of the bundle, from every work/<bundle>_*.result.json. Rows are appended; a row of
         the same unit and generator is replaced, so a re-run does not duplicate.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
SUITES = ["ff", "int", "boolstr", "horiz", "aggsel", "agggrp", "frames", "ranknp", "logexp"]
DIAG = ["diag", "diag2", "diag3"]  # minimal reproductions (not counted in the receipt)
# Notes of the rows. A KNOWN-LIMIT row takes its note from its cases (`lim(...)` in prelude_suites.py:
# the limit as recorded in RULEBOOK section 6); a DIFF row MUST have a note here or is flagged UNEXPLAINED.
NOTES = {
    # ---- differences that are NOT recorded limits (reported; the preludes are frozen)
    "fillNull(Col.null, non-Float64)": "DIFF, not a recorded limit: Col.fillNull has no arm for a Null-dtype operand. pl.lit(None).fill_null(1 | True), "
        "a Null column filled with an Int64 column, and an Int64 / Boolean column filled with pl.lit(None) come back Float64 (same values; polars keeps "
        "Int / Boolean); with a String operand (lit(None).fill_null('x'), s.fill_null(lit(None))) the prelude returns an EMPTY Float64 column "
        "(polars: the String column)",
    "add(Col.null operand, Int64 / Null other operand)": "DIFF, not a recorded limit (dtype only): Int64 + Null is an Int64 column of nulls in polars and "
        "Null + Null is Null; the prelude returns Float64 nulls of the same length",
    "mul(Col.null operand, Int64 / Null other operand)": "DIFF, not a recorded limit (dtype only): Int64 * Null is an Int64 column of nulls in polars; "
        "the prelude returns Float64 nulls of the same length",
    "comparison(Col.null operand, String)": "DIFF, not a recorded limit: String column == pl.lit(None) is 5 Boolean nulls in polars; the prelude returns an "
        "EMPTY Boolean column (cmpBin falls through to asF64, which is [] for a String column)",
    "and/or(Col.null operand)": "DIFF, not a recorded limit: Boolean & / | pl.lit(None) follows Kleene logic in polars (false & null = false, true | null = "
        "true, else null); the prelude returns an EMPTY Boolean column (boolsOf of a Null column is [])",
    "castI64(Col.null)": "DIFF, not a recorded limit (dtype only): pl.lit(None).cast(pl.Int64) is an Int64 null; Expr.castI64 leaves the Null column",
    "sum(Col.null)": "DIFF, not a recorded limit: sum of a Null-dtype column is a Null-dtype null in polars; the prelude returns Float64 0.0",
    "mean(Col.null)": "DIFF, not a recorded limit (dtype only): mean of a Null-dtype column is a Null-dtype null in polars; the prelude returns a Float64 null",
    # ---- what the PASS rows cover
    "add(scalar zero)": "former D2: `col + 0.0`, `0.0 + col`, `col + 0`, `expr + 0.0`, `col + (-0.0)`, `col + aggregate(= 0.0)` keep the column (-0.0 stays); "
                        "209 rows with every pair of edge values, and 5 rows in dump mode",
    "sub(scalar zero)": "former D2: `col - 0.0`, `col - (-0.0)`, `col - aggregate(= 0.0)` keep the column; `0.0 - col`, `0 - col`, `aggregate - col` negate it",
    "add(scalar zero, Int64 operand)": "Int64 column + 0 / 0 + column stay Int64; + 0.0 / 0.0 + is the Float64 cast",
    "sub(scalar zero, Int64 operand)": "Int64 column - 0 stays Int64, 0 - column is the Int64 negation; `0.0 - column` is the negated Float64 cast (0 gives -0.0)",
    "add(scalar zero, Boolean operand)": "Boolean column + 0.0 is the Float64 cast",
    "add(scalar zero, 1-row frame)": "on a 1-row frame the operands are added by IEEE: -0.0 + 0.0 = +0.0 (float and int zero literal, aggregate, Int64 column)",
    "sub(scalar zero, 1-row frame)": "on a 1-row frame IEEE subtraction: -0.0 - 0.0 = -0.0, 0.0 - (-0.0) = +0.0, -0.0 - (-0.0) = +0.0",
    "add(scalar zero, 0-row frame)": "0-row frame: empty column of the same dtype", "sub(scalar zero, 0-row frame)": "0-row frame: empty Float64 column",
    "add(two length-1 operands)": "two literals / aggregates are added by IEEE (-0.0 + 0.0 = +0.0, -0.0 + -0.0 = -0.0)",
    "sub(two length-1 operands)": "two literals / aggregates are subtracted by IEEE (-0.0 - 0.0 = -0.0, 0.0 - 0.0 = +0.0)",
    "wto(litNull branch)": "former D3: then / otherwise None (Pl.litNull) and a missing otherwise with Int, String, Boolean and Float64 literal and column "
                           "branches keep the dtype of the other branch; both branches None give a Null-dtype column; chains; 1-row and 0-row frames",
    "litNull": "pl.lit(None) in select: one Null-dtype null",
    "isNull(Col.null)": "is_null of pl.lit(None) and of a Null-dtype column", "isNotNull(Col.null)": "is_not_null of pl.lit(None) and of a Null-dtype column",
    "fillNull(Col.null)": "Null literal / Null column filled with a Float64 literal or column, and a Float64 column filled with pl.lit(None)",
    "add(Col.null operand)": "Float64 column +/- pl.lit(None) / a Null column: Float64 nulls", "sub(Col.null operand)": "Float64 column - Null and Null - column: Float64 nulls",
    "mul(Col.null operand)": "Float64 column * Null: Float64 nulls", "div(Col.null operand)": "Float64 and Int64 column / Null: Float64 nulls",
    "comparison(Col.null operand)": "Float64 / Int64 column compared with pl.lit(None): Boolean nulls",
    "castF64(Col.null)": "cast(pl.Float64) of pl.lit(None) and of a Null column: Float64 nulls", "count(Col.null)": "count of a Null column is 0",
    "withColumns(Col.null)": "with_columns(n=pl.lit(None)) appends / replaces by a Null-dtype column of the frame's height",
    "select(Col.null)": "select with pl.lit(None): broadcast beside a column, one row alone",
    "toTable(Col.null)": "a Null-dtype column crosses the stage boundary as numeric missing cells",
    "filter(frame, Col.null column)": "frame filter keeps a Null-dtype column", "sort(Col.null column)": "frame sort keeps a Null-dtype column",
    "castF64(frame, Col.null column)": "frame cast(pl.Float64) turns a Null-dtype column into Float64 nulls",
    "litCell": "pl.lit(<date>) = Pl.litCell: with_columns (append, replace), select (broadcast, scalar, positional name `literal`), toTable (the cell itself)",
    "Expr.pos": "output names of 44 expression shapes (column, alias, binary = left operand, literal, len, aggregates, when/then = then branch, horizontal = "
                "first operand, map_batches = `a`, litCell) and positional select",
    "setCol": "with_columns(series.alias(n)): replace in place (same and other dtype, last column), append (Int64, Boolean)",
    "itemF": "frame.item(row, name), item(row, 0) via firstName, item() of a 1x1 frame; null gives none", "itemI": "Int64 column, with a null",
    "itemS": "String column, with a null", "firstName": "3 frames", "getF": "Float64 column with null and -0.0", "getI": "", "getS": "",
    "height": "3-row, 1-row and filtered-to-empty frame",
    "abs": "column without -0.0 (209 rows: null, 0.0, NaN, inf, subnormal, random)",
    "Np.rint": "40 values: negative and positive exact halves (ties to even), -0.0, tiny negatives, values around 2^52 / 2^53, inf, NaN",
    "Np.round3": "former D10: negative values rounding to zero give -0.0; 2,368 grid / random / edge values and 46 negative values and exact halves "
                 "(x * 1000 exactly half for x = k / 16)",
    "Np.sort": "arrays without zeros of both signs; empty array",
    "Np.sum": "lengths 0..300 (4 arrays), 1000, 2048, 3000, 5000; arrays of zeros of both signs and of -0.0 only",
    "median": "25 lengths 0..1300 on 5 columns without zeros of both signs", "group:median": "5 groupings, columns without zeros of both signs",
    "sumHorizontal(full=true)": "matches polars with 2, 3, 4 and 12 threads, N = 2..6, nulls, NaN, inf, -0.0 + null",
    "sumHorizontal(full=false)": "matches POLARS_MAX_THREADS=1, N = 2..6",
    "minHorizontal(full=true)": "N = 2..6", "maxHorizontal(full=true)": "N = 2..6",
    "log,exp": "33 values (edges + random): bit-identical, no 1-ulp case observed",
    "sum": "select context: 25 lengths 0..1300, nulls, all-null, NaN/inf, Int64",
    "group:sum": "4 key shapes (int, string, float with NaN/zeros/null, two keys) + 120 small groups; groups > 128, 1-row, all-null",
    "join(Float64 key)": "float key with NaN, -0.0/0.0 and nulls: equal",
}
NOTES["log"] = NOTES["exp"] = NOTES["log,exp"]
HEADER = "primitive\tcases\tdifferences\tstatus\tnote"


def _load(s: str):
    suite = json.loads((HERE / "work" / f"{s}.json").read_text())
    results = json.loads((HERE / "work" / f"{s}.result.json").read_text())
    if len(results) != len(suite["cases"]) or [r["id"] for r in results] != [c["id"] for c in suite["cases"]]:
        raise SystemExit(f"work/{s}.result.json does not match work/{s}.json (stale: rerun eval_decl and compare.py)")
    return suite, results


def main():
    """receipts/prelude.tsv: one row per primitive over the nine suites.
    status: ERROR (an input did not run) > DIFF (a difference that is not a recorded limit) >
    KNOWN-LIMIT (only differences recorded in RULEBOOK section 6: cases marked `lim`) > PASS(1ulp) > PASS.
    differences = cases that differ (FAIL + XFAIL + ERROR)."""
    agg: dict[str, dict] = {}
    for s in SUITES:
        suite, results = _load(s)
        for r in results:
            prims = [r["primitive"]] if "(" in r["primitive"] else r["primitive"].split(",")
            if r["primitive"].startswith("group:") and len(prims) > 1:
                prims = [prims[0]] + ["group:" + q for q in prims[1:]]
            for prim in prims:
                a = agg.setdefault(prim, {"cases": 0, "PASS": 0, "FAIL": 0, "ULP": 0, "XFAIL": 0, "XPASS": 0, "ERROR": 0, "lim": [], "ids": []})
                a["cases"] += 1
                a[r["status"]] += 1
                if r["status"] in ("XFAIL", "XPASS") and r["note"] and r["note"] not in a["lim"]:
                    a["lim"].append(r["note"])
                if r["status"] in ("FAIL", "ERROR"):
                    a["ids"].append(r["id"])
    rows, tot = [HEADER], {}
    for prim in sorted(agg):
        a = agg[prim]
        if a["ERROR"]:
            st, note = "ERROR", "inputs did not run: " + ", ".join(a["ids"])
        elif a["FAIL"]:
            st = "DIFF"
            note = NOTES.get(prim, "UNEXPLAINED") + " [" + ", ".join(a["ids"]) + "]"
        elif a["XFAIL"] or a["XPASS"]:
            st = "KNOWN-LIMIT"
            note = " | ".join(a["lim"]) + f" [differs in {a['XFAIL']} of {a['cases']} cases" + (
                "; the others agree on their input]" if a["XPASS"] or a["PASS"] else "]")
        else:
            st, note = ("PASS(1ulp)" if a["ULP"] else "PASS"), NOTES.get(prim, "")
        tot[st] = tot.get(st, 0) + 1
        rows.append(f"{prim}\t{a['cases']}\t{a['FAIL'] + a['XFAIL'] + a['ERROR']}\t{st}\t{note}")
    extra = json.loads((HERE / "work" / "multichunk.json").read_text())
    cuts = next(iter(extra.values()))
    rows.append(f"sum(multi-chunk column)\t6\t{len(cuts)}\tKNOWN-LIMIT\tRULEBOOK §6 recorded limit: multi-chunk columns. Python only: the sum of the same "
                f"1000 values differs from the one-chunk sum when the column has 2 chunks (split at {cuts}; 4 other splits agree); "
                "the prelude models one chunk and equals the one-chunk sum")
    tot["KNOWN-LIMIT"] = tot.get("KNOWN-LIMIT", 0) + 1
    (HERE / "receipts" / "prelude.tsv").write_text("\n".join(rows) + "\n")
    print("\n".join(r[:170] for r in rows))
    print(sum(a["cases"] for a in agg.values()), "case-primitive pairs;", len(rows) - 1, "rows;", "  ".join(f"{k}={v}" for k, v in sorted(tot.items())))


UNITS_TSV = HERE / "receipts" / "units.tsv"
UNITS_HEADER = "unit\tcases\tdifferences\tstatus\tnote\tgenerator"


def append_unit(unit: str, cases: int, differences: int, status: str, note: str, generator: str) -> str:
    """Append one row to receipts/units.tsv (replacing the row of the same unit and generator)."""
    clean = lambda x: str(x).replace("\t", " ").replace("\n", " ")  # noqa: E731
    row = "\t".join(clean(x) for x in (unit, cases, differences, status, note, generator))
    UNITS_TSV.parent.mkdir(exist_ok=True)
    lines = UNITS_TSV.read_text().splitlines() if UNITS_TSV.exists() else []
    if not lines or lines[0] != UNITS_HEADER:
        lines = [UNITS_HEADER] + [ln for ln in lines if ln.strip()]
    keep = [ln for ln in lines[1:] if not (ln.split("\t")[0] == unit and ln.split("\t")[-1] == generator)]
    UNITS_TSV.write_text("\n".join([UNITS_HEADER, *keep, row]) + "\n")
    return row


def units(bundle: str) -> list[str]:
    """One row per unit (= the `primitive` of the cases) over the suites work/<bundle>_*.json.
    cases = sum of the cases' `covers` (a case that digests k results covers k; default 1);
    differences = compared values that differ (FAIL + XFAIL + ERROR).
    status: ERROR (an input did not run / malformed) > DIFF (a difference not marked expected) >
    XPASS (a case marked expect_diff no longer differs) > KNOWN-DIFF (only expected differences) > PASS."""
    agg: dict[str, dict] = {}
    notes: dict[str, list[str]] = {}
    generator = ""
    files = sorted((HERE / "work").glob(f"{bundle}_*.result.json"))
    if not files:
        raise SystemExit(f"no work/{bundle}_*.result.json: run the generator, eval_decl and compare.py first")
    for rf in files:
        suite = json.loads(rf.with_name(rf.name.replace(".result.json", ".json")).read_text())
        results = json.loads(rf.read_text())
        if len(results) != len(suite["cases"]):
            raise SystemExit(f"{rf.name}: {len(results)} results for {len(suite['cases'])} cases (stale result: rerun compare.py)")
        generator = suite.get("generator", generator)
        for u, n in suite.get("notes", {}).items():
            if n not in notes.setdefault(u, []):
                notes[u].append(n)
        for case, r in zip(suite["cases"], results, strict=True):
            a = agg.setdefault(r["primitive"], {"cases": 0, "PASS": 0, "FAIL": 0, "ULP": 0, "XFAIL": 0, "XPASS": 0, "ERROR": 0, "known": []})
            a["cases"] += case.get("covers", 1)
            a[r["status"]] += 1
            if r["status"] == "XFAIL" and r["note"] and r["note"] not in a["known"]:
                a["known"].append(r["note"])
    rows = []
    for unit, a in agg.items():
        if a["ERROR"]:
            st = "ERROR"
        elif a["FAIL"]:
            st = "DIFF"
        elif a["XPASS"]:
            st = "XPASS"
        elif a["XFAIL"]:
            st = "KNOWN-DIFF"
        else:
            st = "PASS(1ulp)" if a["ULP"] else "PASS"
        note = "; ".join(notes.get(unit, []) + ([f"{a['XFAIL']} expected: " + " | ".join(a["known"])] if a["XFAIL"] else []))
        rows.append(append_unit(unit, a["cases"], a["FAIL"] + a["XFAIL"] + a["ERROR"], st, note, generator))
    return rows


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2 and sys.argv[1] == "units":
        for b in sys.argv[2:]:
            print("\n".join(units(b)))
    else:
        main()
