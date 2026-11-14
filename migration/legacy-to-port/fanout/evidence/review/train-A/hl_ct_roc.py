"""train-A: HL partition, HL chi-square, ctable and ROC from a pd vector (numpy only)."""
import math, sys, os
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(__file__))
from mystats import chi2

R = '/Users/cristophersalvi/GitHub/sas-migration/judge/reference/'
S = os.path.dirname(__file__)
which = sys.argv[1]  # ref | conv | mine
MODEL_FINAL = ['credit_utilization_capped', 'debt_ratio_capped', 'has_delinquency', 'has_serious_delinquency', 'log_monthly_income', 'num_real_estate_loans', 'num_dependents', 'income_per_dependent', 'credit_lines_per_person', 'flag_high_utilization', 'flag_very_high_utilization', 'flag_very_high_debt_ratio', 'flag_recent_late_payments', 'flag_multiple_delinquencies', 'flag_few_credit_lines', 'credit_util_category', 'financial_health', 'age_income_interaction']
d = pl.read_csv(R + 'model_features_train.csv', infer_schema_length=None)
dv = pl.read_csv(R + 'model_features_validation.csv', infer_schema_length=None)
if which == 'ref':
    rt = pl.read_csv(R + 'risk_scores_train.csv', infer_schema_length=None)
    rv = pl.read_csv(R + 'risk_scores_validation.csv', infer_schema_length=None)
elif which == 'conv':
    F = '/Users/cristophersalvi/GitHub/sas-migration/judge/fixtures/converged/'
    rt = pl.read_csv(F + 'risk_scores_train.csv', infer_schema_length=None)
    rv = pl.read_csv(F + 'risk_scores_validation.csv', infer_schema_length=None)
else:
    rt = d.select('row_id').with_columns(pl.Series('pd_logistic', np.load(S + '/my_pd_train.npy')))
    rv = dv.select('row_id').with_columns(pl.Series('pd_logistic', np.load(S + '/my_pd_valid.npy')))
t = d.join(rt.select('row_id', 'pd_logistic'), on='row_id', how='left', maintain_order='left')
v = dv.join(rv.select('row_id', 'pd_logistic'), on='row_id', how='left', maintain_order='left')
assert t['pd_logistic'].null_count() == 0 and v['pd_logistic'].null_count() == 0
y = t['default_flag'].to_numpy().astype(float); p = t['pd_logistic'].to_numpy()
N = len(y)
OUT = f'{S}/cand_{which}'; os.makedirs(OUT, exist_ok=True)
def wr(name, cols, rows):
    with open(f'{OUT}/{name}', 'w') as f:
        f.write(','.join(cols) + '\n')
        for r in rows: f.write(','.join(str(x) for x in r) + '\n')
pv = lambda q: '<.0001' if q < 1e-4 else f'{q:.4f}'

# ---------------- Hosmer-Lemeshow (SAS doc partition) ----------------
def hl(fuzz, mode, expected):
    o = np.argsort(p, kind='stable'); ps = p[o]; ys = y[o]
    # blocks
    blocks = []; i = 0
    while i < N:
        j = i + 1
        if mode == 'anchor':
            while j < N and ps[j] <= ps[i] + fuzz: j += 1
        elif mode == 'chain':
            while j < N and ps[j] <= ps[j-1] + fuzz: j += 1
        elif mode == 'round':
            r = round(ps[i] / fuzz)
            while j < N and round(ps[j] / fuzz) == r: j += 1
        blocks.append((i, j)); i = j
    M = math.floor(0.1 * N + 0.5)
    groups = [[blocks[0]]]; c = blocks[0][1] - blocks[0][0]
    for (a, b) in blocks[1:]:
        nb = b - a
        if c < M and c + math.floor(nb / 2) <= M:
            groups[-1].append((a, b)); c += nb
        else:
            groups.append([(a, b)]); c = nb
    if sum(b - a for a, b in groups[-1]) <= math.floor(0.05 * N):
        last = groups.pop(); groups[-1] += last
    pe = ps.copy()
    for a, b in blocks:
        if expected == 'min': pe[a:b] = ps[a]
        elif expected == 'mean': pe[a:b] = ps[a:b].mean()
        elif expected == 'round': pe[a:b] = round(ps[a] / fuzz) * fuzz
    rows = []; chi = 0.0
    for g, bl in enumerate(groups, 1):
        a, b = bl[0][0], bl[-1][1]
        tot = b - a; eo = int(ys[a:b].sum()); ee = pe[a:b].sum()
        rows.append((g, tot, eo, f'{ee:.2f}', tot - eo, f'{tot - ee:.2f}'))
        chi += (eo - ee) ** 2 / ee + ((tot - eo) - (tot - ee)) ** 2 / (tot - ee)
    return rows, chi, len(groups)

ref_hl = pl.read_csv(R + 'printed_hl_partition.csv', infer_schema=False)
ref_rows = [tuple(r) for r in ref_hl.iter_rows()]
for fz, mode, ex in [(0, 'anchor', 'own'), (1e-6, 'anchor', 'own'), (1e-6, 'anchor', 'min'), (1e-6, 'chain', 'min'),
                     (1e-6, 'round', 'round'), (1e-6, 'round', 'own'), (1e-7, 'anchor', 'min'), (1e-5, 'anchor', 'min'), (1e-8, 'anchor', 'min')]:
    rows, chi, G = hl(fz, mode, ex)
    srows = [tuple(str(x) for x in r) for r in rows]
    tot_ok = [r[1] for r in srows] == [r[1] for r in ref_rows]
    print(f'HL fuzz={fz} {mode:6s} exp={ex:5s} G={G} totals_equal={tot_ok} rows_equal={srows == ref_rows} chi={chi:.4f}',
          'totals' if tot_ok else [r[1] for r in srows])
