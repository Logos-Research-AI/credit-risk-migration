import json,sys,re
exec(open('defdiff.py').read().split("old=load")[0])
new=load('agent-a85a026d089a3651f.jsonl')
changed={'def:roc_train','def:roc_valid','def:model_summary','def:roc_train_precond','def:roc_valid_precond'}
# reverse closure over statement_dependencies and proof_dependencies
rev={}
for k,it in new.items():
    for d in (it.get('statement_dependencies') or [])+(it.get('proof_dependencies') or []):
        rev.setdefault(d,set()).add(k)
for c in sorted(changed):
    seen=set();st=[c]
    while st:
        x=st.pop()
        for y in rev.get(x,()):
            if y not in seen: seen.add(y);st.append(y)
    print(c,'<- direct:',sorted(rev.get(c,())),'| closure non-def:',len([y for y in seen if not y.startswith('def:')]),'| closure defs:',sorted(y for y in seen if y.startswith('def:')))
# names actually used in bodies (comments stripped)
def strip(t):
    return '\n'.join(l.split('--')[0] for l in t.split('\n'))
for k in ['def:sasPipeline','def:SasLinks','def:validation_summary','def:model_performance_metrics','def:roc_stats','def:roc_valid']:
    b=strip(new[k]['statement_lean'])
    print(k,'deps',new[k]['statement_dependencies'])
    print('   names in code: roc_train',len(re.findall(r'\broc_train\b',b)),'roc_valid',len(re.findall(r'\broc_valid\b',b)),'model_summary',len(re.findall(r'\bmodel_summary\b',b)),'rocObs/rocArea/rocTops',len(re.findall(r'roc(Obs|Area|Tops|Group)',b)),'merge11',len(re.findall(r'merge11',b)))
# every item whose code names the changed defs
for k,it in new.items():
    b=strip(it['statement_lean'] or '')
    hits=[n for n in ['roc_train','roc_valid','model_summary','roc_train_precond','roc_valid_precond'] if re.search(r'(?<![\w.])'+n+r'(?![\w])',b)]
    if hits and k not in changed: print('USES',k,hits)
print(new['def:validation_summary']['statement_lean'])
