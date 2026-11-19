import json,sys
sel=json.load(open('diffeval/work/fz5_ctable.sel.json'))
def data(c):
    s=c['input']; m=s.rfind('(fun x => Float.log (1.0 + x)) ')
    return s[m+31:] if m>=0 else s[s.rfind('(fun x => x) ')+13:]
a,b=int(sys.argv[1]),int(sys.argv[2])
for i in range(a,min(b,len(sel))):
    c=sel[i]; t='S' if c['case']['final'] is None else c['case']['a']
    print(i,t,data(c))
