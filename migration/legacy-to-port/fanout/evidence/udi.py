import polars as pl, numpy as np, compare as C
from decimal import Decimal, ROUND_HALF_UP
raw = pl.read_csv("../data/cs-training.csv", infer_schema=False).rename({"": "row_id"})
ref = pl.concat([pl.read_csv(f"reference/model_features_{s}.csv", infer_schema=False) for s in ("train","validation")])
d = ref.select("row_id","utilization_debt_interaction").join(raw.select("row_id","RevolvingUtilizationOfUnsecuredLines","DebtRatio"), on="row_id")
R = np.array([float(x) for x in d["RevolvingUtilizationOfUnsecuredLines"]]); D = np.array([float(x) for x in d["DebtRatio"]])
u, dr = R*100, D*100
forms = {"ieee (u*d)/100": (u*dr)/100, "u*d*0.01": (u*dr)*0.01}
def best12_dbl(x):  # double rounding: 15 significant digits first, then BEST12
    return C.sas_best12(float(f"{x:.15g}"))
def best12_halfup(x):  # exact decimal value, round half up at the 12-char position
    if x == 0: return "0"
    ilen = len(str(int(abs(x)))) + (x < 0); dec = max(0, 11 - ilen)
    s = str(Decimal(x).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP))
    if "." in s: s = s.rstrip("0").rstrip(".")
    return s
refv = d["utilization_debt_interaction"].to_list()
for name, v in forms.items():
    for pname, pr in [("sas_best12", C.sas_best12), ("15g-then-best12", best12_dbl), ("exact half-up", best12_halfup)]:
        bad = sum(1 for a, b in zip(v, refv) if "E" not in b and pr(float(a)) != b)
        print(f"{name:16s} {pname:16s} mismatches {bad}")
