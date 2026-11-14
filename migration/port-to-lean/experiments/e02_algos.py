"""Reference re-implementations of the summation orders identified in E02 (shared by later experiments)."""
def seq(xs, init=None):
    it = iter(xs)
    acc = next(it) if init is None else init
    for v in it: acc = acc + v
    return acc
def np_pairwise(a):
    n = len(a)
    if n < 8:
        res = 0.0
        for v in a: res += v
        return res
    if n <= 128:
        r = list(a[:8]); i = 8
        while i < n - (n % 8):
            for j in range(8): r[j] += a[i + j]
            i += 8
        res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]))
        while i < n:
            res += a[i]; i += 1
        return res
    n2 = n // 2; n2 -= n2 % 8
    return np_pairwise(a[:n2]) + np_pairwise(a[n2:])
def hsum16(v):
    v = list(v)
    for i in range(8): v[i] = v[i] + v[i + 8]
    for i in range(4): v[i] = v[i] + v[i + 4]
    for i in range(2): v[i] = v[i] + v[i + 2]
    return v[0] + v[1]
def block128(f):
    acc = [0.0] * 16
    for c in range(0, 128, 16):
        for j in range(16): acc[j] = acc[j] + f[c + j]
    return hsum16(acc)
def pl_pairwise(f):
    if len(f) == 128: return block128(f)
    blocks = len(f) // 128
    left = (blocks // 2) * 128
    return pl_pairwise(f[:left]) + pl_pairwise(f[left:])
def pl_sum(f):
    rem = len(f) % 128
    rest, main = f[:rem], f[rem:]
    mainsum = pl_pairwise(main) if len(main) else 0.0
    restsum = 0.0
    for v in rest: restsum = restsum + v
    return mainsum + restsum
