import json,sys,hashlib,difflib
S='/Users/cristophersalvi/.claude/projects/-Users-cristophersalvi-GitHub-credit-risk-migration/c1fe66b8-ae3b-4265-94cf-019bef1d754b/subagents/'
SNAP='/Users/cristophersalvi/GitHub/credit-risk-migration/migration/proofs/legacy-meets-requirements/reports/snapshot-round5.json'
def load(f):
    uses={};items={}
    for line in open(S+f):
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
                if n=='get_items' and isinstance(r,list):
                    for it in r:
                        if 'statement_lean' in it: items[it['id']]=it
    return items
old=load('agent-a3d12f6ed67f518e0.jsonl'); new=load('agent-a85a026d089a3651f.jsonl')
sn={i['id']:i for i in json.load(open(SNAP))['items']}
h=lambda s:hashlib.sha256(s.encode()).hexdigest()
for k in ['def:roc_train','def:roc_valid','def:model_summary','def:roc_train_precond','def:roc_valid_precond']:
    o=old[k]['statement_lean']; n=new[k]['statement_lean']
    print('=====',k,'baseline text hash equals snapshot:',h(o)==sn[k]['statement_sha256'],'bytes',len(o.encode()),'->',len(n.encode()),'deps',new[k]['statement_dependencies'])
    if '-full' in sys.argv: print(n)
    else:
        for l in difflib.unified_diff(o.split('\n'),n.split('\n'),lineterm='',n=2): print(l)
