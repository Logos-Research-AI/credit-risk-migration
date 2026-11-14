"""Build the inputs for the second-round evidence of the legacy corrections (Q27 branches,
Q14 negative income). Inputs only, never code changes. Each scenario is a folder under
scenarios/fix2/ with cs-training.csv and cs-test.csv (q25_tiny_psi: stage inputs for the metrics step). Base: the first 3000 rows of the real
training file and the first 200 rows of the real test file; one thing is changed per scenario.

    uv run python make_fix_scenarios.py
"""

from __future__ import annotations

import csv
from pathlib import Path

JUDGE = Path(__file__).resolve().parent
DATA = JUDGE.parent / "legacy" / "data"
OUT = JUDGE / "scenarios" / "fix2"


def read(name: str, n: int) -> tuple[list[str], list[list[str]]]:
    with open(DATA / name, newline="") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1 : n + 1]


def write(folder: str, train, test, note: str) -> None:
    d = OUT / folder
    d.mkdir(parents=True, exist_ok=True)
    for name, (header, rows) in (("cs-training.csv", train), ("cs-test.csv", test)):
        with open(d / name, "w", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(header)
            w.writerows(rows)
    (d / "README.txt").write_text(note + "\n")


def changed(table, row: int, column: str, value: str):
    """Copy of the table with one cell changed; row is the 1-based data row."""
    header, rows = table
    rows = [r[:] for r in rows]
    rows[row - 1][header.index(column)] = value
    return header, rows


def main() -> None:
    train = read("cs-training.csv", 3000)
    test = read("cs-test.csv", 200)
    h = train[0]
    inc, dep = h.index("MonthlyIncome"), h.index("NumberOfDependents")

    write("good", train, test, "Valid files: first 3000 training rows, first 200 test rows.")

    # --- faulty training files (the test file is valid) ---
    t = {
        "train_outcome_2": changed(train, 30, "SeriousDlqin2yrs", "2"),
        "train_age_missing": changed(train, 30, "age", ""),
        "train_count_fraction": changed(train, 30, "NumberOfTimes90DaysLate", "0.5"),
        "train_count_negative": changed(train, 30, "NumberOfOpenCreditLinesAndLoans", "-1"),
        "train_count_almost_whole": changed(train, 30, "NumberOfTimes90DaysLate", "0.99999999999999"),
        "train_dependents_fraction": changed(train, 30, "NumberOfDependents", "1.5"),
        "train_income_text_tail": changed(train, 30, "MonthlyIncome", "12345abc"),
        "train_income_long": changed(train, 30, "MonthlyIncome", "1234567890123456789012345678901234"),
    }
    notes = {
        "train_outcome_2": "Training row 30 has SeriousDlqin2yrs = 2.",
        "train_age_missing": "Training row 30 has no age.",
        "train_count_fraction": "Training row 30 has NumberOfTimes90DaysLate = 0.5.",
        "train_count_negative": "Training row 30 has NumberOfOpenCreditLinesAndLoans = -1.",
        "train_count_almost_whole": "Training row 30 has NumberOfTimes90DaysLate = 0.99999999999999 (prints as 1 in 12 characters).",
        "train_dependents_fraction": "Training row 30 has NumberOfDependents = 1.5.",
        "train_income_text_tail": "Training row 30 has MonthlyIncome = 12345abc; the first 20 incomes have at most 5 characters.",
        "train_income_long": "Training row 30 has a MonthlyIncome of 34 digits (more than 32 characters).",
    }
    header, rows = train
    dup = [r[:] for r in rows]
    dup[30][0] = dup[29][0]
    t["train_duplicate_id"] = (header, dup)
    notes["train_duplicate_id"] = "Training rows 30 and 31 have the same row id."
    t["train_no_known_income"] = (header, [r[:inc] + ["NA"] + r[inc + 1 :] for r in rows])
    notes["train_no_known_income"] = "Every training MonthlyIncome is NA."
    t["train_extra_column"] = (header + ["Extra"], [r + ["1"] for r in rows])
    notes["train_extra_column"] = "The training file has a thirteenth column."
    k = h.index("NumberRealEstateLoansOrLines")
    t["train_missing_column"] = (header[:k] + header[k + 1 :], [r[:k] + r[k + 1 :] for r in rows])
    notes["train_missing_column"] = "The training file has no NumberRealEstateLoansOrLines column."
    # every income and dependents value numeric, then one text: PROC IMPORT with the default
    # guessingrows made the column numeric and read the text as a missing value
    full = [r[:] for r in rows]
    for r in full:
        if r[inc] == "NA":
            r[inc] = "5000"
        if r[dep] == "NA":
            r[dep] = "0"
    full[29][inc] = "abc"
    t["train_income_text"] = (header, full)
    notes["train_income_text"] = "No NA anywhere in the training file; row 30 has MonthlyIncome = abc."
    for name, table in t.items():
        write(name, table, test, "Faulty training file. " + notes[name])

    # --- valid training file with the unusual but allowed values ---
    v = changed(train, 30, "MonthlyIncome", "")
    v = changed(v, 31, "MonthlyIncome", ".")
    v = changed(v, 32, "MonthlyIncome", "na")
    v = changed(v, 33, "NumberOfDependents", "")
    v = changed(v, 34, "MonthlyIncome", "-1")
    v = changed(v, 35, "MonthlyIncome", "-7.5")
    vt = changed(test, 30, "MonthlyIncome", "-1")
    vt = changed(vt, 31, "MonthlyIncome", "-7.5")
    vt = changed(vt, 32, "MonthlyIncome", "")
    write("valid_unusual", v, vt,
          "Valid files. Training rows 30-32 have MonthlyIncome blank, '.', 'na'; row 33 has blank "
          "NumberOfDependents; rows 34 and 35 have MonthlyIncome -1 and -7.5. Test rows 30 and 31 "
          "have MonthlyIncome -1 and -7.5, row 32 blank.")

    # --- Q14 on the real model: the whole training file, two incomes of -1 or less ---
    real = read("cs-training.csv", 10**9)
    real = changed(changed(real, 34, "MonthlyIncome", "-1"), 35, "MonthlyIncome", "-7.5")
    write("q14_negative_real", real, vt,
          "Valid files. The whole real training file with MonthlyIncome -1 and -7.5 in rows 34 and 35; "
          "the test file of valid_unusual (rows 30 and 31 have MonthlyIncome -1 and -7.5).")

    # --- Q13: medians of incomes longer than the first 20 rows suggest ---
    a = h.index("age")
    m = [r[:] for r in rows]
    for i, r in enumerate(m):
        if int(r[a]) < 30:
            r[inc] = "NA"
        elif i < 20 and len(r[inc]) > 4:
            r[inc] = "9999"
    young = [i for i, r in enumerate(m) if int(r[a]) < 30 and i >= 20][:3]
    for i, value in zip(young, ("10000", "20000", "30000")):
        m[i][inc] = value
    mt = changed(changed(changed(test, 1, "age", "25"), 1, "MonthlyIncome", "NA"), 2, "age", "25")
    write("q13_median_width", (header, m), mt,
          "Valid files. Training: the first 20 incomes have at most 4 characters; the known incomes "
          "of the under-30 group are 10000, 20000 and 30000. Test row 1 is under 30 with a missing "
          "income and must get 20000.")

    # --- faulty test files (the training file is valid) ---
    s = {
        "test_age_missing": (changed(test, 30, "age", ""), "Test row 30 has no age."),
        "test_outcome_2": (changed(test, 30, "SeriousDlqin2yrs", "2"), "Test row 30 has SeriousDlqin2yrs = 2."),
        "test_count_fraction": (changed(test, 30, "NumberOfTimes90DaysLate", "0.5"),
                                "Test row 30 has NumberOfTimes90DaysLate = 0.5."),
        "test_income_text": (changed(test, 30, "MonthlyIncome", "abc"), "Test row 30 has MonthlyIncome = abc."),
    }
    th, tr = test
    dup = [r[:] for r in tr]
    dup[30][0] = dup[29][0]
    s["test_duplicate_id"] = ((th, dup), "Test rows 30 and 31 have the same row id.")
    s["test_extra_column"] = ((th + ["Extra"], [r + ["1"] for r in tr]), "The test file has a thirteenth column.")
    for name, (table, note) in s.items():
        write(name, train, table, "Faulty test file. " + note)


def tiny_psi() -> None:
    """Stage inputs for metrics_calculation.sas: 100,000 training and 100,000 validation rows
    with the same scores, except one validation applicant moved from the lowest bin to the
    highest. The shares differ by one applicant in two bins: PSI is about 4e-9."""
    d = OUT / "q25_tiny_psi"
    d.mkdir(parents=True, exist_ok=True)
    n = 100_000
    for name, start in (("risk_scores_train.csv", 1), ("risk_scores_validation.csv", 200_001)):
        with open(d / name, "w", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["row_id", "default_flag", "pd_logistic", "credit_risk_score"])
            for i in range(n):
                k = i
                if name == "risk_scores_validation.csv" and i == 0:
                    k = n  # the lowest score becomes the highest
                pd_ = round(0.9 - 0.8 * k / n, 6)  # distinct, falling: the score rises with i
                w.writerow([start + i, int(i % 13 == 0 and pd_ > 0.3), pd_, round(600 + 250 * (1 - pd_), 6)])
    (d / "README.txt").write_text(
        "Stage inputs for metrics_calculation.sas (finding Q25, second round). Training and validation "
        "have the same 100,000 scores except one validation applicant, moved from the lowest bin to the "
        "highest: the bin shares differ by one applicant in two bins.\n")


if __name__ == "__main__":
    main()
    tiny_psi()
