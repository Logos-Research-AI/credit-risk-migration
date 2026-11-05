import csv
from decimal import Decimal, ROUND_HALF_UP
def pct(x, w=8, d=2):
    for dd in range(d, -1, -1):
        s = str(Decimal(repr(x*100)).quantize(Decimal(1).scaleb(-dd), ROUND_HALF_UP)) + '%'
        if len(s) <= w - 2: return s
    return s
def fx(x, w, d):
    return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-d), ROUND_HALF_UP))
ok = bad = 0
for d in ['reference', 'reference/scenarios/edge_metrics_a', 'reference/scenarios/edge_metrics_b', 'reference/scenarios/edge_metrics_c']:
    rows = list(csv.DictReader(open(f'/Users/cristophersalvi/GitHub/sas-migration/judge/{d}/printed_cumulative_lift.csv')))
    D = sum(int(r['defaults']) for r in rows); N = sum(int(r['total_count']) for r in rows)
    cd = 0; cc = 0
    for r in rows:
        dft, n = int(r['defaults']), int(r['total_count']); cd += dft; cc += n
        rate = dft / n
        for col, val in [('default_rate', pct(rate)), ('capture_rate', pct(dft / D)), ('cum_capture_rate', pct(cd / D)),
                         ('lift', fx(rate / (D / N), 8, 2)), ('cum_lift', fx((cd / cc) / (D / N), 8, 2))]:
            if val == r[col]: ok += 1
            else: bad += 1; print('MISMATCH', d, r['decile'], col, r[col], val)
print('ok', ok, 'bad', bad)
