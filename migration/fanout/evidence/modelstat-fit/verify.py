"""modelstat-fit shard: rebuild the six PROC LOGISTIC ODS files from first principles
(numpy Newton, converged to max|step| < 1e-10) and measure them against the reference.
Run from judge/:  uv run python <this file> <outdir>"""
import math, sys
from pathlib import Path
import numpy as np
import polars as pl

REF = Path("reference")
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
d = pl.read_csv(REF / "model_features_train.csv", infer_schema_length=None)
y = d["default_flag"].to_numpy().astype(float)
n = len(y)
C = """credit_utilization_capped debt_ratio_capped num_late_30_59 num_late_60_89 num_late_90_plus
total_late_payments has_delinquency has_serious_delinquency age monthly_income log_monthly_income
num_credit_lines num_real_estate_loans log_num_credit_lines num_dependents income_per_dependent credit_lines_per_person
flag_high_utilization flag_very_high_utilization flag_high_debt_ratio flag_very_high_debt_ratio
flag_recent_late_payments flag_serious_delinquency flag_multiple_delinquencies flag_low_income
flag_many_dependents flag_few_credit_lines total_risk_flags credit_util_category debt_category age_category
financial_health age_income_interaction utilization_debt_interaction MonthlyIncome_missing Dependents_missing""".split()
full = {}
for c in C:
    assert c[:20] not in full, c
    full[c[:20]] = c
Z = {c: d[c].to_numpy().astype(float) for c in C}
Z20 = 1.959963984540054  # probit(0.975)


def chi2_sf1(x):  # DF = 1
    return math.erfc(math.sqrt(max(x, 0) / 2))


def chi2_sf(x, k):  # closed form for integer DF (scipy not installed in judge env)
    h = x / 2
    if k % 2 == 0:
        t = s = math.exp(-h)
        for i in range(1, k // 2):
            t *= h / i; s += t
        return s
    s = math.erfc(math.sqrt(h)); t = math.sqrt(2 * x / math.pi) * math.exp(-h)
    for i in range(1, (k + 1) // 2):
        s += t; t *= x / (2 * i + 1)
    return s


def fit(cols):
    X = np.column_stack([np.ones(n)] + [Z[c] for c in cols]); b = np.zeros(X.shape[1])
    for _ in range(200):
        p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p)
        s = np.linalg.solve(X.T @ (X * W[:, None]), X.T @ (y - p)); b += s
        if np.max(np.abs(s)) < 1e-10:
            break
    p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p)
    cov = np.linalg.inv(X.T @ (X * W[:, None]))
    m2ll = -2 * np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    return X, b, p, cov, m2ll


def pval(p):  # PVALUE6.4
    return "<.0001" if p < 1e-4 else f"{p:.4f}"


def d8(x):  # hypothesis for SAS D8. (fitted on the 38 Estimate/StdErr cells)
    ax = abs(x); neg = x < 0
    if ax < 1e-5:
        m, e = f"{x:.2E}".split("E")
        return f"{m}E{int(e)}"
    intlen = len(str(int(ax)))
    cap = 8 - intlen - 1 - (1 if neg else 0)
    need = max(0, 3 - (math.floor(math.log10(ax)) + 1))
    return f"{x:.{min(cap, max(4, need))}f}"


def sas_round(x):
    return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)


# ---- intercept-only (step 0)
_, b0, p0, _, m2ll0 = fit([])
ybar = y.mean()
print("-2LL0", m2ll0, "closed form", -2 * n * (ybar * math.log(ybar) + (1 - ybar) * math.log(1 - ybar)))

# ---- path from the stepwise summary (decided by batch-1 row 14)
sw = pl.read_csv(REF / "stepwise_summary.csv", infer_schema=False)
model, steps = [], []
for r in sw.iter_rows(named=True):
    if r["EffectEntered"]:
        model = model + [full[r["EffectEntered"]]]
    else:
        model = [c for c in model if c != full[r["EffectRemoved"]]]
    steps.append(list(model))

