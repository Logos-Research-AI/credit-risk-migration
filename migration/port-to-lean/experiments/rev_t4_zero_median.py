"""Review of T4 (port-translator-6): the overall median when the known incomes hold zeros of both
signs. Runs feature_engineering.py:179-186 verbatim on small inputs and prints the bits of
overall_median_income; also whether such incomes pass the input check (text "-0").
  PYTHONPATH=../../port uv run --project ../../port python experiments/rev_t4_zero_median.py"""
import struct, sys, tempfile
from pathlib import Path
import polars as pl
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rev_t4_probe as rp
from credit_risk import feature_engineering as fe, sas_compat as sc

b = lambda x: None if x is None else struct.unpack("<Q", struct.pack("<d", x))[0]
im = pl.DataFrame({"age_group": [1], "median_income": [1.0]}, schema={"age_group": pl.Int32, "median_income": pl.Float64})
for v in ([-0.0, 0.0], [0.0, -0.0], [0.0, -0.0, -0.0], [-0.0, 0.0, 0.0], [-0.0, -0.0, 0.0, 0.0], [0.0, 0.0, -0.0, -0.0],
          [0.0, -0.0, 0.0, -0.0], [-0.0, 0.0, -0.0, 0.0], [-1.0, -0.0, 0.0, 1.0], [-1.0, 0.0, -0.0, 1.0], [0.0, -0.0, 5.0],
          [-0.0, 0.0, 5.0], [-0.0, -0.0], [0.0, 0.0]):
    out = rp.py02b(im, pl.DataFrame({"MonthlyIncome": v}))
    m = out.get_column("overall_median_income")[0]
    g = pl.DataFrame({"g": [1] * len(v), "x": v}).group_by("g", maintain_order=True).agg(pl.col("x").median())["x"][0]
    print(v, "-> Series median bits", b(m), repr(m), "| group_by median", repr(g))

# does a file with incomes "-0" and "0" pass the input check and reach the medians?
hdr = ",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents\n"
rows = ["1,0,0.5,40,0,0.5,0,1,0,0,0,0\n", "2,0,0.5,41,0,0.5,-0,1,0,0,0,2\n", "3,0,0.5,42,0,0.5,NA,1,0,0,0,3\n"]
for order in ([0, 1, 2], [1, 0, 2]):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "cs-training.csv").write_text(hdr + "".join(rows[i] for i in order))
        (d / "split.csv").write_text("row_id\n1\n2\n3\n")
        rec = {}
        def prof(fr, ev, arg):
            if ev == "return" and fr.f_code is fe.run.__code__:
                rec.update(fr.f_locals)
        sys.setprofile(prof)
        try:
            fe.run(d, d / "out", split_ids=d / "split.csv")
        except Exception as e:
            print("raised", e)
        finally:
            sys.setprofile(None)
        print("order", order, "MonthlyIncome", [repr(x) for x in rec["credit_raw_clean"]["MonthlyIncome"].to_list()])
        print("  income_medians_all", rec["income_medians_all"].rows(), [repr(x) for x in rec["income_medians_all"]["overall_median_income"].to_list()[:1]],
              [repr(x) for x in rec["income_medians_all"]["median_income"].to_list()])
        print("  credit_imputed monthly_income", [repr(x) for x in rec["credit_imputed"]["monthly_income"].to_list()])
        print("  income_per_dependent", [repr(x) for x in rec["credit_features"]["income_per_dependent"].to_list()])
        print((d / "out" / "income_medians.csv").read_text())
        print("\n".join(",".join(l.split(",")[:4] + ["..."] + [l.split(",")[rec["credit_features"].columns.index("income_per_dependent")]]) for l in (d / "out" / "model_features_train.csv").read_text().splitlines()))
