import glob, csv, re, sys, collections
sys.path.insert(0, '/Users/cristophersalvi/GitHub/sas-migration/judge')
from compare import sas_best12, FORMATTED, MODEL_STAT_FILES
def best12(x):
    if x != 0 and abs(x) < 1e-5:
        neg = x < 0
        m = f"{abs(x):.{12}e}"  # get exponent
        exp = int(m.split('e')[1])
        for _ in range(2):
            es = f"E{exp}"
            w = 12 - len(es) - (1 if neg else 0)
            mant = abs(x) / 10**exp
            s = f"{mant:.{w-2}f}"
            if s.startswith("10"):
                exp += 1; continue
            break
        s = s.rstrip('0').rstrip('.')
        return ('-' if neg else '') + s + es
    return sas_best12(x)
num = re.compile(r'^-?(\d+\.?\d*|\.\d+)(E-?\d+)?$')
bad = collections.Counter(); ecount = collections.Counter(); n = 0
for f in sorted(glob.glob('/Users/cristophersalvi/GitHub/sas-migration/judge/reference/**/*.csv', recursive=True)):
    name = f.split('/')[-1]
    if name in MODEL_STAT_FILES: continue
    rows = list(csv.reader(open(f)))
    for r in rows[1:]:
        for h, v in zip(rows[0], r):
            if h in FORMATTED.get(name, set()) or not num.match(v): continue
            n += 1
            if 'E' in v: ecount[f.split('reference/')[1]] += 1
            if best12(float(v)) != v:
                bad[(name, h)] += 1
                if bad[(name,h)] < 3: print('MISMATCH', f.split('reference/')[1], h, v, best12(float(v)))
print('cells', n, 'bad', sum(bad.values()), dict(bad))
print('E cells', dict(ecount))