fs = [("0", "M2LOGL0", "-2 Log L", "=", str(sas_round(m2ll0)), f"{m2ll0:.3f}")]
gt, rs, swrows = [], [], []
prev_fit = fit([])
lnn = math.log(n)
for k, (r, cols) in enumerate(zip(sw.iter_rows(named=True), steps), 1):
    # summary row: score (entry) at the previous model's fit, or Wald (removal) at the previous fit
    Xp, bp, pp, covp, _ = prev_fit
    if r["EffectEntered"]:
        z = Z[full[r["EffectEntered"]]]; W = pp * (1 - pp)
        v = Xp.T @ (z * W); V = z @ (z * W) - v @ np.linalg.solve(Xp.T @ (Xp * W[:, None]), v)
        U = z @ (y - pp); s = U * U / V
        swrows.append((str(k), r["EffectEntered"], "", "1", str(len(cols)), f"{s:.4f}", "_", pval(chi2_sf1(s))))
    else:
        prevcols = steps[k - 2]
        i = prevcols.index(full[r["EffectRemoved"]]) + 1
        w = bp[i] ** 2 / covp[i, i]
        swrows.append((str(k), "", r["EffectRemoved"], "1", str(len(cols)), "_", f"{w:.4f}", pval(chi2_sf1(w))))
    X, b, p, cov, m2ll = fit(cols)
    q = len(cols)
    fs += [(str(k), "AIC", "AIC", "", str(sas_round(m2ll0 + 2)), f"{m2ll + 2 * (q + 1):.3f}"),
           (str(k), "SBC", "SC", "", str(sas_round(m2ll0 + lnn)), f"{m2ll + (q + 1) * lnn:.3f}"),
           (str(k), "M2LOGL", "-2 Log L", "", str(sas_round(m2ll0)), f"{m2ll:.3f}")]
    lr = m2ll0 - m2ll
    U0 = X.T @ (y - ybar); I0 = X.T @ X * (ybar * (1 - ybar))
    score = U0 @ np.linalg.solve(I0, U0)
    bb = b[1:]; wald = bb @ np.linalg.solve(cov[1:, 1:], bb)
    for t, v in (("Likelihood Ratio", lr), ("Score", score), ("Wald", wald)):
        gt.append((str(k), t, f"{v:.4f}", str(q), pval(chi2_sf(v, q))))
    r2 = 1 - math.exp(-lr / n); r2max = 1 - math.exp(-m2ll0 / n)
    rs.append((str(k), "R-Square", f"{r2:.4f}", f"{r2:.6f}", "Max-rescaled R-Square", f"{r2 / r2max:.4f}", f"{r2 / r2max:.6f}"))
    prev_fit = (X, b, p, cov, m2ll)

# final model tables
X, b, p, cov, m2ll = prev_fit
cols = steps[-1]
order = [c for c in C if c in cols]  # MODEL statement order
idx = {c: i + 1 for i, c in enumerate(cols)}
pe = [("Intercept", "1", d8(b[0]), d8(math.sqrt(cov[0, 0])), f"{b[0] ** 2 / cov[0, 0]:.4f}", pval(chi2_sf1(b[0] ** 2 / cov[0, 0])), "MLE")]
orr = []
for c in order:
    i = idx[c]; se = math.sqrt(cov[i, i]); w = b[i] ** 2 / cov[i, i]
    pe.append((c[:20], "1", d8(b[i]), d8(se), f"{w:.4f}", pval(chi2_sf1(w)), "MLE"))
    orr.append((c[:20], f"{math.exp(b[i]):.3f}", f"{math.exp(b[i] - Z20 * se):.3f}", f"{math.exp(b[i] + Z20 * se):.3f}"))


print("RAW", {c[:20]: (b[idx[c]], math.sqrt(cov[idx[c], idx[c]])) for c in ("income_per_dependent", "debt_ratio_capped", "age_income_interaction")})

def write(name, header, rows):
    pl.DataFrame([list(r) for r in rows], schema=header, orient="row").write_csv(OUT / name)


write("model_coefficients.csv", ["Variable", "DF", "Estimate", "StdErr", "WaldChiSq", "ProbChiSq", "_ESTTYPE_"], pe)
write("stepwise_summary.csv", ["Step", "EffectEntered", "EffectRemoved", "DF", "NumberInModel", "ScoreChiSq", "WaldChiSq", "ProbChiSq"], swrows)
write("printed_fit_statistics.csv", ["Step", "RowId", "Criterion", "Equals", "InterceptOnly", "InterceptAndCovariates"], fs)
write("printed_global_tests.csv", ["Step", "Test", "ChiSq", "DF", "ProbChiSq"], gt)
write("printed_rsquare.csv", ["Step", "Label1", "cValue1", "nValue1", "Label2", "cValue2", "nValue2"], rs)
write("printed_odds_ratios.csv", ["Effect", "OddsRatioEst", "LowerCL", "UpperCL"], orr)

# ---- measurement: per file/column max abs and rel diff, text identity
for name in ["model_coefficients.csv", "stepwise_summary.csv", "printed_fit_statistics.csv",
             "printed_global_tests.csv", "printed_rsquare.csv", "printed_odds_ratios.csv"]:
    ref = pl.read_csv(REF / name, infer_schema=False).fill_null("")
    cand = pl.read_csv(OUT / name, infer_schema=False).fill_null("")
    assert ref.columns == cand.columns and ref.height == cand.height, name
    same = sum(a == b for col in ref.columns for a, b in zip(ref[col], cand[col]))
    tot = ref.height * ref.width
    print(f"\n== {name}: {same}/{tot} cells text-identical")
    for col in ref.columns:
        diffs = []
        for i, (a, bb) in enumerate(zip(ref[col], cand[col])):
            try:
                fa, fb = float(a), float(bb)
            except ValueError:
                if a != bb:
                    print(f"   TEXT {col} row {i}: ref={a!r} cand={bb!r}")
                continue
            if a != bb:
                diffs.append((abs(fa - fb), abs(fa - fb) / max(abs(fa), 1e-300), a, bb, i))
        if diffs:
            ma = max(diffs); mr = max(diffs, key=lambda t: t[1])
            print(f"   {col}: {len(diffs)} text diffs; max abs {ma[0]:.3g} (ref {ma[2]} cand {ma[3]} row {ma[4]}); max rel {mr[1]:.3g} (ref {mr[2]} cand {mr[3]})")
