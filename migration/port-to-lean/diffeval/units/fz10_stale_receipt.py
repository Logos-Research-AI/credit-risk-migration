"""Fidelity pass 2026-11-20 (label stale-compositions): receipt rows for def:run and def:run_py_py.

  cd migration/port-to-lean && python3 diffeval/units/fz10_stale_receipt.py
      -> diffeval/receipts/fuzz_2026-11-20-stale-compositions.tsv (columns of fuzz_2026-11-19.tsv)

Reads work/fz10_run.{json,fuzz.json}, work/fz10_run_py_py.{json,fuzz.json}, work/fz10_real.expected.json.
No work/<suite>.out.txt exists: eval_decl refused every call (see NOTE_EVAL), so compared_kept = 0 and
the status is ERROR (the harness's status for inputs that did not run); `differences` is 0 because
nothing was compared, not because Lean was shown equal.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parent / "work"
TSV = HERE.parent / "receipts" / "fuzz_2026-11-20-stale-compositions.tsv"
HEAD = ("unit\tfuzzer\tseeds\tgenerated\tkept\tshare_kept\tcompared_kept\tdifferences\tnarrowings\t"
        "python_raises_inside_precondition\tstatus\tnote\tblueprint\tgenerator")
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
FUZZER = "port-translator (stale-compositions 2026-11-20)"
NOTE_EVAL = ("NOT EVALUATED IN LEAN: on 2026-11-20 the blueprint has no zz_carrier_* item, and eval_decl refuses "
             "def:run and def:run_py_py at call level (the schema-error refusal of eval_decl-errors-2026-11-18.md "
             "section 1, also with the input `1`, with decl omitted and with decl Pl.zipB; also on def:fe_run_06_split "
             "and def:predict_run_08_outputs), while def:_hl_groups answers [12, 6] in the same session; the brief forbids adding "
             "a carrier. Python side at port HEAD 4a757fb run in full; suites ready in work/ for a carrier")


def row(unit, seeds, gen, kept, raises, note, generator):
    share = f"{kept / gen:.3f}" if gen else "-"
    return "\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in
                     (unit, FUZZER, seeds, gen, kept, share, 0, 0, 0, len(raises), "ERROR", note, BP, generator))


def main() -> None:
    rows = []
    for suite in ("fz10_run", "fz10_run_py_py"):
        fz = json.loads((W / f"{suite}.fuzz.json").read_text())
        s = json.loads((W / f"{suite}.json").read_text())
        inputs = json.loads((W / f"{suite}.inputs.json").read_text())
        n_in = sum(len(g["inputs"]) for g in inputs)
        for unit, u in fz["units"].items():
            note = (f"{NOTE_EVAL}; suite {suite}: {len(s['cases'])} cases in {n_in} eval inputs, out.txt absent; "
                    + u["note"])
            rows.append(row(unit, u["seeds"], u["generated"], u["kept"], u["python_raises_inside_precondition"], note,
                            fz["generator"]))
    real = json.loads((W / "fz10_real.expected.json").read_text())
    sp = real["split"]
    rows.append(row("run (real data)", "legacy/data/cs-training.csv + inputs/split_ids.csv", 1, 1, [],
                    f"{NOTE_EVAL}; real feature_engineering.run at HEAD: files "
                    f"{[(f['file'], f['height']) for f in real['run']]}, split file fits ({sp['file_ids']} distinct ids = "
                    f"(7n+9)//10 for n = {sp['n']}: used as given, the draw is not reached on real data); digests in "
                    "work/fz10_real.expected.json; a whole-file Lean input is beyond an eval_decl input in any case",
                    "diffeval/units/fz10_real_gen.py"))
    rows.append(row("run_py_py (real data)", "legacy/data/cs-test.csv + model of the real train.run", 1, 1, [],
                    f"{NOTE_EVAL}; real predict.run at HEAD after the real feature_engineering.run and train.run: files "
                    f"{[(f['file'], f['height']) for f in real['run_py_py']]}, model.json intercept {real['model']['intercept']!r}, "
                    f"{real['model']['n_coefficients']} coefficients; digests in work/fz10_real.expected.json",
                    "diffeval/units/fz10_real_gen.py"))
    TSV.write_text("\n".join([HEAD, *rows]) + "\n")
    for r in rows:
        print(r[:160])


if __name__ == "__main__":
    main()
