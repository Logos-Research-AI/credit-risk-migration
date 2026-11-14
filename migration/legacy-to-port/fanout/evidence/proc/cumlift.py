import polars as pl
from decimal import Decimal, ROUND_HALF_UP
def best8(x):
    # BEST8. for 0<x<1: plain with up to 8 chars
    s = f"{x:.6f}"  # '0.' + 6 digits = 8 chars
    return float(s)
def f82(x): return str(Decimal(repr(x)).quantize(Decimal('0.01'), ROUND_HALF_UP))
for d in ['reference', 'reference/scenarios/edge_metrics_a', 'reference/scenarios/edge_metrics_b', 'reference/scenarios/edge_metrics_c']:
    ref = pl.read_csv(f'/Users/cristophersalvi/GitHub/sas-migration/judge/{d}/printed_cumulative_lift.csv', infer_schema=False)
    da = ref.select(pl.col('total_count').cast(pl.Float64), pl.col('defaults').cast(pl.Float64))
    N, D = da['total_count'].sum(), da['defaults'].sum()
    rate = D / N
    cd = da['defaults'].cum_sum(); cc = da['total_count'].cum_sum()
    ex = [(a/b)/rate for a, b in zip(cd, cc)]
    b8 = [(a/b)/best8(rate) for a, b in zip(cd, cc)]
    r = ref['cum_lift'].to_list()
    print(d, 'rate', rate, 'best8', best8(rate), 'exact ok', [f82(x) for x in ex] == r, 'best8 ok', [f82(x) for x in b8] == r)
    print('   min margin to .005 boundary exact', min(abs((x*100) % 1 - 0.5) for x in ex))
