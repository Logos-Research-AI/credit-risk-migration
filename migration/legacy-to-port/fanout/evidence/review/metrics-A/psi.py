import sys, numpy as np, polars as pl
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/metrics-A")
from pathlib import Path
J = Path("/Users/cristophersalvi/GitHub/sas-migration/judge")
exec(open(sys.path[0] + "/verify.py").read().split("bad = 0")[0])  # reuse helpers
for name, (inp, rdir) in SETS.items():
    out = {}
    for s in ("train", "validation"):
        d = read(inp / f"risk_scores_{s}.csv")
        b = d.with_columns(score_bin=pl.Series(rank_groups(d["pd_logistic"].to_numpy(), 10, False)))
        g = b.group_by("score_bin", maintain_order=True).agg(n=pl.len())
        n = b.height
        # A7 as written: Float64 division AFTER aggregation, plain polars col / scalar
        out[s] = (g.with_columns(pct=pl.col("n").cast(pl.Float64) / n), g.with_columns(pct=pl.col("n") / pl.lit(float(n))),
                  g.with_columns(pct=pl.Series(np.divide(g["n"].to_numpy().astype(float), float(n)))))
    for i, lab in enumerate(("A7 col/int", "A7 col/lit", "numpy IEEE")):
        a = out["train"][i].select("score_bin", train_pct="pct"); bb = out["validation"][i].select("score_bin", valid_pct="pct")
        j = a.join(bb, on="score_bin", how="inner", maintain_order="left").sort("score_bin").with_columns(
            psi_component=(pl.col("train_pct") - pl.col("valid_pct")) * (pl.col("train_pct") / pl.col("valid_pct")).log())
        comps = j["psi_component"].to_list()
        print(name, lab, "train_pct[0]", repr(j["train_pct"][0]), "psi comps nonzero:", sum(c != 0 for c in comps) if name == "real" else "", "first", comps[:2], "PSI", sum(comps))
    print("  ref:", open(rdir / "printed_psi_calculation.csv").read().splitlines()[:3])
