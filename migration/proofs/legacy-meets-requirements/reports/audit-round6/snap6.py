import json,hashlib,collections,datetime,sys
exec(open('defdiff.py').read().split("old=load")[0])
T='agent-a85a026d089a3651f.jsonl'
new=load(T)
status=None; ts=[]
for line in open(S+T):
    try: e=json.loads(line)
    except: continue
    if e.get('timestamp'): ts.append(e['timestamp'])
    c=e.get('message',{}).get('content')
    if isinstance(c,list):
        for b in c:
            if b.get('type')=='tool_result':
                cc=b.get('content'); txt=cc if isinstance(cc,str) else ''.join(x.get('text','') for x in cc if isinstance(x,dict))
                if '"total_items"' in txt and '"verification_approved"' in txt and '"name"' not in txt:
                    try: status=json.loads(txt)['result']
                    except: pass
r5=json.load(open(SNAP)); o5={i['id']:i for i in r5['items']}
items=[]
for i in r5['items']:
    k=i['id']
    if k not in new: continue
    s=new[k]['statement_lean']
    items.append({'id':k,'kind':new[k]['kind'],'state':new[k]['state'],'is_auxiliary':new[k]['is_auxiliary'],
      'statement_sha256':hashlib.sha256(s.encode()).hexdigest(),'statement_bytes':len(s.encode()),
      'same_as_round5':hashlib.sha256(s.encode()).hexdigest()==i['statement_sha256']})
out={'taken_at':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
 'read_window_utc':[min(ts),max(ts)],'round':6,'blueprint_id':r5['blueprint_id'],'blueprint_name':r5['blueprint_name'],
 'status':status,
 'notes':['statement_sha256 is SHA-256 of the UTF-8 bytes of statement_lean exactly as get_items returned it (accepted Lean), computed by python3 hashlib from the raw tool results in the transcript of a read-only fetch; no Lean was retyped.',
  'Taken by the round 6 auditor after the second pass (rulings G54 to G58, rule R46). Nothing was changed on the blueprint.',
  'No Lean is stored in this file: hashes and byte counts only. same_as_round5 compares with snapshot-round5.json.',
  'Items of snapshot-round5.json no longer on the blueprint: '+', '.join(sorted(set(o5)-set(new)))],
 'item_count':len(items),'counts_by_state':dict(collections.Counter(i['state'] for i in items)),'items':items}
json.dump(out,open(sys.argv[1],'w'),indent=1,ensure_ascii=False)
print(out['item_count'],out['counts_by_state'],out['status'],out['read_window_utc'],[i['id'] for i in items if not i['same_as_round5']])
