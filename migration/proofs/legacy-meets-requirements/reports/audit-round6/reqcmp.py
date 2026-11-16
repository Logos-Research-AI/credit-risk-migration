#!/usr/bin/env python3
"""Compare CreditRisk declarations seen from the SAS blueprint (old) and the requirements blueprint (now).
Usage: reqcmp.py <subagent-transcript.jsonl>"""
import json,sys,difflib
SAS='3f5df696-7c80-45cc-809f-b2881714663d'; REQ='006ff04c-d34c-4a9c-b230-ccd725b1be6f'
uses={}; got={SAS:{},REQ:{}}; fail=[]; other=[]
for line in open(sys.argv[1]):
    try: e=json.loads(line)
    except: continue
    c=e.get('message',{}).get('content')
    if not isinstance(c,list): continue
    for b in c:
        if b.get('type')=='tool_use': uses[b['id']]=(b['name'].split('__')[-1],b['input'])
        elif b.get('type')=='tool_result':
            nm,i=uses.get(b['tool_use_id'],('?',{}))
            cc=b.get('content')
            txt=cc if isinstance(cc,str) else ''.join(x.get('text','') for x in cc if isinstance(x,dict))
            try: j=json.loads(txt)
            except: continue
            r=j.get('result')
            if nm=='check_decl':
                if isinstance(r,dict) and r.get('success'): got[i['blueprint_id']][i['decl']]=r['type']
                else: fail.append((i['blueprint_id'][:8],i['decl'],txt[:160]))
            elif nm in('grep','get_status','get_items'): other.append((nm,i.get('blueprint_id','')[:8],r))
print('old',len(got[SAS]),'now',len(got[REQ]))
for f in fail:
    if f[1] not in got[SAS if f[0]==SAS[:8] else REQ]: print('FAILED',f)
ident=0
for d in sorted(set(got[SAS])|set(got[REQ])):
    a=got[SAS].get(d); b=got[REQ].get(d)
    if a is None or b is None: print(d,'ONLY','now' if a is None else 'old'); continue
    if a==b: ident+=1
    else:
        print(d,'DIFFERS')
        for l in difflib.unified_diff(a.split('\n'),b.split('\n'),lineterm='',n=1): print('   ',l)
print('identical:',ident)
for nm,bp,r in other:
    if nm=='get_items':
        for it in r:
            x=dict(it)
            if 'proof_lean' in x and x['proof_lean']:
                p=x['proof_lean']; x['proof_lean']='<%d chars; sorry:%s>'%(len(p),'sorry' in p)
                open('witness_proof.txt.tmp','w').write(p) if False else None
                import re
                print('--- witness defs/rows in proof:')
                for l in p.split('\n'):
                    if re.search(r'noncomputable def t[AB]\d|refine ⟨\[|^-- (training|test)|length',l): print('   ',l)
            print(nm,bp,json.dumps(x,ensure_ascii=False)[:1500])
    else: print(nm,bp,json.dumps(r,ensure_ascii=False)[:900])
