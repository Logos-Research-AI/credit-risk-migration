"""Decide what experiments X07 and X08 establish about the PROC LOGISTIC ROC tie rule (R25) and
the Association table (R28). Reads the .sas (inputs, hex binary64) and .log (SAS results) only."""
import re, struct, collections, itertools, sys
from fractions import Fraction as Fr
def h2f(h): return struct.unpack(">d", bytes.fromhex(h))[0]
def f2h(x): return struct.pack(">d", x).hex().upper()
BCD = h2f("3E46A09E667F3BCD")          # sqrt(2**-53) rounded to nearest
CONSTS = {"bcc": h2f("3E46A09E667F3BCC"), "bcd": BCD, "bce": h2f("3E46A09E667F3BCE"), "bcf": h2f("3E46A09E667F3BCF")}

def read(sas):
    G = collections.OrderedDict()
    for l in open(sas).read().splitlines():
        m = re.match(r"^(\d+) ([0-9A-F]{16}) ([01])$", l)
        if m: G.setdefault(int(m[1]), []).append((h2f(m[2]), int(m[3])))
    return G

def groups(ps, rule, tied):
    """ps: distinct values. Returns dict value -> group label."""
    lab = {}
    if rule == "top":       # from the largest down, anchored at the group's largest
        s = sorted(ps, reverse=True); a = None; k = 0
        for p in s:
            if a is None or not tied(a - p): a = p; k += 1
            lab[p] = k
    elif rule == "chain":   # joins while within tolerance of the previous value
        s = sorted(ps, reverse=True); prev = None; k = 0
        for p in s:
            if prev is None or not tied(prev - p): k += 1
            prev = p; lab[p] = k
    elif rule == "bottom":  # from the smallest up, anchored at the group's smallest
        s = sorted(ps); a = None; k = 0
        for p in s:
            if a is None or not tied(p - a): a = p; k -= 1
            lab[p] = k
        # labels: larger value -> more negative; flip so that larger label = smaller prob as in "top"
        lab = {p: -v for p, v in lab.items()}
        lab = {p: -v for p, v in lab.items()}
    return lab

def counts(rows, rule, tied):
    if rule == "pair":
        nc = nd = nt = 0
        for p1, y1 in rows:
            if y1 != 1: continue
            for p0, y0 in rows:
                if y0 != 0: continue
                if tied(abs(p1 - p0)): nt += 1
                elif p1 > p0: nc += 1
                else: nd += 1
        return nc, nd, nt
    lab = groups(set(p for p, _ in rows), rule, tied)
    # group order: compare by a representative (groups are intervals)
    rep = {}
    for p, k in lab.items(): rep[k] = max(rep.get(k, p), p)
    e = collections.Counter(); n = collections.Counter()
    for p, y in rows: (e if y == 1 else n)[rep[lab[p]]] += 1
    nc = nd = nt = 0
    for a, ca in e.items():
        for b, cb in n.items():
            if a == b: nt += ca * cb
            elif a > b: nc += ca * cb
            else: nd += ca * cb
    return nc, nd, nt

AREAS = {
 "(nc+0.5*nt)/(n1*n0)": lambda nc, nd, nt, n1, n0: (nc + 0.5 * nt) / (n1 * n0),
 "(nc+nt/2)/n1/n0":     lambda nc, nd, nt, n1, n0: (nc + nt / 2) / n1 / n0,
 "nc/t+0.5*(nt/t)":     lambda nc, nd, nt, n1, n0: nc / (n1 * n0) + 0.5 * (nt / (n1 * n0)),
 "0.5*(1+(nc-nd)/t)":   lambda nc, nd, nt, n1, n0: 0.5 * (1 + (nc - nd) / (n1 * n0)),
 "(nc-nd)/t/2+0.5":     lambda nc, nd, nt, n1, n0: (nc - nd) / (n1 * n0) / 2 + 0.5,
 "1-(nd+0.5*nt)/t":     lambda nc, nd, nt, n1, n0: 1 - (nd + 0.5 * nt) / (n1 * n0),
 "(2*nc+nt)/(2*t)":     lambda nc, nd, nt, n1, n0: (2 * nc + nt) / (2 * n1 * n0),
}
TIED = {
 "d<=bcc": lambda d: d <= CONSTS["bcc"], "d<=bcd": lambda d: d <= CONSTS["bcd"],
 "d<=bce (same as d<bcf)": lambda d: d <= CONSTS["bce"], "d<=bcf": lambda d: d <= CONSTS["bcf"],
 "d<=1e-8": lambda d: d <= 1e-8, "exact": lambda d: d == 0,
 "d*d<=2^-53": lambda d: d * d <= 2.0 ** -53, "d*d<2^-53": lambda d: d * d < 2.0 ** -53,
}

