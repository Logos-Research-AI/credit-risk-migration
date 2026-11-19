"""Check of the plan of the Lean draw of def:fe_run_06_split (update 2026-11-19, T0): a plain-Python
mirror of CPython's MT19937 seeding (init_by_array), twist, tempering, _randbelow_with_getrandbits and
the pool branch of Random.sample, compared with random.Random(42). Harness only."""
import random
M32 = 2**32
def init_genrand(s):
    mt = [s % M32]
    for i in range(623):
        p = mt[-1]; mt.append((1812433253 * (p ^ (p >> 30)) + (i + 1)) % M32)
    return mt
def init_by_array(key):
    mt = init_genrand(19650218); i, j = 1, 0; kl = len(key)
    for _ in range(max(624, kl)):
        p = mt[i - 1]; mt[i] = ((mt[i] ^ ((p ^ (p >> 30)) * 1664525 % M32)) + key[j] + j) % M32
        i += 1; j += 1
        if i >= 624: mt[0] = mt[623]; i = 1
        if j >= kl: j = 0
    for _ in range(623):
        p = mt[i - 1]; mt[i] = ((mt[i] ^ ((p ^ (p >> 30)) * 1566083941 % M32)) + M32 - i) % M32
        i += 1
        if i >= 624: mt[0] = mt[623]; i = 1
    mt[0] = 2147483648
    return mt
def twist(m):
    m = list(m)
    for kk in range(624):
        y = (m[kk] & 2147483648) | (m[(kk + 1) % 624] & 2147483647)
        m[kk] = m[(kk + 397) % 624] ^ (y >> 1) ^ (2567483615 if y % 2 else 0)
    return m
def nxt(st):
    mt, i = st
    if i >= 624: mt, i = twist(mt), 0
    y = mt[i]; y ^= y >> 11; y ^= (y << 7) & 2636928640; y ^= (y << 15) & 4022730752; y ^= y >> 18
    return y, (mt, i + 1)
def randbelow(n, st):
    while True:
        r, st = nxt(st); v = r >> (32 - n.bit_length())
        if v < n: return v, st
def sample(pool, k, st):
    pool = list(pool); n = len(pool); out = []
    for i in range(k):
        j, st = randbelow(n - i, st); out.append(pool[j]); pool[j] = pool[n - i - 1]
    return out
if __name__ == "__main__":
    st = (init_by_array([42]), 624)
    print(nxt(st)[0], random.Random(42).getrandbits(32))
    bad = 0
    for n in range(1, 400):
        for k in {0, 1, n // 2, min(n, (7 * n + 9) // 10), n}:
            if sample(range(n), k, (init_by_array([42]), 624)) != random.Random(42).sample(range(n), k): bad += 1
    print("bad", bad)
