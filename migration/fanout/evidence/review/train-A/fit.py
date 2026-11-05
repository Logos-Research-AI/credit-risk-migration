"""train-A independent recompute of the stepwise model statistics (numpy only)."""
import math, sys
import numpy as np, polars as pl
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/train-A"); from mystats import chi2, norm

R = '/Users/cristophersalvi/GitHub/sas-migration/judge/reference/'
d = pl.read_csv(R + 'model_features_train.csv', infer_schema_length=None)
y = d['default_flag'].to_numpy().astype(float)
n = len(y)
MODEL = """credit_utilization_capped debt_ratio_capped num_late_30_59 num_late_60_89 num_late_90_plus
total_late_payments has_delinquency has_serious_delinquency age monthly_income log_monthly_income
num_credit_lines num_real_estate_loans log_num_credit_lines num_dependents income_per_dependent credit_lines_per_person
flag_high_utilization flag_very_high_utilization flag_high_debt_ratio flag_very_high_debt_ratio
flag_recent_late_payments flag_serious_delinquency flag_multiple_delinquencies flag_low_income
flag_many_dependents flag_few_credit_lines total_risk_flags credit_util_category debt_category age_category
financial_health age_income_interaction utilization_debt_interaction MonthlyIncome_missing Dependents_missing""".split()
full = {c[:20]: c for c in MODEL}
assert len(full) == len(MODEL)

def fit(cols, tol=1e-10):
    X = np.column_stack([np.ones(n)] + [d[c].to_numpy().astype(float) for c in cols])
    b = np.zeros(X.shape[1])
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p)
        H = X.T @ (X * W[:, None]); s = np.linalg.solve(H, X.T @ (y - p)); b = b + s
        if np.abs(s).max() < tol: break
    p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p)
    V = np.linalg.inv(X.T @ (X * W[:, None]))
    ll = np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    return X, b, p, V, -2 * ll

ss = pl.read_csv(R + 'stepwise_summary.csv', infer_schema=False)
ybar = y.mean()
m2ll0 = -2 * n * (ybar * math.log(ybar) + (1 - ybar) * math.log(1 - ybar))
model = []
fs, gt, rs, sw = [], [], [], []
prev = None
pv = lambda p: '<.0001' if p < 1e-4 else f'{p:.4f}'
# step 0 fit (intercept only)
X0, b0, p0, V0, m0 = fit([])
print('m2ll0 closed', m2ll0, 'newton', m0)
fs.append(('0', 'M2LOGL0', '-2 Log L', '=', str(round(m2ll0)), f'{m2ll0:.3f}'))
for row in ss.iter_rows(named=True):
    k = row['Step']
    Xp, bp, pp, Vp, _ = prev if prev else (X0, b0, p0, V0, m0)
    if row['EffectEntered']:
        c = full[row['EffectEntered']]
        z = d[c].to_numpy().astype(float); Wp = pp * (1 - pp)
        v = Xp.T @ (z * Wp); Vz = z @ (z * Wp) - v @ np.linalg.solve(Xp.T @ (Xp * Wp[:, None]), v)
        U = z @ (y - pp); stat = U * U / Vz
        model.append(c)
        sw.append((k, row['EffectEntered'], '', '1', str(len([m for m in model])), f'{stat:.4f}', '_', pv(chi2.sf(stat, 1))))
    else:
        c = full[row['EffectRemoved']]
        i = [m for m in model].index(c) + 1
        stat = bp[i] ** 2 / Vp[i, i]
        model.remove(c)
        sw.append((k, '', row['EffectRemoved'], '1', str(len(model)), '_', f'{stat:.4f}', pv(chi2.sf(stat, 1))))
    # keep in MODEL order for the design matrix
    cols = [m for m in MODEL if m in model]
    model = cols
    X, b, p, V, m2 = fit(cols)
    prev = (X, b, p, V, m2)
    q = len(cols)
    fs += [(k, 'AIC', 'AIC', '', str(round(m2ll0 + 2)), f'{m2 + 2*(q+1):.3f}'),
           (k, 'SBC', 'SC', '', str(round(m2ll0 + math.log(n))), f'{m2 + (q+1)*math.log(n):.3f}'),
           (k, 'M2LOGL', '-2 Log L', '', str(round(m2ll0)), f'{m2:.3f}')]
    LR = m2ll0 - m2
    U0 = X.T @ (y - ybar); I0 = ybar * (1 - ybar) * X.T @ X
    sc = U0 @ np.linalg.solve(I0, U0)
    bs = b[1:]; C = V[1:, 1:]; wald = bs @ np.linalg.solve(C, bs)
    for t, s in (('Likelihood Ratio', LR), ('Score', sc), ('Wald', wald)):
        gt.append((k, t, f'{s:.4f}', str(q), pv(chi2.sf(s, q))))
    r2 = 1 - math.exp(-LR / n); mx = r2 / (1 - math.exp(-m2ll0 / n))
    rs.append((k, 'R-Square', f'{r2:.4f}', f'{r2:.6f}', 'Max-rescaled R-Square', f'{mx:.4f}', f'{mx:.6f}'))

