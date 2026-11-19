import json
from collections import Counter
cs=json.load(open('diffeval/work/fz5_ctable.cases.json'))
def cat(c):
    if c['case']['final'] is None: return 'none'
    return 'made' if c['expected'] else 'some'
def data(c):
    s=c['input']
    m=s.rfind('(fun x => Float.log (1.0 + x)) ')
    return s[m+31:] if m>=0 else s[s.rfind('(fun x => x) ')+13:]
sel=[];cnt=Counter();lim={'none':20,'some':45,'made':48};wide=0
for c in sorted(cs,key=lambda c:len(data(c))):
    k=cat(c)
    if cnt[k]>=lim[k] or len(data(c))>900: continue
    if c['rows']>3:
        if wide>=3: continue
        wide+=1
    cnt[k]+=1; sel.append(c)
sel.sort(key=lambda c:c['seed'])
json.dump(sel,open('diffeval/work/fz5_ctable.sel.json','w'),default=lambda x:None)
print(cnt,len(sel),sum(len(data(c)) for c in sel),sum(c['rows'] for c in sel))
