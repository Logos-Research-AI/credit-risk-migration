import numpy as np, polars as pl, math
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
d = pl.read_csv(f"{J}/reference/risk_scores_train.csv", infer_schema_length=0).select(
    pl.col("pd_logistic").cast(pl.Float64).alias("pd")).sort("pd")
p = d["pd"].to_numpy(); N = len(p)
REF = [10498, 10502, 10501, 10502, 10499, 10500, 10500, 10501, 10500, 10497]

def blocks_of(key):
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    return np.diff(np.r_[st, len(key)])

def r_doc(bs, G=10):
    M = math.floor(N / G + 0.5); groups = []; c = 0
    for nj in bs:
        if c == 0 or (c < M and c + math.floor(0.5 * nj) <= M):
            c += nj
        else:
            groups.append(c); c = nj
    groups.append(c)
    if groups[-1] <= math.floor(0.05 * N) and len(groups) > 1:
        groups[-2] += groups.pop()
    return groups

def r_lt(bs, G=10):
    M = math.floor(N / G + 0.5); groups = []; c = 0
    for nj in bs:
        if c == 0 or c < M: c += nj
        else: groups.append(c); c = nj
    groups.append(c); return groups

def r_cum(bs, G=10, mode="half"):
    cum = 0; groups = []; start = 0; k = 1
    for nj in bs:
        tgt = k * N / G
        if mode == "half":
            add = cum + nj / 2 <= tgt
        else:
            add = cum < tgt
        if add or cum == start:
            cum += nj
        else:
            groups.append(cum - start); start = cum; cum += nj; k += 1
    groups.append(cum - start); return groups

keys = {}
for dd in range(3, 10):
    keys[f"round{dd}"] = np.round(p, dd)
for s in range(2, 9):
    keys[f"sig{s}"] = np.array([float(f"{x:.{s-1}e}") for x in p])
for k in range(3, 9):
    for m in (1, 2, 5):
        w = m * 10.0 ** -k
        keys[f"bin{w:g}"] = np.floor(p / w)
keys["exact"] = p
hits = 0
for name, key in keys.items():
    bs = blocks_of(key)
    for rn, rule in [("doc", r_doc), ("lt", r_lt), ("cumhalf", lambda b: r_cum(b, mode="half")), ("cumlt", lambda b: r_cum(b, mode="lt"))]:
        g = rule(bs)
        if g == REF:
            print("MATCH", name, rn); hits += 1
        elif len(g) == 10 and sum(abs(a - b) for a, b in zip(g, REF)) <= 8:
            print("near", name, rn, g)
print("hits", hits)
