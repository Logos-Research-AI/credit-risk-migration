"""Review of T10/T17: is `base_score + score_range * (1 - pd)` evaluated as two rounded operations
(Python float `600.0 + 250.0 * (1 - p)`), on frame columns as the port builds them?"""
import math, random, struct
import polars as pl
random.seed(7)
ps = [random.random() for _ in range(200000)] + [0.0, 1.0, 0.5, 0.1, 5e-324, 1 - 2**-53, 2**-60]
df = pl.DataFrame({"pd_logistic": ps}).with_columns(base_score=pl.lit(600.0), score_range=pl.lit(250.0))
out = df.with_columns(credit_risk_score=pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic")))
got = out.get_column("credit_risk_score").to_list()
b = lambda x: struct.pack(">d", x)
plain = sum(b(g) != b(600.0 + 250.0 * (1 - p)) for g, p in zip(got, ps))
fma = sum(b(g) != b(math.fma(250.0, 1 - p, 600.0)) for g, p in zip(got, ps))
print("rows", len(ps), "differ from two rounded operations:", plain, "; differ from a fused multiply-add:", fma)
r = pl.DataFrame({"base_rate": [0.05] * 3}).with_columns(x=pl.col("base_rate") + 0.02, y=pl.col("base_rate") + 0.15).row(0)
print("rates", b(r[1]) == b(0.05 + 0.02), b(r[2]) == b(0.05 + 0.15))
