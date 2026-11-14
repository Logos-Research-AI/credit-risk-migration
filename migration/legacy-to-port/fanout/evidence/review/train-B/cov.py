import re,csv,sys
def sites(path,fname='train.sas'):
    out={}
    for i,l in enumerate(open(path)):
        f=l.rstrip('\n').split('\t')
        if i==0 or len(f)<6 or f[0]!=fname: continue
        m=re.search(r'sites (S[\d,S ]+)\s*$',f[5])
        s=set(re.findall(r'S\d+',m.group(1))) if m else set()
        out[(f[1],f[2])]=s
    return out
b=sites('migration/fanout/review-batch.train.tsv')
b1=sites('migration/inventory.batch1.tsv')
inv=sites('migration/inventory.tsv')
allb=set().union(*b.values()); allb1=set().union(*b1.values())
sweep=[l.split('\t')[0] for l in open('migration/gap-sweep.tsv') if '\ttrain.sas\t' in l]
print('missing from batch+batch1:', [s for s in sweep if s not in allb|allb1])
print('batch1 sites:', sorted(allb1))
from collections import Counter
c=Counter(s for v in b.values() for s in v)
print('dups in batch:', {k:v for k,v in c.items() if v>1})
print('in both batch and batch1:', sorted(allb & allb1))
print('inv rows', len(inv))
