import sys, polars as pl
from pathlib import Path
import compare as C
cand=Path(sys.argv[1])
for name in ["model_coefficients.csv","stepwise_summary.csv","printed_fit_statistics.csv","printed_global_tests.csv","printed_rsquare.csv","printed_odds_ratios.csv"]:
    ref=C.read_text_csv(Path("reference")/name); cd=C.read_text_csv(cand/name)
    lab = "Test" if "Test" in ref.columns else ("Criterion" if "Criterion" in ref.columns else None)
    for col in ref.columns:
        r=ref[col]; c=cd[col]
        rn=r.str.strip_suffix("%").cast(pl.Float64,strict=False); cn=c.cast(pl.Float64,strict=False)
        if rn.drop_nulls().len()==0: continue
        du=pl.select(C.display_unit(pl.lit(r))).to_series()
        is_int=~r.str.contains(r"[.Ee]")
        if name=="printed_fit_statistics.csv": rel=pl.Series([C.LIKELIHOOD_REL_TOL]*len(r))
        elif name=="printed_global_tests.csv": rel=pl.Series([C.LIKELIHOOD_REL_TOL if t=="Likelihood Ratio" else C.MODEL_REL_TOL for t in ref["Test"]])
        else: rel=pl.Series([0.0 if col in C.DU_ONLY_COLS else C.MODEL_REL_TOL]*len(r))
        tol=pl.Series([0.0 if i else 2*u for i,u in zip(is_int,du)])+rel*rn.abs()
        diff=(rn-cn).abs()
        frac=diff/tol
        df=pl.DataFrame({"lab":ref[lab] if lab else pl.Series([""]*len(r)),"diff":diff,"frac":frac,"rel":diff/rn.abs()}).drop_nulls()
        for g,sub in (df.group_by("lab") if lab else [(("",),df)]):
            print(f"{name:28s} {col:22s} {str(g[0]):18s} max|d|={sub['diff'].max():.3g} maxrel={sub['rel'].max():.3g} max d/tol={sub['frac'].max():.3f}")
