"""Python with a correctly rounded exp, folded in the same chunks: does it equal Lean's chunk digests (all chunks, both sweeps)?"""
import sys, json
sys.argv = [sys.argv[0]] + sys.argv[1:]
exec(open("diffeval/work/fz5_s10_crall.py").read().split("diff = []")[0])
def fold(base, K):
    a1 = a2 = cnt = 0
    for s in range(base, base + K):
        c = g.build(s)
        if c["icpt"] is None and c["fin"] and not c["coefs"]: continue
        res = step_cr(c); df = g.to_df(c)
        a1 = g.mx(a1, g.cmp.digest(g.tok_in(c, df))); a2 = g.mx(a2, g.cmp.digest(g.cmp.tokens(g.cmp.canon_frame(res)))); cnt += 1
    return [a1, a2, cnt]
which = sys.argv[1]
if which == "s1":
    lean = json.load(open("diffeval/work/fz5_s10.cout.json")); base = 0
else:
    lean = [[8371559740272217644,1476048282370936613,98],[14053015303075362106,2501559983582828880,98],[16178440855070141502,13142247442407255808,98],[8554846578472822006,12925791939388223859,100],[8783363079674413345,12269752466206831588,98],[2002210378547937730,9773067381840874558,98],[8633041202261774285,13196886195539788192,99],[3883858325174951249,10613130631024865531,98],[15138012996605537869,8946113006810729267,99]]; base = 50000
bad = [i for i, L in enumerate(lean) if fold(base + 100 * i, 100) != L]
print(which, "chunks", len(lean), "chunks where Lean != Python-with-correctly-rounded-exp:", bad)
