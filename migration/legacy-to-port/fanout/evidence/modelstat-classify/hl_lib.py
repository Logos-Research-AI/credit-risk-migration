import numpy as np, math

def anchored_blocks(v, eps, rel=False):
    """v sorted ascending. Block = run starting at v[i] containing all values <= v[i] + eps."""
    out = []; i = 0; n = len(v)
    while i < n:
        lim = v[i] * (1 + eps) if rel else v[i] + eps
        j = int(np.searchsorted(v, lim, side="right"))
        out.append(j - i); i = j
    return out

def doc(bs, N, G=10):
    M = math.floor(N / G + 0.5); groups = []; c = 0
    for nj in bs:
        if c == 0 or (c < M and c + math.floor(0.5 * nj) <= M): c += nj
        else: groups.append(c); c = nj
    groups.append(c)
    if len(groups) > 1 and groups[-1] <= math.floor(0.05 * N):
        x = groups.pop(); groups[-1] += x
    return groups

def lt(bs, N, G=10):
    M = math.floor(N / G + 0.5); groups = []; c = 0
    for nj in bs:
        if c == 0 or c < M: c += nj
        else: groups.append(c); c = nj
    groups.append(c); return groups
