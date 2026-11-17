#!/usr/bin/env python3
"""Search the 37 proofs. Usage: proofs6.py <proof-fetch-transcript> <statement-fetch-transcript>"""
import json,re,sys,collections
def scan(T):
    uses={}
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
                yield n,i,(j.get('result') if isinstance(j,dict) else None)
acc={}; state={}; big={}; chunks=collections.defaultdict(dict); revs=collections.defaultdict(set); tot={}; used={}
for n,i,r in scan(sys.argv[1]):
    if n=='get_items' and isinstance(r,list):
        for it in r:
            if 'error' in it and it.get('error')=='response_too_large': big[i['item_ids'][0]]=it.get('size_bytes')
            elif it.get('proof_lean'): acc[it['id']]=it['proof_lean']; state[it['id']]=it.get('state')
    elif n=='read_scratch' and isinstance(r,dict) and r.get('success') and i.get('part')=='solution':
        chunks[r['item_id']][(r['start_line'],r['end_line'])]=r['content']; revs[r['item_id']].add(r.get('revision')); tot[r['item_id']]=r['total_lines']
    elif n=='used_decls' and isinstance(r,dict): used[i['item_id']]='\n'.join(r.get('used_decls',[])) if r.get('success') else 'FAILED'
stm={}
for n,i,r in scan(sys.argv[2]):
    if n=='get_items' and isinstance(r,list):
        for it in r:
            if 'statement_lean' in it: stm[it['id']]=it
ids=['thm:sas_Q%d'%k for k in range(1,28) if k!=17]+['thm:score_chains_agree','lem:sasLinks_witness','lem:sas_links_sat','lem:sas_split_sat','lem:sas_Q27_clause1','lem:sas_feature_rows','lem:sas_features_some','lem:sas_test_feature_rows','lem:sas_score_rows','lem:sas_features_row_total','lem:sas_test_chain_agree']
PAT=re.compile(r'\bsorry\b|\baxiom\b|native_decide|\bunsafe\b|set_option|sorryAx|implemented_by|\bextern\b|\bopaque\b|ofReduceBool|reduceBool|trustCompiler|\badmit\b|\bpartial\b|csimp|\bmacro\b|\bsyntax\b|\belab\b|run_cmd|#eval|\bnotation\b|\binstance\b|bv_decide|Lean\.Elab')
NAMES=set(k.split(':')[1] for k in stm if not k.startswith('def:'))
def strip(t):
    o=[];i=0;d=0
    while i<len(t):
        if t.startswith('/-',i): d+=1;i+=2;continue
        if d and t.startswith('-/',i): d-=1;i+=2;continue
        if d:
            if t[i]=='\n': o.append('\n')
            i+=1;continue
        if t.startswith('--',i):
            while i<len(t) and t[i]!='\n': i+=1
            continue
        o.append(t[i]);i+=1
    return ''.join(o)
norm=lambda s: re.sub(r'\s+',' ',strip(s)).strip()
rows=[]
for k in ids:
    if k in acc: text=acc[k]; method='accepted'; note=''
    elif k in chunks:
        ls={}
        for (a,b) in sorted(chunks[k]):
            for n_,l in zip(range(a,b+1),chunks[k][(a,b)].split('\n')): ls[n_]=l
        text='\n'.join(ls[n_] for n_ in sorted(ls))
        full=set(ls)==set(range(1,tot[k]+1))
        j=len(json.dumps({"result":[{"id":k,"state":"TheoremProved","proof_lean":text}]},ensure_ascii=True,separators=(',',':')))
        method='draft'; note='%d lines, complete=%s, revisions=%d, size draft/accepted %s/%s'%(tot[k],full,len(revs[k]),j,big.get(k))
    else: rows.append((k,'NO TEXT','','','','','')); continue
    code=strip(text)
    hits=sorted(set(m.group(0) for m in PAT.finditer(code)))
    hitlines=[l.strip()[:70] for l in code.split('\n') if PAT.search(l)]
    st=re.sub(r':= sorry$','',norm(stm[k]['statement_lean'])).strip(); st=re.sub(r'^open Tabular in ','',st)
    nc=norm(code)
    rest= st in nc or re.sub(r'\bhlinks\b','hLinks',st) in nc or re.sub(r'\bhLinks\b','hlinks',st) in nc
    me=k.split(':')[1]
    calls=sorted(n for n in NAMES if n!=me and re.search(r'(?<![\w.])'+re.escape(n)+r"(?![\w.'])",code))
    decl=sorted(stm[k].get('proof_dependencies') or [])
    u=used.get(k,'MISSING')
    ubad=[w for w in ['sorryAx','ofReduceBool','trustCompiler','reduceBool'] if w in u]
    extra=[]
    if 'decide +kernel' in code: extra.append('decide +kernel')
    if re.search(r'Classical\.|open Classical|open scoped Classical',code): extra.append('Classical')
    rows.append((k,method,note,hits,hitlines if hits else '',rest,calls,decl,('FAILED/MISSING' if u in('FAILED','MISSING') else ubad),extra,len(text.encode())))
if '-json' in sys.argv: print(json.dumps(rows,ensure_ascii=False))
else:
    for r in rows: print(r)
