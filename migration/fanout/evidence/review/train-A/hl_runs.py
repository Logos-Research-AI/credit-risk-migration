import glob, math, os, numpy as np, polars as pl
def hl(p, y, fuzz):
    o = np.argsort(p, kind='stable'); ps = p[o]; ys = y[o]; N = len(p)
    blocks = []; i = 0
    while i < N:
        j = i + 1
        while j < N and ps[j] <= ps[i] + fuzz: j += 1
        blocks.append((i, j)); i = j
    M = math.floor(0.1 * N + 0.5); groups = [[blocks[0]]]; c = blocks[0][1] - blocks[0][0]
    for a, b in blocks[1:]:
        nb = b - a
        if c < M and c + nb // 2 <= M: groups[-1].append((a, b)); c += nb
        else: groups.append([(a, b)]); c = nb
    if groups[-1][-1][1] - groups[-1][0][0] <= math.floor(0.05 * N):
        last = groups.pop(); groups[-1] += last
    pe = ps.copy()
    for a, b in blocks: pe[a:b] = ps[a]
    rows = []; chi = 0
    for g, bl in enumerate(groups, 1):
        a, b = bl[0][0], bl[-1][1]; tot = b - a; eo = int(ys[a:b].sum()); ee = pe[a:b].sum()
        rows.append((str(g), str(tot), str(eo), f'{ee:.2f}', str(tot - eo), f'{tot-ee:.2f}'))
        chi += (eo-ee)**2/ee + ((tot-eo)-(tot-ee))**2/(tot-ee)
    return rows, chi
for d in sorted(glob.glob('runs/*/printed_hl_partition.csv')):
    run = os.path.dirname(d)
    r = pl.read_csv(f'{run}/risk_scores_train.csv', infer_schema_length=None)
    ref = [tuple(x) for x in pl.read_csv(d, infer_schema=False).iter_rows()]
    hc = pl.read_csv(f'{run}/printed_hosmer_lemeshow.csv', infer_schema=False)['ChiSq'][0]
    rows, chi = hl(r['pd_logistic'].to_numpy(), r['default_flag'].to_numpy().astype(float), 1e-6)
    print(f'{run:45s} rows_equal={rows == ref} chi {chi:.4f} ref {hc}')
