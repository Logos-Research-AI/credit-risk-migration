import sys
import numpy as np
import polars as pl
R = "/Users/cristophersalvi/GitHub/sas-migration/"
sys.path.insert(0, R + "judge")
from compare import sas_best12
S = "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/fe-predict-A/"
fe = pl.read_parquet(S + "fe.parquet")
ref = pl.concat([pl.read_csv(R + "judge/reference/model_features_train.csv", infer_schema=False), pl.read_csv(R + "judge/reference/model_features_validation.csv", infer_schema=False)]).with_columns(pl.col("row_id").cast(pl.Float64))
m = ref.select("row_id", "utilization_debt_interaction").join(fe.select("row_id", "credit_utilization", "debt_ratio", "utilization_debt_interaction"), on="row_id", suffix="_m")
cu = m["credit_utilization"].to_numpy(); dr = m["debt_ratio"].to_numpy()
prod = cu * dr
forms = {
    "polars_expr": m["utilization_debt_interaction_m"].to_numpy(),
    "ieee_div": np.divide(prod, 100.0),
    "recip_mul": prod * (1 / 100.0),
    "cu*(dr/100)": cu * (dr / 100.0),
}
print("polars == ieee_div:", np.sum(forms["polars_expr"] == forms["ieee_div"]), "polars == recip:", np.sum(forms["polars_expr"] == forms["recip_mul"]), "n", len(cu))
rt = m["utilization_debt_interaction"].to_list()
for k, v in forms.items():
    bad = 0
    for r, x in zip(rt, v):
        ok = (abs(float(r) - x) <= 1e-6 * abs(float(r))) if "E" in r else sas_best12(float(x)) == r
        bad += not ok
    print(k, "mismatch", bad)
# single-element vs multi-element polars behaviour
s = pl.Series([0.3 * 7])
print(pl.DataFrame({"a": [2.1, 2.1]}).select(pl.col("a") / 100)["a"].to_list(), pl.DataFrame({"a": [2.1]}).select(pl.col("a") / 100)["a"].to_list(), 2.1 / 100, 2.1 * (1 / 100))
print(pl.__version__)
from decimal import Decimal
pa, ie = forms["polars_expr"], forms["ieee_div"]
diff_print = agree_p = agree_i = 0
maxunits = 0
for r, a, b in zip(rt, pa, ie):
    if "E" in r: continue
    sa, sb = sas_best12(float(a)), sas_best12(float(b))
    if sa != sb:
        diff_print += 1; agree_p += sa == r; agree_i += sb == r
    if sa != r:
        d = Decimal(r); unit = Decimal(1).scaleb(d.as_tuple().exponent)
        u = abs(Decimal(sa) - d) / unit
        maxunits = max(maxunits, u)
print("cells printing differently", diff_print, "SAS==polars", agree_p, "SAS==ieee", agree_i, "max units off (polars form)", maxunits)
fe2 = fe
print("FE exact cu 30/50/75:", [(fe2["credit_utilization"] == v).sum() for v in (30, 50, 75)], "dr 43/60:", [(fe2["debt_ratio"] == v).sum() for v in (43, 60)])
