import contextlib, io, sys, tempfile
from pathlib import Path
import polars as pl
from credit_risk import feature_engineering as fe, sas_compat as sc
E = ["VAR1","SeriousDlqin2yrs","age","MonthlyIncome","NumberOfDependents","RevolvingUtilizationOfUnsecuredL","DebtRatio",
     "NumberOfTime30-59DaysPastDueNotW","NumberOfTime60-89DaysPastDueNotW","NumberOfTimes90DaysLate","NumberOfOpenCreditLinesAndLoans","NumberRealEstateLoansOrLines"]
def run(frame):
    rec = {}
    o = sc.proc_import_csv
    def prof(fr, ev, arg):
        if ev in ("return", "exception") and fr.f_code is fe.run.__code__:
            rec["L"] = dict(fr.f_locals)
    with tempfile.TemporaryDirectory() as d:
        sc.proc_import_csv = lambda p, guessingrows=20: frame
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(Path(d), Path(d)/"o", split_ids=Path(__file__).resolve().parents[1]/"inputs/split_ids.csv")
        except Exception as e:
            rec["exc"] = type(e).__name__ + ": " + str(e)[:80]
        finally:
            sys.setprofile(None); sc.proc_import_csv = o
    L = rec.get("L", {})
    return rec.get("exc"), {k: L.get(k) for k in ("columns_ok","bad_rows","duplicate_ids","known_incomes")}, (L.get("credit_raw").columns if L.get("credit_raw") is not None else None)
good = {n: [1.0, 2.0] for n in E}; good["VAR1"] = [1.0, 2.0]; good["SeriousDlqin2yrs"] = [0.0, 1.0]
def fr(names=None, **over):
    d = dict(good); d.update(over)
    f = pl.DataFrame(d)
    return f.rename(dict(zip(E, names))) if names else f
print("good", run(fr()))
n = list(E); n[0] = "AGE"   # no VAR1; 'AGE' and 'age'
print("AGE+age, 12 columns", run(fr(n)))
print("3 columns age, AGE, x", run(pl.DataFrame({"age": [1.0], "AGE": [2.0], "x": [3.0]})))
n = list(E); n[1] = "ſeriousDlqin2yrs"
print("long-s name", run(fr(n)), repr("ſeriousDlqin2yrs".upper()))
n = list(E); n[2] = "aɡe"
print("non-ascii other", run(fr(n)))
print("int column age", run(fr(age=[30, 40])))
print("int Serious", run(fr(SeriousDlqin2yrs=[0, 1])))
print("bool column", run(fr(DebtRatio=[True, False])))
print("NaN count col", run(fr(**{"NumberOfTimes90DaysLate": [float("nan"), 1.0]})))
print("inf count col", run(fr(**{"NumberOfTimes90DaysLate": [float("inf"), 1.0]})))
print("NaN id twice", run(fr(VAR1=[float("nan"), float("nan")])))
print("-0.0 / 0.0 ids", run(fr(VAR1=[-0.0, 0.0])))
print("text cell ß in income", run(fr(MonthlyIncome=["nɑ", "5"])))
print("text income 'ｎａ' fullwidth", run(fr(MonthlyIncome=["ｎａ", "5"])))
print("no columns frame", run(pl.DataFrame()))
print("12 cols 0 rows", run(fr().clear()))
print("null dtype column", run(fr(NumberOfDependents=pl.Series([None, None]))))
print("with_columns lit on no-column frame:", pl.DataFrame().with_columns(pl.lit(None, dtype=pl.Float64).alias("a")).shape)