VERB=True
def cmp(name, rows, cols):
    ref = pl.read_csv(R + name, infer_schema=False).fill_null('')
    assert ref.columns == cols, (ref.columns, cols)
    nd = 0; maxrel = {}
    for a, r in zip(rows, ref.iter_rows()):
        for c, x, z in zip(cols, a, r):
            x = str(x)
            if x != z:
                nd += 1
                if VERB: print('   ', a[0], c, x, z)
                try:
                    rel = abs(float(x) - float(z)) / abs(float(z)); maxrel[c] = max(maxrel.get(c, 0), rel)
                except ValueError:
                    print('  TEXT DIFF', name, c, x, z)
    print(name, 'rows', len(rows), ref.height, 'cells differing', nd, 'maxrel', maxrel)

cmp('printed_fit_statistics.csv', fs, ['Step','RowId','Criterion','Equals','InterceptOnly','InterceptAndCovariates'])
cmp('printed_global_tests.csv', gt, ['Step','Test','ChiSq','DF','ProbChiSq'])
cmp('printed_rsquare.csv', rs, ['Step','Label1','cValue1','nValue1','Label2','cValue2','nValue2'])
cmp('stepwise_summary.csv', sw, ['Step','EffectEntered','EffectRemoved','DF','NumberInModel','ScoreChiSq','WaldChiSq','ProbChiSq'])

# final model
X, b, p, V, m2 = prev
se = np.sqrt(np.diag(V))
names = ['Intercept'] + [c[:20] for c in model]
def d8(x):
    if abs(x) < 1e-5:
        s = f'{x:.2E}'; m, e = s.split('E'); return f'{m}E{int(e)}'
    ip = len(str(int(abs(x))))
    sig = max(4, 3 - int(math.floor(math.log10(abs(x)))) - 1) if x != 0 else 4
    dd = min(8 - ip - 1 - (1 if x < 0 else 0), sig)
    return f'{x:.{dd}f}'
pe = []
for nm, bi, si in zip(names, b, se):
    w = (bi / si) ** 2
    pe.append((nm, '1', d8(bi), d8(si), f'{w:.4f}', pv(chi2.sf(w, 1)), 'MLE'))
cmp('model_coefficients.csv', pe, ['Variable','DF','Estimate','StdErr','WaldChiSq','ProbChiSq','_ESTTYPE_'])
z = norm.ppf(0.975)
orr = [(nm, f'{math.exp(bi):.3f}', f'{math.exp(bi - z*si):.3f}', f'{math.exp(bi + z*si):.3f}') for nm, bi, si in zip(names[1:], b[1:], se[1:])]
cmp('printed_odds_ratios.csv', orr, ['Effect','OddsRatioEst','LowerCL','UpperCL'])
np.save('/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/train-A/final_b.npy', b)
print('final model', model)
# pd vs reference
rst = pl.read_csv(R + 'risk_scores_train.csv', infer_schema_length=None)
assert (rst['row_id'] == d['row_id']).all()
print('max |pd - ref pd|', np.abs(p - rst['pd_logistic'].to_numpy()).max())
# raw values for d8 boundary
for nm, bi, si in zip(names, b, se):
    print(f'  {nm:22s} {bi: .6e} {si: .6e}')

import os
OUT = '/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/train-A/cand'
os.makedirs(OUT, exist_ok=True)
def wr(name, cols, rows):
    with open(f'{OUT}/{name}', 'w') as f:
        f.write(','.join(cols) + '\n')
        for r in rows: f.write(','.join(str(x) for x in r) + '\n')
wr('printed_fit_statistics.csv', ['Step','RowId','Criterion','Equals','InterceptOnly','InterceptAndCovariates'], fs)
wr('printed_global_tests.csv', ['Step','Test','ChiSq','DF','ProbChiSq'], gt)
wr('printed_rsquare.csv', ['Step','Label1','cValue1','nValue1','Label2','cValue2','nValue2'], rs)
wr('stepwise_summary.csv', ['Step','EffectEntered','EffectRemoved','DF','NumberInModel','ScoreChiSq','WaldChiSq','ProbChiSq'], sw)
wr('model_coefficients.csv', ['Variable','DF','Estimate','StdErr','WaldChiSq','ProbChiSq','_ESTTYPE_'], pe)
wr('printed_odds_ratios.csv', ['Effect','OddsRatioEst','LowerCL','UpperCL'], orr)
np.save(OUT + '/../my_pd_train.npy', p)
# validation pd from my model
dv = pl.read_csv(R + 'model_features_validation.csv', infer_schema_length=None)
Xv = np.column_stack([np.ones(dv.height)] + [dv[c].to_numpy().astype(float) for c in model])
np.save(OUT + '/../my_pd_valid.npy', 1 / (1 + np.exp(-(Xv @ b))))
np.save(OUT + '/../my_V.npy', V); np.save(OUT + '/../my_X.npy', X)
