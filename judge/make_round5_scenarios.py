"""Build the round 5 evidence inputs: files on which rulings G46, G48 and G49 would have had the
SAS program corrected. Ruling G53 set those rulings aside, so no correction was applied; the
files stay as a record of what SAS does on them, and "valid" and "faulty" below and in the
README.txt files are meant in the sense of G46 to G49. Inputs only, never code changes. Each scenario is a folder under scenarios/fix_round5/ with
cs-training.csv and cs-test.csv. Base, as in make_fix_scenarios.py: the first 3000 rows of the
real training file and the first 200 rows of the real test file; one thing is changed per
scenario. The lines are written as text, not through a CSV writer, so that quotes and short
rows are exactly as stated.

    uv run python make_round5_scenarios.py
"""

from __future__ import annotations

import json
from pathlib import Path

JUDGE = Path(__file__).resolve().parent
DATA = JUDGE.parent / "legacy" / "data"
OUT = JUDGE / "scenarios" / "fix_round5"
FOUR = "feature_engineering.sas,train.sas,metrics_calculation.sas,predict.sas"


def read(name: str, n: int) -> list[str]:
    """The header line and the first n data lines."""
    with open(DATA / name) as fh:
        return [next(fh).rstrip("\n") for _ in range(n + 1)]


def write(folder: str, train: list[str], test: list[str], note: str) -> None:
    d = OUT / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / "cs-training.csv").write_text("\n".join(train) + "\n")
    (d / "cs-test.csv").write_text("\n".join(test) + "\n")
    (d / "README.txt").write_text(note + "\n")


def cell(lines: list[str], row: int, column: str, value: str) -> list[str]:
    """Copy with one field changed; row is the 1-based data row."""
    k = lines[0].split(",").index(column)
    fields = lines[row].split(",")
    fields[k] = value
    return lines[:row] + [",".join(fields)] + lines[row + 1 :]


def header(lines: list[str], old: str, new: str) -> list[str]:
    names = lines[0].split(",")
    names[names.index(old)] = new
    return [",".join(names)] + lines[1:]


def shorter(lines: list[str], row: int, fields: int) -> list[str]:
    """Copy with the last `fields` fields of one data row removed (separators included)."""
    return lines[:row] + [",".join(lines[row].split(",")[:-fields])] + lines[row + 1 :]


def last(lines: list[str], column: str) -> list[str]:
    """Copy with one column moved to the end of every line."""
    k = lines[0].split(",").index(column)
    out = []
    for ln in lines:
        f = ln.split(",")
        out.append(",".join(f[:k] + f[k + 1 :] + [f[k]]))
    return out


def variants(lines: list[str]) -> dict[str, tuple[list[str], str, bool]]:
    """name -> (file, what is changed, whether the file meets the input conditions)."""
    return {
        # G46: the header differs from the names of section 5 in capitalisation only
        "header_age_upper": (header(lines, "age", "AGE"), "the header has AGE for age", False),
        "header_all_upper": ([lines[0].upper()] + lines[1:], "the header is in capitals throughout", False),
        "header_income_lower": (header(lines, "MonthlyIncome", "monthlyincome"),
                                "the header has monthlyincome for MonthlyIncome", False),
        # G48: ids that read as the same number
        "id_quoted_07": (cell(lines, 8, "", '"07"'), 'row 8 has the id "07" (quoted); row 7 has 7', False),
        "id_quoted_7_0": (cell(lines, 8, "", '"7.0"'), 'row 8 has the id "7.0" (quoted); row 7 has 7', False),
        "id_quoted_distinct": (cell(lines, 8, "", '"08"'),
                               'row 8 has the id "08" (quoted): the ids are distinct numbers', True),
        # G49: short rows
        "short_row_optional": (shorter(lines, 30, 1),
                               "row 30 has eleven fields: NumberOfDependents, the last column, is not there", True),
        "short_row_required": (shorter(lines, 30, 2),
                               "row 30 has ten fields: NumberOfTime60-89DaysPastDueNotWorse and "
                               "NumberOfDependents are not there", False),
        "short_row_required_last": (shorter(last(lines, "age"), 30, 1),
                                    "age is the last column, and row 30 has eleven fields: age is not there", False),
        # G48: ways of writing a number
        "age_quoted": (cell(lines, 30, "age", '"45"'), 'row 30 has age "45" (quoted)', True),
        "age_exponent": (cell(lines, 30, "age", "4.5e1"), "row 30 has age 4.5e1", True),
    }


def main() -> None:
    train = read("cs-training.csv", 3000)
    test = read("cs-test.csv", 200)
    write("good", train, test, "Valid files: first 3000 training rows, first 200 test rows.")
    d = "scenarios/fix_round5/"
    plan = [("good", FOUR)]
    for name, (lines, what, valid) in variants(train).items():
        kind = "Valid training file" if valid else "Faulty training file"
        write("train_" + name, lines, test, f"{kind}: {what}. The test file is valid.")
        plan.append(("train_" + name, "feature_engineering.sas"))
    plan.append(("good", FOUR))
    for name, (lines, what, valid) in variants(test).items():
        kind = "Valid test file" if valid else "Faulty test file"
        write("test_" + name, train, lines, f"{kind}: {what}. The training file is valid.")
        plan.append(("test_" + name, "predict.sas"))
    write("test_header_only_age_upper", train, [header(test, "age", "AGE")[0]],
          "Faulty test file: the header line only, with AGE for age. The training file is valid.")
    plan.append(("test_header_only_age_upper", "predict.sas"))
    plan.append(("good", "predict.sas"))
    (OUT / "plan.json").write_text(json.dumps(
        [{"label": label, "data_dir": d + label, "scripts": scripts} for label, scripts in plan], indent=1) + "\n")


if __name__ == "__main__":
    main()
