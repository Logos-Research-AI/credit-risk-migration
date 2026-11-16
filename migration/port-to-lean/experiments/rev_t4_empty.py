"""Review of T4 (port-translator-6): fe_run_04_imputed on a credit_cleaned with columns and no row
(outside the unit's precondition as written: `0 < credit_cleaned.height`). Expected digest of the
Python result, to compare with the Lean one.
  PYTHONPATH=../../port uv run --project ../../port python experiments/rev_t4_empty.py"""
import sys
from pathlib import Path
import polars as pl
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rev_t4_probe as rp

names = ["VAR1", "SeriousDlqin2yrs", "age", "RevolvingUtilizationOfUnsecuredL", "NumberOfTime30-59DaysPastDueNotW", "DebtRatio",
         "NumberOfOpenCreditLinesAndLoans", "NumberOfTimes90DaysLate", "NumberRealEstateLoansOrLines",
         "NumberOfTime60-89DaysPastDueNotW", "MonthlyIncome", "NumberOfDependents"]
schema = {n: pl.Float64 for n in names} | {"age_group": pl.Int32, "MonthlyIncome_missing": pl.Int64, "Dependents_missing": pl.Int64}
cc0 = pl.DataFrame({n: [] for n in schema}, schema=schema)
ma = pl.DataFrame({"age_group": [1, 2, 3, 4, 5], "median_income": [5400.0, None, float("nan"), 6000.0, 7000.0],
                   "overall_median_income": [5000.0] * 5}, schema={"age_group": pl.Int32, "median_income": pl.Float64, "overall_median_income": pl.Float64})
out = rp.py04(cc0, ma)
print(out.schema, out.height)
print("digest input", rp.dgf(cc0), "digest result", rp.dgf(out))