rows, chi, G = hl(1e-6, 'anchor', 'min')
wr('printed_hl_partition.csv', ['Group','Total','EventsObserved','EventsExpected','NoneventsObserved','NoneventsExpected'], rows)
wr('printed_hosmer_lemeshow.csv', ['ChiSq','DF','ProbChiSq','NGroups'], [(f'{chi:.4f}', G - 2, pv(chi2.sf(chi, G - 2)), G)])
print('HL chi', chi, 'p', chi2.sf(chi, G - 2))

# ---------------- ctable with bias-adjusted probabilities ----------------
X = np.column_stack([np.ones(N)] + [t[c].to_numpy().astype(float) for c in MODEL_FINAL])
w = p * (1 - p)
V = np.linalg.inv(X.T @ (X * w[:, None]))
q = np.einsum('ij,jk,ik->i', X, V, X)
h = w * q
eta = np.log(p / (1 - p))
ps_ = 1 / (1 + np.exp(-(eta - (y - p) * q / (1 - h))))
lo = math.floor(p.min() / 0.02 + 1e-9) * 0.02; hi = math.ceil(p.max() / 0.02 - 1e-9) * 0.02
lo2 = math.floor(ps_.min() / 0.02) * 0.02; hi2 = math.ceil(ps_.max() / 0.02) * 0.02
print('grid pd', lo, hi, 'grid pstar', lo2, hi2, 'pstar min/max', ps_.min(), ps_.max())
n1 = int(y.sum()); n0 = N - n1
def pct(a, b): return '' if b == 0 else f'{100 * a / b:.1f}'
def ctab(score, ge=True):
    out = []
    k = 0
    while True:
        z = round(lo + 0.02 * k, 10)
        if z > hi + 1e-9: break
        ev = score >= z if ge else score > z
        CE = int(np.sum(ev & (y == 1))); IE = int(np.sum(ev & (y == 0)))
        IN = n1 - CE; CN = n0 - IE
        out.append((f'{z:.3f}', CE, CN, IE, IN, pct(CE + CN, N), pct(CE, n1), pct(CN, n0), pct(IE, CE + IE), pct(IN, CN + IN), pct(CE, CE + IE), pct(CN, CN + IN)))
        k += 1
    return out
ref_ct = [tuple(r) for r in pl.read_csv(R + 'printed_classification.csv', infer_schema=False).fill_null('').iter_rows()]
for lab, sc, ge in [('pstar>=', ps_, True), ('pstar>', ps_, False), ('pd>=', p, True)]:
    ct = ctab(sc, ge); s = [tuple(str(x) for x in r) for r in ct]
    nd = sum(a != b for a, b in zip(s, ref_ct))
    print('ctable', lab, 'rows', len(s), len(ref_ct), 'rows differing', nd)
    if lab == 'pstar>=':
        wr('printed_classification.csv', ['ProbLevel','CorrectEvents','CorrectNonevents','IncorrectEvents','IncorrectNonevents','Correct','Sensitivity','Specificity','FalsePositive','FalseNegative','PPV','NPV'], ct)
        for a, b in zip(s, ref_ct):
            if a != b: print('   mine', a, '\n   ref ', b)
# grid-point proximity
for z in np.arange(0, 0.9, 0.02):
    m = np.min(np.abs(ps_ - z))
    if m < 1e-7: print('pstar near grid', z, m)

# ---------------- ROC association ----------------
def roc(yv, s, label, fuzz=1e-8):
    e = np.sort(s[yv == 1]); ne = np.sort(s[yv == 0]); n1, n0 = len(e), len(ne)
    below = np.searchsorted(ne, e - fuzz, side='left')         # nonevents < e - fuzz
    upto = np.searchsorted(ne, e + fuzz, side='right')          # nonevents <= e + fuzz
    tie_e = upto - below
    C = below.sum(); T = tie_e.sum(); P = n1 * n0; D = P - C - T
    # per nonevent
    above = n1 - np.searchsorted(e, ne + fuzz, side='right')
    tie_n = np.searchsorted(e, ne + fuzz, side='right') - np.searchsorted(e, ne - fuzz, side='left')
    V10 = (below + 0.5 * tie_e) / n0; V01 = (above + 0.5 * tie_n) / n1
    A = (C + T / 2) / P
    se = math.sqrt(V10.var(ddof=1) / n1 + V01.var(ddof=1) / n0)
    z = 1.959963984540054; NN = n1 + n0
    def d8(x):
        sig = 2 - math.floor(math.log10(abs(x)))
        return f'{x:.{min(8 - len(str(int(abs(x)))) - 1, max(4, sig))}f}'
    row = (label, f'{A:.4f}', d8(se), f'{A - z*se:.4f}', f'{A + z*se:.4f}', f'{(C-D)/P:.4f}', f'{(C-D)/(C+D):.4f}', f'{(C-D)/(NN*(NN-1)/2):.4f}')
    print('ROC', label, 'C', C, 'D', D, 'T', T, 'A', A, 'se', se, 'gamma', (C-D)/(C+D))
    return row
for lab, frame, fn in [('Training Set', t, 'printed_roc_train.csv'), ('Validation Set', v, 'printed_roc_validation.csv')]:
    r = roc(frame['default_flag'].to_numpy(), frame['pd_logistic'].to_numpy(), lab)
    ref = tuple(pl.read_csv(R + fn, infer_schema=False).row(0))
    print('   ', r, '\n   ', ref, r == ref)
    wr(fn, ['ROCModel','Area','StdErr','LowerArea','UpperArea','SomersD','Gamma','TauA'], [r])
