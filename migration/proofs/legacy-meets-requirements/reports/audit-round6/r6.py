#!/usr/bin/env python3
"""Round 6 audit, points 1-3. Usage: r6.py <subagent-transcript.jsonl>
Reads raw Logos tool results from the transcript; compares with snapshot-round5.json."""
import json,sys,hashlib,re,difflib,collections
SNAP='/Users/cristophersalvi/GitHub/credit-risk-migration/migration/proofs/legacy-meets-requirements/reports/snapshot-round5.json'
T=sys.argv[1]
THE34=['thm:sas_Q%d'%k for k in range(1,28) if k!=17]+['thm:score_chains_agree','lem:sasLinks_witness','lem:sas_links_sat','lem:sas_split_sat','lem:sas_Q27_clause1','lem:sas_feature_rows','lem:sas_features_some','lem:sas_test_feature_rows']
assert len(THE34)==34
uses={}; items={}; status=None; proofs={}; chunks=collections.defaultdict(dict); tot={}; used={}; errs=[]; log=[]
for line in open(T):
    try: e=json.loads(line)
    except: continue
    c=e.get('message',{}).get('content')
    if not isinstance(c,list): continue
    for b in c:
        if b.get('type')=='tool_use': uses[b['id']]=(b['name'].split('__')[-1],b['input'])
        elif b.get('type')=='tool_result':
            n,i=uses.get(b['tool_use_id'],('?',{}))
            cc=b.get('content')
            txt=cc if isinstance(cc,str) else ''.join(x.get('text','') for x in cc if isinstance(x,dict))
            try: j=json.loads(txt)
            except: continue
            r=j.get('result') if isinstance(j,dict) else None
            log.append((n,json.dumps({k:v for k,v in i.items() if k!='blueprint_id'})[:80],len(txt)))
            if n=='get_status': status=r
            elif n=='get_items' and isinstance(r,list):
                for it in r:
                    if 'error' in it: errs.append((i.get('item_ids'),it.get('error'))); continue
                    if 'statement_lean' in it: items[it['id']]=it
                    if it.get('proof_lean'): proofs[it['id']]=it['proof_lean']
                    if 'proof_lean' in it and it['proof_lean'] is None: proofs.setdefault(it['id'],None)
            elif n=='read_scratch' and isinstance(r,dict) and r.get('success'):
                chunks[r['item_id']][(r['start_line'],r['end_line'])]=r['content']; tot[r['item_id']]=r['total_lines']
            elif n=='used_decls' and isinstance(r,dict): used[i['item_id']]='\n'.join(r.get('used_decls',[])) if r.get('success') else 'FAILED '+json.dumps(r)[:300]
if '-v' in sys.argv:
    for l in log: print(l)
snap=json.load(open(SNAP)); sn={i['id']:i for i in snap['items']}; full=snap['statement_lean']
print('status:',status); print('errors:',errs)
print('items fetched:',len(items),'snapshot:',len(sn),'missing:',sorted(set(sn)-set(items)),'extra:',sorted(set(items)-set(sn)))
def h(s): return hashlib.sha256(s.encode()).hexdigest()
print('\n== Point 1: the 34')
for k in THE34:
    it=items.get(k)
    if not it: print(k,'NOT FETCHED'); continue
    s=it['statement_lean'] or ''
    same=h(s)==sn[k]['statement_sha256']; nb=len(s.encode())
    print('%-28s %-14s sha %s  bytes %d/%d%s'%(k,it['state'],'same' if same else 'DIFF',nb,sn[k]['statement_bytes'],'' if same else '  <<<'))
    if not same and k in full:
        for l in difflib.unified_diff(full[k].split('\n'),s.split('\n'),lineterm='',n=0): print('     ',l)
print('\n== Point 2: SasLinks, sasPipeline, units')
k='def:SasLinks'; s=items[k]['statement_lean']
print(k,items[k]['state'],'sha same' if h(s)==sn[k]['statement_sha256'] else 'sha DIFF','bytes %d/%d'%(len(s.encode()),sn[k]['statement_bytes']))
for l in difflib.unified_diff(full[k].split('\n'),s.split('\n'),lineterm='',n=0): print('     ',l)
bad=[]
for k in sn:
    if k.startswith('def:') and k!='def:SasLinks':
        it=items.get(k)
        if not it or h(it['statement_lean'] or '')!=sn[k]['statement_sha256'] or it['state']!=sn[k]['state']: bad.append(k)
print('other defs (incl. def:sasPipeline, all units): %d checked, changed or missing: %s'%(sum(1 for k in sn if k.startswith('def:'))-1,bad))
print('\n== Point 3: proved items outside the 34')
out=[k for k in items if not k.startswith('def:') and k not in THE34]
PAT=re.compile(r'TrainOK|TestOK|InputOK|decimal12|decimal32|CreditRisk\.[\w.]+|\bFitted\b|SasLinks|sasPipeline')
def strip(t):
    o=[];i=0;d=0
    while i<len(t):
        if t.startswith('/-',i): d+=1;i+=2;continue
        if d and t.startswith('-/',i): d-=1;i+=2;continue
        if d: i+=1;continue
        if t.startswith('--',i):
            while i<len(t) and t[i]!='\n': i+=1
            continue
        o.append(t[i]);i+=1
    return ''.join(o)
for k in out:
    it=items[k]; s=it['statement_lean'] or ''
    same=h(s)==sn[k]['statement_sha256'] if k in sn else None
    if proofs.get(k): p=proofs[k]; src='accepted proof'
    elif k in chunks:
        ls={}
        for (a,b) in sorted(chunks[k]):
            for n_,l in zip(range(a,b+1),chunks[k][(a,b)].split('\n')): ls[n_]=l
        p='\n'.join(ls[n_] for n_ in sorted(ls)); src='stored draft %d/%d lines'%(len(ls),tot[k])
    else: p=None; src='no proof text'
    print(k,it['state'],'| statement sha','same' if same else 'DIFF','| stmt deps',it.get('statement_dependencies'),'| proof deps',it.get('proof_dependencies'))
    print('   statement names:',sorted(set(PAT.findall(strip(s)))))
    print('   proof (%s) names:'%src,sorted(set(PAT.findall(strip(p)))) if p else None)
    u=used.get(k,'(no used_decls)')
    print('   used_decls names:',sorted(set(PAT.findall(u))))
