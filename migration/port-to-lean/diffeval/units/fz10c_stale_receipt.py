"""Fidelity pass 2026-11-20, third attempt (label stale-compositions): receipt rows for def:run and def:run_py_py.

  cd migration/port-to-lean && python3 diffeval/units/fz10c_stale_receipt.py
      -> diffeval/receipts/fuzz_2026-11-20c-stale-compositions.tsv (columns of fuzz_2026-11-19.tsv)

Counts are read from work/<suite>.json (cases, "fz") and work/<suite>.result.json (statuses written by compare.py
from work/<suite>.out.txt, which fz10c_stale_collect.py took by script from this agent's eval_decl results).
Evaluation: eval_decl on def:zz_carrier_fid_2 (decl zz_carrier_fid_2), blueprint 5365851c, Lean as accepted at the
time of the pass (def:run, def:run_py_py, def:fe_run_06_split, def:zz_carrier_fid_2 DefinitionFormalized before
and after the runs; nothing written to the blueprint).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parent / "work"
TSV = HERE.parent / "receipts" / "fuzz_2026-11-20c-stale-compositions.tsv"
HEAD = ("unit\tfuzzer\tseeds\tgenerated\tkept\tshare_kept\tcompared_kept\tdifferences\tnarrowings\t"
        "python_raises_inside_precondition\tstatus\tnote\tblueprint\tgenerator")
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
FZ = "port-translator (stale-compositions, fidelity pass 2026-11-20 third attempt)"


def res(suite: str) -> tuple[list, Counter]:
    r = json.loads((W / f"{suite}.result.json").read_text())
    return r, Counter(x["status"] for x in r)


def cases(suite: str) -> list:
    return json.loads((W / f"{suite}.json").read_text())["cases"]


def main() -> None:
    rows = []
    # ---- def:run, generated suite
    fz = json.loads((W / "fz10_run.fuzz.json").read_text())["units"]["run"]
    r, c = res("fz10_run")
    cs = cases("fz10_run")
    kept_cases = [x for x in cs if x.get("fz") == "kept"]
    rej_pass = sum(1 for x, y in zip(cs, r) if x.get("fz") == "rejected" and y["status"] == "PASS")
    rl, cl = res("fz10c_run_logbits")
    assert c == Counter({"PASS": len(cs)}) and cl == Counter({"PASS": len(rl)}), (c, cl)
    rows.append(("run", FZ, fz["seeds"], fz["generated"], fz["kept"], f"{fz['kept'] / fz['generated']:.3f}",
                 len(kept_cases), 0, rej_pass, 0, "PASS",
                 f"suite fz10_run (generated earlier today, REGENERATED in this pass from port/ at HEAD 4a757fb: "
                 f"fz10_run.json/.inputs.json/.fuzz.json byte-identical, so the expected values are the current Python's), "
                 f"{len(cs)} cases in 7 eval_decl inputs on def:zz_carrier_fid_2, out.txt by script (fz10c_stale_collect.py), "
                 f"compare.py: {dict(c)}; kept cases compared {len(kept_cases)} (2,301 seeds + 6 log-fold cases); the 15 "
                 f"precondition-rejected seeds were sent too and equal Python ({rej_pass} narrowings: 12 non-ASCII text in "
                 f"MonthlyIncome / NumberOfDependents (the stricter-than-needed clause recorded in RULEBOOK 6), 3 no split id). "
                 f"The low-20-bit coarsening of the four log columns in fz10_run is REMOVED by suite fz10c_run_logbits "
                 f"(fz10c_run_logbits_gen.py): same 2,314 seeds, one full-bit fold of the four log columns per seed "
                 f"(29,888 log values): {dict(cl)}; so every column of every file is compared bit for bit, no KNOWN-LIMIT used. "
                 f"SPLIT draw branch reached (fz10c_stale_drawcount.py, current Python): of the kept seeds whose run completes, "
                 f"647 take _split_draw (555 with a draw that is not the first n_train sorted ids; pools of 1-12 ids), 707 use the "
                 f"file as given; 957 stop. {fz['note']}",
                 BP, "diffeval/units/fz10_run_gen.py + diffeval/units/fz10c_run_logbits_gen.py"))
    # ---- def:run_py_py, generated suite
    fz = json.loads((W / "fz10_run_py_py.fuzz.json").read_text())["units"]["run_py_py"]
    r, c = res("fz10_run_py_py")
    fails = [x["id"] for x in r if x["status"] != "PASS"]
    rn, cn = res("fz10c_stale_narrow")
    nf = [x["id"] for x in rn if x["status"] != "PASS"]
    assert fails == ["fz10_run_py_py/kept seeds of 2002100..2002124"], fails
    assert nf == ["fz10c_stale_narrow/seed 2002107: E (files)", "fz10c_stale_narrow/seed 2002107: exp at argument bits 4633626959958896978"], nf
    rows.append(("run_py_py", FZ, fz["seeds"], fz["generated"], fz["kept"], f"{fz['kept'] / fz['generated']:.3f}",
                 fz["kept"], 1, 0, len(fz["python_raises_inside_precondition"]), "KNOWN-LIMIT",
                 f"suite fz10_run_py_py (regenerated in this pass from port/ at HEAD 4a757fb: byte-identical), 104 cases = "
                 f"104 blocks of 25 seeds (every kept seed digested), 4 eval_decl inputs on def:zz_carrier_fid_2; compare.py: "
                 f"{dict(c)}. The one differing block, kept seeds 2002100..2002124, was narrowed (suite fz10c_stale_narrow, "
                 f"fz10c_stale_narrow_gen.py: per-seed E for the 24 kept seeds + Lean Float.exp at each of the 19 exp arguments "
                 f"the block's runs reach): {dict(cn)}; the only differing seed is 2002107 and the only differing exp is at "
                 f"argument 59.8997662095086 (bits 4633626959958896978, = -predicted_logit, predict.py:393 sas_exp): polars "
                 f"4996001759243522978, Lean Float.exp 4996001759243522979, ONE ulp. fz10c_stale_explain.py recomputes the port's "
                 f"two output frames of seed 2002107 with the Lean's exp value on the 2 rows (one per file) of that argument: "
                 f"the digest is the Lean's 5069487142773800831, EQUAL; so the one ulp of exp accounts for the whole difference. "
                 f"Rule: RULEBOOK section 6, 'Outside the model altogether: the last bit of exp and log ... (RealLike.exp / "
                 f"RealLike.log are abstract in the statements)', recorded for def:run_py_py with seeds 30930, 31316, 31393 "
                 f"(2026-11-16). Smallest case: seed 2002107, 3 test rows, intercept -1.0642047184159598, coefficients "
                 f"credit_utilization -1.0, credit_util_category -13.851954381310906, flag_high_debt_ratio -1.1316527284708249, "
                 f"full false; the row with credit_utilization 30.0, credit_util_category 2, flag_high_debt_ratio 1 has "
                 f"predicted_logit -59.8997662095086. 103 of 104 blocks equal; 2,299 of 2,300 kept seeds equal. {fz['note']}",
                 BP, "diffeval/units/fz10_run_py_py_gen.py + diffeval/units/fz10c_stale_narrow_gen.py + diffeval/units/fz10c_stale_explain.py"))
    # ---- real data
    for suite, unit, what in (("fz10c_stale_real_run", "run (real data)", "legacy/data/cs-training.csv slices + inputs/split_ids.csv"),
                              ("fz10c_stale_real_pp", "run_py_py (real data)", "legacy/data/cs-test.csv slices + the real model and medians")):
        r, c = res(suite)
        ran = [x for x in r if x["status"] != "ERROR"]
        notrun = [x["id"] for x in r if x["status"] == "ERROR"]
        st = "PASS" if all(x["status"] == "PASS" for x in ran) else "FAIL"
        rows.append((unit, FZ, what, len(r), len(r), "1.000", len(ran), sum(1 for x in ran if x["status"] != "PASS"), 0, 0,
                     st + (" (partial)" if notrun else ""),
                     f"suite {suite} (fz10c_stale_real_gen.py, current Python at HEAD 4a757fb): data lines of the real file copied "
                     f"byte for byte under the real header, the REAL run on them; all columns at full bits. Compared: "
                     f"{[x['id'].split('/', 1)[1] for x in ran]}: {dict(Counter(x['status'] for x in ran))}. Generated but NOT "
                     f"evaluated (the larger slice of each kind, left out to keep the transcribed eval inputs within this agent's "
                     f"budget; the inputs are in work/{suite}.inputs.json): {[x.split('/', 1)[1] for x in notrun]}. The whole files "
                     f"(150,000 / 101,503 rows) are beyond one eval_decl input; their Python digests at HEAD are in "
                     f"work/fz10_real.expected.json (the real split file fits: the whole-file run does not draw).",
                     BP, "diffeval/units/fz10c_stale_real_gen.py"))
    TSV.write_text(HEAD + "\n" + "\n".join("\t".join(str(v) for v in row) for row in rows) + "\n")
    print(TSV.read_text()[:3000])


if __name__ == "__main__":
    main()
