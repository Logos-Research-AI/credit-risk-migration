import sys, math, os
sys.argv = [sys.argv[0], "1e-8"] + sys.argv[1:]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "roc.py")).read().split("cases = [")[0]
exec(src)
def d8(x):
    dec = max(4, 2 - math.floor(math.log10(abs(x))))
    return f"{x:.{dec}f}"
def write(data, label, out, name):
    d = pl.read_csv(data, infer_schema_length=0)
    r = roc_assoc(d["default_flag"].cast(pl.Int64).to_numpy(), d["pd_logistic"].cast(pl.Float64).to_numpy(), 1e-8)
    os.makedirs(out, exist_ok=True)
    with open(f"{out}/{name}", "w") as f:
        f.write("ROCModel,Area,StdErr,LowerArea,UpperArea,SomersD,Gamma,TauA\n")
        f.write(",".join([label, f"{r['Area']:.4f}", d8(r["StdErr"])] + [f"{r[k]:.4f}" for k in ("LowerArea", "UpperArea", "SomersD", "Gamma", "TauA")]) + "\n")
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
S = os.path.dirname(os.path.abspath(__file__))
for tag, base in (("ref", f"{J}/reference"), ("conv", f"{J}/fixtures/converged")):
    write(f"{base}/risk_scores_train.csv", "Training Set", f"{S}/roc_{tag}", "printed_roc_train.csv")
    write(f"{base}/risk_scores_validation.csv", "Validation Set", f"{S}/roc_{tag}", "printed_roc_validation.csv")
write(f"{J}/reference/risk_scores_validation.csv", "Logistic Model", f"{S}/roc_m_real", "printed_roc_metrics.csv")
for x in "abc":
    write(f"{J}/scenarios/edge_metrics_{x}/risk_scores_validation.csv", "Logistic Model", f"{S}/roc_m_{x}", "printed_roc_metrics.csv")
