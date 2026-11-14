import glob, csv, re, sys
sys.path.insert(0, '/Users/cristophersalvi/GitHub/sas-migration/judge')
from compare import sas_best12
num = re.compile(r'^-?\d*\.?\d+(E-?\d+)?$')
minplain = (1, None)
for f in sorted(glob.glob('/Users/cristophersalvi/GitHub/sas-migration/judge/reference/**/*.csv', recursive=True)):
    rows = list(csv.reader(open(f)))
    for r in rows[1:]:
        for h, v in zip(rows[0], r):
            if 'E' in v and num.match(v):
                print('E:', f.split('reference/')[1], h, v, 'best12->', sas_best12(float(v)))
            elif num.match(v) and '%' not in v and float(v) != 0 and abs(float(v)) < minplain[0]:
                minplain = (abs(float(v)), (f.split('reference/')[1], h, v))
print('smallest plain nonzero', minplain)
