import polars as pl, numpy as np
t=pl.read_csv('/Users/cristophersalvi/GitHub/sas-migration/judge/reference/risk_scores_train.csv',infer_schema=False).select(pl.col('pd_logistic').cast(pl.Float64))
n=t.height
t=t.with_columns(score_bin=(pl.col('pd_logistic').rank('average')*10/(n+1)).floor().cast(pl.Int64))
g=t.group_by('score_bin',maintain_order=True).agg(c=pl.len())
a=g.with_columns(p=pl.col('c')/n)
print(a['p'].unique().to_list(), 10500/105000)
b=g.with_columns(p=pl.col('c').cast(pl.Float64)/pl.lit(float(n)))
print(b['p'].unique().to_list())
