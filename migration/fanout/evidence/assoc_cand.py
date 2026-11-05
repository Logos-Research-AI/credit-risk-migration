import sys, numpy as np, polars as pl
src, out = sys.argv[1], sys.argv[2]
d = pl.read_csv(src, infer_schema_length=None)
y = d['default_flag'].to_numpy(); p = d['pd_logistic'].to_numpy()
ev = np.sort(p[y == 1]); ne = np.sort(p[y == 0]); N = len(ev) * len(ne)
lo = np.searchsorted(ne, ev - 1e-8, 'left'); hi = np.searchsorted(ne, ev + 1e-8, 'right')
T = int((hi - lo).sum()); C = int(lo.sum()); D = N - C - T
n = len(p); pc, pdis, pt = 100*C/N, 100*D/N, 100*T/N
sd = (C-D)/N; g = (C-D)/(C+D); ta = (C-D)/(n*(n-1)/2); c = (C+T/2)/N
def b(x): return f"{x:.{max(0, 11-len(str(int(abs(x)))))}f}".rstrip('0').rstrip('.')
rows = [("Percent Concordant", f"{pc:.1f}", b(pc), "Somers' D", f"{sd:.3f}", b(sd)),
        ("Percent Discordant", f"{pdis:.1f}", b(pdis), "Gamma", f"{g:.3f}", b(g)),
        ("Percent Tied", f"{pt:.1f}", b(pt), "Tau-a", f"{ta:.3f}", b(ta)),
        ("Pairs", str(N), str(N), "c", f"{c:.3f}", b(c))]
with open(out, 'w') as f:
    f.write("Label1,cValue1,nValue1,Label2,cValue2,nValue2\n")
    for r in rows: f.write(",".join(r) + "\n")
print("T", T, open(out).read())