def roc_part():
    out = {}
    for name, sas, log, pat in (("X07", "experiments/x07_roc_ties.sas", "experiments/x07_roc_ties.log", r"X07 roc g=(\d+) Area=(\w+)"),
                                ("X08", "experiments/x08_roceps_boundary.sas", "experiments/x08_roceps_boundary.log", r"X08 roc g=(\d+) Area=([\d.]+)")):
        G = read(sas); A = dict(re.findall(pat, open(log).read()))
        print(f"== {name}: {len(G)} cases")
        for rule in ("top", "chain", "bottom", "pair"):
            for tn, tf in TIED.items():
                res = collections.Counter(); bad = {}
                for g, rows in G.items():
                    n1 = sum(y for _, y in rows); n0 = len(rows) - n1
                    nc, nd, nt = counts(rows, rule, tf)
                    exact = Fr(2 * nc + nt, 2 * n1 * n0)
                    sasv = A[str(g)]
                    if name == "X07":
                        ok = Fr(h2f(sasv)) == Fr(float(exact))
                        for an, af in AREAS.items():
                            if f2h(af(nc, nd, nt, n1, n0)) == sasv: res[an] += 1
                    else:
                        ok = abs(float(exact) - float(sasv)) < 5e-5
                    if not ok: bad[g] = 1
                line = f"  rule={rule:6s} tied: {tn:24s} counts wrong on {len(bad):3d} cases {sorted(bad)[:12]}"
                if name == "X07" and not bad: line += "  | bit-exact area: " + ", ".join(f"{k}:{v}" for k, v in res.items())
                if len(bad) <= 12 or rule == "top": print(line)

def assoc_part():
    log = open("experiments/x07_roc_ties.log").read()
    for c in "1234":
        rows = [(h2f(p), int(y)) for y, p in re.findall(rf"X07 C{c} row i=\d+ y=(\d) p=(\w+)", log)]
        a = {}
        for l1, v1, l2, v2 in re.findall(rf"X07 C{c} assoc Label1=(.*?) nValue1=(\w+) nValue1=\S+ Label2=(.*?) nValue2=(\w+)", log):
            a[l1.strip()] = v1; a[l2.strip()] = v2
        n1 = sum(y for _, y in rows); n0 = len(rows) - n1; t = n1 * n0; N = len(rows)
        ps = sorted(set(p for p, _ in rows)); gaps = sorted(b - a_ for a_, b in zip(ps, ps[1:]))
        print(f"== C{c}: N={N} pairs={t} (SAS {h2f(a['Pairs'])})  distinct p={len(ps)}  gaps<5e-8: {sum(g < 5e-8 for g in gaps)}, smallest {gaps[0]:.3e}, gaps in (bcd/2, 2bcd): {sum(BCD/2 < g < 2*BCD for g in gaps)}")
        for rule in ("top", "chain", "bottom", "pair"):
            for tn in ("d<=bcd", "d<=bce (same as d<bcf)", "exact", "d<=1e-8"):
                nc, nd, nt = counts(rows, rule, TIED[tn])
                forms = {
                  "Percent Concordant": {"100*nc/t": 100 * nc / t, "100*(nc/t)": 100 * (nc / t), "nc/t*100": nc / t * 100},
                  "Percent Discordant": {"100*nd/t": 100 * nd / t, "100*(nd/t)": 100 * (nd / t)},
                  "Percent Tied": {"100*nt/t": 100 * nt / t, "100*(nt/t)": 100 * (nt / t), "100*(t-nc-nd)/t": 100 * (t - nc - nd) / t},
                  "c": {"(nc+0.5*nt)/t": (nc + 0.5 * nt) / t, "nc/t+0.5*(nt/t)": nc / t + 0.5 * (nt / t), "0.5*(1+(nc-nd)/t)": 0.5 * (1 + (nc - nd) / t)},
                  "Somers' D": {"nc/t-nd/t": nc / t - nd / t, "(nc-nd)/t": (nc - nd) / t, "2*c-1": 2 * ((nc + 0.5 * nt) / t) - 1},
                  "Gamma": {"(nc-nd)/(nc+nd)": (nc - nd) / (nc + nd)},
                  "Tau-a": {"(nc-nd)/(0.5*N*(N-1))": (nc - nd) / (0.5 * N * (N - 1)), "2*(nc-nd)/(N*(N-1))": 2 * (nc - nd) / (N * (N - 1))},
                }
                hit = {k: [fn for fn, v in fs.items() if f2h(v) == a[k]] for k, fs in forms.items()}
                close = abs(100 * nc / t - h2f(a["Percent Concordant"])) < 1e-9 and abs(100 * nt / t - h2f(a["Percent Tied"])) < 1e-9
                print(f"  rule={rule:6s} {tn:24s} nc={nc} nd={nd} nt={nt} counts {'MATCH' if close else 'differ'}" + ("  " + "; ".join(f"{k}: {'|'.join(v) or 'NONE'}" for k, v in hit.items()) if close else ""))

if __name__ == "__main__":
    roc_part(); assoc_part()
