import polars as pl
from credit_risk import sas_compat as sc
for name, df in (("str flag", pl.DataFrame({"default_flag": ["1", "0"], "pd_logistic": [.1, .2]})), ("str pd", pl.DataFrame({"default_flag": [1., 0.], "pd_logistic": ["a", "b"]}))):
    try:
        r = (df.filter(pl.col("pd_logistic").is_not_null()).group_by("pd_logistic", maintain_order=True)
             .agg(n_bad=sc.flag(pl.col("default_flag") == 1).sum(), n_good=sc.flag(pl.col("default_flag") == 0).sum()).sort("pd_logistic", maintain_order=True))
        print(name, r.schema, r.rows())
    except Exception as e:
        print(name, type(e).__name__, str(e)[:100])
