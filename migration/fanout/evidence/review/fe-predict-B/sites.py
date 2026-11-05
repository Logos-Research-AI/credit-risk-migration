import csv,re,sys,collections
def rows(p):
    with open(p) as f:
        return list(csv.DictReader(f,delimiter='\t',quoting=csv.QUOTE_NONE))
b=rows('migration/fanout/review-batch.fe-predict.tsv')
sweep=rows('migration/gap-sweep.tsv')
inv=rows('migration/inventory.tsv')
def sites(r):
    m=re.search(r'sites\s+(S[\dS,\s-]+)$',r['evidence'].strip())
    if not m: return []
    return re.findall(r'S\d+',m.group(1))
cov=collections.defaultdict(list)
for i,r in enumerate(b,2):
    for s in sites(r): cov[s].append(i)
invcov=collections.defaultdict(list)
for r in inv:
    for s in sites(r): invcov[s].append((r['file'],r['symbol'][:40]))
for s in sweep:
    if s['file'] in ('predict.sas','feature_engineering.sas'):
        print(s['site_id'],s['file'][:4],s['line'],s['category'],s['symbol'][:30],'| batch',cov.get(s['site_id']),'| inv',len(invcov.get(s['site_id'],[])))
# sites cited from batch rows belonging to other file
sw={s['site_id']:s for s in sweep}
for i,r in enumerate(b,2):
    for s in sites(r):
        if s not in sw: print('UNKNOWN SITE',i,s)
        elif sw[s]['file']!=r['file']: print('WRONG FILE',i,s)
print('----')
bkeys={(r['file'],r['symbol'],r['source_construct']) for r in b}
for r in inv:
    if r['file'] in ('predict.sas','feature_engineering.sas') and (r['file'],r['symbol'],r['source_construct']) not in bkeys:
        print('NOT IN BATCH:',r['file'],'|',r['symbol'],'|',r['source_construct'][:60],'|',sites(r))
invkeys={(r['file'],r['symbol'],r['source_construct']):r for r in inv}
for r in b:
    k=(r['file'],r['symbol'],r['source_construct'])
    if k not in invkeys: print('BATCH NOT IN INV',k)
    elif invkeys[k]!=r: print('DIFFERS',k)
