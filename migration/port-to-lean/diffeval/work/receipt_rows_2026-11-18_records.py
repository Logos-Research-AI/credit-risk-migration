"""Records step 2026-11-18: appends the fifth-diff fuzz receipts that were not yet in receipts/fuzz_2026-11-18.tsv
(train_run_10_score_valid two sweeps; _hl_groups before the n / g fix).  Run: cd migration/port-to-lean && python3 diffeval/work/receipt_rows_2026-11-18_records.py
"""
from pathlib import Path

BP = "5365851c-5549-44b7-9207-4bd4c422031d"
TSV = Path(__file__).resolve().parent.parent / "receipts" / "fuzz_2026-11-18.tsv"
rows = [
    ["train_run_10_score_valid", "port-translator (fz5_s10, non-author fuzz)", "0..2099 (21 chunks of 100)", "2100", "2049", "0.976", "2049", "6", "0", "0", "KNOWN-LIMIT",
     "fifth diff, through def:zz_carrier_e; 51 Python raises (intercept None, final some, no coefficient) not sent; 6 chunk digests differ, one seed each (320, 484, 1197, 1313, 1997, 2018): last bit of exp (pd_logistic = 1 / (1 + exp(-eta)), train.py:629), Lean Float.exp against CPython math.exp, RULEBOOK section 6; Python with a correctly rounded exp (Decimal, 60 digits; work/fz5_s10_crchunk.py s1) equals Lean on all 21 chunks (re-run 2026-11-18); seeds 1997, 2018, 1313 compared row by row (fz5_s10_pcmp.py)",
     BP, "diffeval/units/fz5_s10_gen.py"],
    ["train_run_10_score_valid", "port-translator (fz5_s10 hp2 sweep)", "50000..50899 (9 chunks of 100)", "900", "886", "0.984", "886", "1", "0", "0", "KNOWN-LIMIT",
     "second sweep (eta near -2^-51 .. -2^-49 where pd first falls below 0.5, and exp-compare mode); one chunk differs, seed 50221: last bit of exp, same recorded limit; Python with a correctly rounded exp equals Lean on all 9 chunks (crchunk.py s2 hp2, re-run 2026-11-18); plain Python differs in chunk 2 only",
     BP, "diffeval/units/fz5_s10_gen.py (argument hp2)"],
    ["_hl_groups", "port-translator (fz5 generator, before the n / g fix)", "700000..702054 (kind 0; chunks 0..2, 600 cases compared)", "2055", "600", "n/a", "600", "1", "0", "0", "DIFF-FIXED",
     "run before the lead's decision on n / g (see the rows of the same unit after the fix): seed 700248, n = 100000000000000000019, g = 5: Python q is the correctly rounded int true division, the Lean divided two floats; fixed by def:_hl_groups revision 2864ca0a (update-2026-11-17.md section 5); diffeval/units/fz5_compare.py 0 1 2 reports 1 difference in 600",
     BP, "diffeval/units/fz5_hl_groups_gen.py"],
]
with TSV.open("a") as f:
    for r in rows:
        assert len(r) == 14
        f.write("\t".join(r) + "\n")
print("appended", len(rows))
