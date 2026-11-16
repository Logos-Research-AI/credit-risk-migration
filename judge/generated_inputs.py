"""Differential run of the corrected SAS against the Python port on GENERATED valid inputs.

The contract (judge/README.md) judges the port on the real data and four hand-made scenarios.
This script makes raw files that are valid input as the requirements define it
(migration/requirements/requirements.md, section 3) and whose rows sit on the edges of the
program's rules, so that the same contract can be run against a SAS run of each of them.

    uv run python generated_inputs.py make  --seed 1 --out ../out/generated/s01      # the two raw files
    uv run python run_sas.py --run-id gen_s01 --data-dir ../out/generated/s01        # the corrected SAS
    uv run python generated_inputs.py judge --seed 1 --data ../out/generated/s01 \
        --sas runs/gen_s01 --out ../out/generated/s01/port                           # the port, judged

`make` is deterministic in the seed. What a seed looks like (sizes, which special feature it
carries) is the table SEEDS below. Every field of every row is drawn either from a pool of edge
values (each threshold of a flag, band, age group or cap exactly and just either side; zero; very
large values; long numbers) or from an ordinary distribution close to the real data, so the model
fit has something to hold on to. The outcome is drawn from a logistic model of the row's own
values, so there are defaulters and non-defaulters at every edge and the fit is not separated.

`judge` runs the port stage by stage on the SAS run's files and end to end, exactly as
migration/legacy-to-port/parity/run_contract.sh does on the reference, and judges every stage
with compare.py --mode port against the SAS run. It writes judge_<line>_<stage>.txt/.json in the
output folder and prints one line per contract line.

Valid input (section 3), and how the generator keeps to it:
  * the twelve columns of section 5 and no others (the header of the real files);
  * only MonthlyIncome and NumberOfDependents are ever missing (NA, or blank in seed 11);
  * the training file has at least one known income;
  * the outcome is 0 or 1 in the training file, blank in the test file (as the real test file);
  * row ids are distinct within a file;
  * the three late-payment counts, dependents and credit lines are whole numbers, zero or more;
  * a known income is zero or more;
  * every value is a plain decimal number of at most 32 characters.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

JUDGE = Path(__file__).resolve().parent
ROOT = JUDGE.parent
HEADER = (",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,"
          "DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,"
          "NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents")
MAX_WIDTH = 32  # section 3: a number that can be written in at most 32 characters


@dataclass(frozen=True)
class Seed:
    train: int
    test: int  # 0 = a test file with its header and no applicant
    note: str
    edge: float = 0.5  # share of fields drawn from the edge pools
    empty_income_group: int | None = None  # age group (1-5) with no known income in the training file
    test_missing_group: int | None = None  # age group whose every test income is missing
    all_dependents_known: bool = False  # no missing NumberOfDependents in the training file
    ties: float = 0.0  # share of rows that repeat an earlier row (another id)
    wild: bool = False  # values the requirements allow and the real data does not have
    long_numbers: float = 0.02  # share of decimal fields written with up to 32 characters
    shuffled_ids: bool = False
    blank_missing: bool = False  # missing written as an empty field, not NA
    base_logit: float = -3.3  # sets the default rate


SEEDS: dict[int, Seed] = {
    1: Seed(400, 150, "small"),
    2: Seed(1200, 400, "medium"),
    3: Seed(300, 0, "smallest training file; the test file has its header and no applicant"),
    4: Seed(2500, 800, "age group 2 (30 to 39) has no known income in the training file", empty_income_group=2),
    5: Seed(800, 300, "no NumberOfDependents missing in the training file (a numeric column)", all_dependents_known=True),
    6: Seed(5000, 1000, "largest"),
    7: Seed(600, 200, "three rows in ten repeat an earlier row: tied probabilities", ties=0.3),
    8: Seed(1500, 500, "values the requirements allow and the real data lacks: negative utilization and debt "
                       "ratio, ages and real-estate loans with decimals, age 0", wild=True),
    9: Seed(3000, 600, "one decimal field in four written with up to 32 characters", long_numbers=0.25),
    10: Seed(500, 2000, "test file larger than the training file; every test income of the 60-and-over group "
                        "is missing", test_missing_group=5),
    11: Seed(2000, 500, "row ids shuffled and not contiguous; missing written as an empty field",
             shuffled_ids=True, blank_missing=True),
    12: Seed(1000, 300, "few defaulters (about one in ten)", base_logit=-4.7),
    13: Seed(700, 250, "nearly every field from the edge pools", edge=0.9),
    14: Seed(4000, 900, "large, age group 1 (under 30) with no known income, ties",
             empty_income_group=1, ties=0.1),
}

# ---- edge pools: each threshold of the program exactly and just either side ----------------------
# feature_engineering.sas: utilization and debt ratio are raw * 100; utilization bands 30/50/75, flags
# > 75 and > 100, cap 200; debt ratio bands 30/43/60, flags > 43 and > 60, cap 500.
UTIL_EDGES = ["0", "0.2999999", "0.3", "0.3000001", "0.4999999", "0.5", "0.5000001", "0.7499999", "0.75",
              "0.7500001", "0.9999999", "1", "1.0000001", "1.9999999", "2", "2.0000001", "0.29", "0.57",
              "0.1", "0.7", "50708", "0.000000001"]
DEBT_EDGES = ["0", "0.2999999", "0.3", "0.3000001", "0.4299999", "0.43", "0.4300001", "0.5999999", "0.6",
              "0.6000001", "4.9999999", "5", "5.0000001", "0.07", "0.14", "0.28", "0.56", "3296", "329664"]
# age groups < 30/40/50/60 (income medians), age categories < 25/35/50/65
AGE_EDGES = ["21", "24", "25", "26", "29", "30", "31", "34", "35", "36", "39", "40", "41", "49", "50", "51",
             "59", "60", "61", "64", "65", "66", "80", "109"]
# flag_low_income: income < 2500; income > 0 decides the interaction; zero and very large incomes
INCOME_EDGES = ["0", "1", "2499", "2499.99", "2500", "2500.01", "2501", "0.5", "5400", "10000", "99999",
                "100000", "1000000", "3008750", "0.01"]
DEPENDENT_EDGES = ["0", "1", "2", "3", "4", "10", "20"]  # flag_many_dependents: >= 3; > 0 divides the income
LATE_EDGES = ["0", "1", "2", "3", "4", "13", "98"]  # delinquency > 0; multiple delinquencies: total >= 3
LINES_EDGES = ["0", "1", "2", "3", "4", "20", "58"]  # flag_few_credit_lines: <= 2
ESTATE_EDGES = ["0", "1", "2", "3", "13", "54"]
WILD = {"util": ["-0.5", "-0.0000001"], "debt": ["-1", "-0.0000001"],
        "age": ["0", "29.5", "29.9999999", "30.0000001", "59.5", "64.9999999"], "estate": ["0.5", "2.5"]}


def age_group(age: float) -> int:
    return 1 if age < 30 else 2 if age < 40 else 3 if age < 50 else 4 if age < 60 else 5


def lengthen(rng: random.Random, text: str) -> str:
    """The same decimal number written longer, at most 32 characters: trailing zeros, or digits
    after the last one that leave the value within a hair of it."""
    if "e" in text or "E" in text:
        return text
    if "." not in text:
        text += "."
    room = MAX_WIDTH - len(text)
    if room <= 0:
        return text
    n = rng.randint(1, room)
    kind = rng.random()
    if kind < 0.4:
        return text + "0" * n
    if kind < 0.7:
        return text + "".join(rng.choice("0123456789") for _ in range(n))
    return text + "0" * (n - 1) + "1"


class Maker:
    def __init__(self, seed: int):
        self.cfg = SEEDS[seed]
        self.rng = random.Random(seed)

    def pick(self, edges: list[str], ordinary) -> str:
        return self.rng.choice(edges) if self.rng.random() < self.cfg.edge else ordinary()

    def decimal(self, text: str) -> str:
        return lengthen(self.rng, text) if self.rng.random() < self.cfg.long_numbers else text

    def row(self, training: bool) -> dict[str, str]:
        r, cfg = self.rng, self.cfg
        late = lambda rate: str(0 if r.random() < 1 - rate else min(98, 1 + int(r.expovariate(0.9))))
        age_pool = AGE_EDGES + (WILD["age"] if cfg.wild else [])
        age = self.pick(age_pool, lambda: str(max(21, min(100, round(r.gauss(52, 15))))))
        util_pool = UTIL_EDGES + (WILD["util"] if cfg.wild else [])
        debt_pool = DEBT_EDGES + (WILD["debt"] if cfg.wild else [])
        estate_pool = ESTATE_EDGES + (WILD["estate"] if cfg.wild else [])
        util = self.pick(util_pool, lambda: f"{min(1.0, r.betavariate(0.5, 1.2)):.9f}".rstrip("0").rstrip(".") or "0")
        debt = self.pick(debt_pool, lambda: f"{r.lognormvariate(-1.0, 1.0):.9f}".rstrip("0").rstrip("."))
        income = self.pick(INCOME_EDGES, lambda: str(max(0, round(r.lognormvariate(8.6, 0.6)))))
        dependents = self.pick(DEPENDENT_EDGES, lambda: str(min(6, int(r.expovariate(1.2)))))
        missing = "" if cfg.blank_missing else "NA"
        group = age_group(float(age))
        if r.random() < 0.2:
            income = missing
        if training and cfg.empty_income_group == group:
            income = missing
        if not training and cfg.test_missing_group == group:
            income = missing
        if r.random() < 0.05 and not (training and cfg.all_dependents_known):
            dependents = missing
        row = {
            "util": self.decimal(util), "age": age,
            "late30": self.pick(LATE_EDGES, lambda: late(0.16)),
            "debt": self.decimal(debt),
            "income": income if income == missing else self.decimal(income),
            "lines": self.pick(LINES_EDGES, lambda: str(max(0, round(r.gauss(8.5, 5))))),
            "late90": self.pick(LATE_EDGES, lambda: late(0.06)),
            "estate": self.pick(estate_pool, lambda: str(min(5, int(r.expovariate(1.0))))),
            "late60": self.pick(LATE_EDGES, lambda: late(0.05)),
            "dependents": dependents,
        }
        row["outcome"] = self.outcome(row) if training else ""
        return row

    def outcome(self, row: dict[str, str]) -> str:
        """0 or 1, from a logistic model of the row: signal for the fit, never a rule (no separation)."""
        num = lambda k: float(row[k])
        late_total = num("late30") + num("late60") + num("late90")
        z = (self.cfg.base_logit + 0.9 * (late_total > 0) + 0.7 * (num("late90") > 0) + 0.25 * min(late_total, 4)
             + 0.8 * (num("util") > 0.75) + 0.4 * (num("util") > 0.3) + 0.3 * (num("debt") > 0.43)
             - 0.012 * (min(num("age"), 90) - 50) - 0.02 * min(num("lines"), 20))
        return "1" if self.rng.random() < 1 / (1 + math.exp(-z)) else "0"

    def table(self, n: int, training: bool) -> list[str]:
        cfg, r = self.cfg, self.rng
        rows: list[dict[str, str]] = []
        for _ in range(n):
            if rows and r.random() < cfg.ties:
                rows.append(dict(r.choice(rows)))  # the same applicant again, under another id
            else:
                rows.append(self.row(training))
        if training and n and all(x["income"] in ("", "NA") for x in rows):
            rows[0]["income"] = "5400"  # section 3: at least one known income
        ids = list(range(1, n + 1))
        if cfg.shuffled_ids:
            ids = r.sample(range(1, 20 * n + 1), n)
        order = ("outcome", "util", "age", "late30", "debt", "income", "lines", "late90", "estate", "late60", "dependents")
        lines = [HEADER] + [",".join([str(i)] + [x[k] for k in order]) for i, x in zip(ids, rows)]
        for ln in lines[1:]:
            assert all(len(f) <= MAX_WIDTH for f in ln.split(",")), ln
        return lines


def make(seed: int, out: Path) -> None:
    cfg, mk = SEEDS[seed], Maker(seed)
    out.mkdir(parents=True, exist_ok=True)
    train, test = mk.table(cfg.train, True), mk.table(cfg.test, False)
    (out / "cs-training.csv").write_text("\n".join(train) + "\n")
    (out / "cs-test.csv").write_text("\n".join(test) + "\n")
    events = sum(ln.split(",")[1] == "1" for ln in train[1:])
    inc = HEADER.split(",").index("MonthlyIncome")
    missing_income = sum(ln.split(",")[inc] in ("", "NA") for ln in train[1:])
    info = {"seed": seed, "note": cfg.note, "training_rows": cfg.train, "test_rows": cfg.test,
            "defaulters": events, "training_incomes_missing": missing_income}
    (out / "generated.json").write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info))


# ---- the port, judged against a SAS run of the same files ----------------------------------------
def judge(seed: int, data: Path, sas: Path, out: Path, accept_warnings: bool) -> int:
    meta_path = sas / "run_meta.json"
    meta = json.loads(meta_path.read_text())
    errors = {k: v for k, v in meta.get("errors", {}).items() if v}
    if errors:
        print(f"seed {seed}: the SAS run has ERROR lines, nothing to judge against: {errors}")
        return 2
    new = sorted({w for v in meta.get("new_warnings", {}).values() for w in v})
    reviewed = set((meta.get("warnings_reviewed") or {}).get("warnings", []))
    if set(new) - reviewed:
        print(f"seed {seed}: the SAS run has WARNINGs not in judge/known_warnings.txt:")
        for w in new:
            print("   ", w)
        if not accept_warnings:
            print("    read them; rerun with --accept-warnings to record them as reviewed in the run's run_meta.json")
            return 2
        meta["warnings_reviewed"] = {"warnings": new, "by": "generated_inputs.py --accept-warnings"}
        meta_path.write_text(json.dumps(meta, indent=2))

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    split = out / "split_ids.csv"
    ids = [ln.split(",")[0] for ln in (sas / "model_features_train.csv").read_text().splitlines()[1:]]
    split.write_text("row_id\n" + "\n".join(ids) + "\n")
    timings: dict[str, float] = {}

    def port(name: str, module: str, *args: object) -> bool:
        t0 = time.time()
        res = subprocess.run(["uv", "run", "--quiet", "--project", str(ROOT / "port"), "python", "-m",
                              f"credit_risk.{module}", *map(str, args)], cwd=ROOT, capture_output=True, text=True)
        timings[name] = round(time.time() - t0, 1)
        (out / f"{name}.log").write_text(res.stdout + res.stderr)
        if res.returncode:
            print(f"    {name} CRASH: " + (res.stderr.strip().splitlines() or ["?"])[-1][:200])
        return res.returncode == 0

    verdicts: list[tuple[str, str, str]] = []

    def compare(line: str, stage: str, cand: Path) -> None:
        tag = f"{line}_{stage}"
        res = subprocess.run(["uv", "run", "--quiet", "python", "compare.py", str(sas.resolve()), str(cand.resolve()),
                              "--mode", "port", "--stage", stage, "--json", str((out / f"judge_{tag}.json").resolve())],
                             cwd=JUDGE, capture_output=True, text=True)
        text = res.stdout + res.stderr
        (out / f"judge_{tag}.txt").write_text(text)
        summary = next((ln for ln in text.splitlines() if "files pass" in ln), text.strip().splitlines()[-1][:120])
        verdict = {0: "PASS", 1: "FAIL"}.get(res.returncode, "UNUSABLE")
        verdicts.append((line, stage, verdict))
        print(f"  {line:<3} {stage:<8} {summary}  {verdict}")
        if verdict != "PASS":
            for ln in text.splitlines():
                if ln.startswith("FAIL") or ln.startswith("      -"):
                    print("      " + ln[:260])

    d = lambda name: out / name
    for name in ("r1_fe", "r2_train", "r3_metrics", "r4_predict", "r9_e2e"):
        d(name).mkdir()
    port("fe", "feature_engineering", "--data-dir", data, "--output-dir", d("r1_fe"), "--split-ids", split)
    compare("1", "fe", d("r1_fe"))
    port("train", "train", "--input-dir", sas, "--output-dir", d("r2_train"))
    compare("2", "train", d("r2_train"))
    port("metrics", "metrics_calculation", "--input-dir", sas, "--output-dir", d("r3_metrics"))
    compare("3", "metrics", d("r3_metrics"))
    port("predict", "predict", "--input-dir", d("r2_train"), "--data-dir", data,
         "--income-medians", sas / "income_medians.csv", "--output-dir", d("r4_predict"))
    compare("4", "predict", d("r4_predict"))
    e = d("r9_e2e")
    ok = (port("e2e_fe", "feature_engineering", "--data-dir", data, "--output-dir", e, "--split-ids", split)
          and port("e2e_train", "train", "--input-dir", e, "--output-dir", e)
          and port("e2e_metrics", "metrics_calculation", "--input-dir", e, "--output-dir", e)
          and port("e2e_predict", "predict", "--input-dir", e, "--data-dir", data,
                   "--income-medians", e / "income_medians.csv", "--output-dir", e))
    if not ok:
        print("  9   e2e      stopped at the first crashed step")
    for stage in ("fe", "train", "metrics", "predict"):
        compare("9", stage, e)
    (out / "verdicts.json").write_text(json.dumps(
        {"seed": seed, "verdicts": verdicts, "timings_s": timings, "sas_new_warnings": new}, indent=1) + "\n")
    return 0 if all(v == "PASS" for _, _, v in verdicts) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make", help="write cs-training.csv and cs-test.csv for a seed")
    m.add_argument("--seed", type=int, required=True, choices=sorted(SEEDS))
    m.add_argument("--out", type=Path, required=True)
    j = sub.add_parser("judge", help="run the port on a seed's files and judge it against the SAS run")
    j.add_argument("--seed", type=int, required=True, choices=sorted(SEEDS))
    j.add_argument("--data", type=Path, required=True, help="folder with the seed's two raw files")
    j.add_argument("--sas", type=Path, required=True, help="the SAS run of those files (judge/runs/<run-id>)")
    j.add_argument("--out", type=Path, required=True)
    j.add_argument("--accept-warnings", action="store_true",
                   help="record the SAS run's new WARNINGs as reviewed (after reading them)")
    args = ap.parse_args()
    if args.cmd == "make":
        make(args.seed, args.out.resolve())
        return 0
    return judge(args.seed, args.data.resolve(), args.sas.resolve(), args.out.resolve(), args.accept_warnings)


if __name__ == "__main__":
    sys.exit(main())
