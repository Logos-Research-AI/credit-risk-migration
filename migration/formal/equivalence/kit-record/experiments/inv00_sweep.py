"""Gap-inventory sweep: enumerate every construct site in the in-scope code by AST walk.
Usage: uv run python migration/experiments/inv00_sweep.py . <created.json out> > sites.tsv   (tab-separated: file, line, col, tag, n, symbol, enclosing calls, columns, snippet; counts on stderr). migration/inventory.sites.txt is this output reformatted."""
import ast, sys, collections
root = sys.argv[1]
OOS = {"fit_logistic","stepwise_logistic","proc_import_csv","input_best32","sas_best","sas_best12","fmt_wd","fmt_oddsr",
       "fmt_percent","sas_d8","sas_d12_3","sas_pvalue","write_sas_csv","date9","today_date9","sas_round_scalar","_loglik"}
SCOPE = {
 "credit_risk/sas_compat.py": ["FloatArray","Z975","ExprOrNum","_TWO52","_ROUND_FUZZ","_TIE_EPS","_e","_named","_has_bare_column","_is_scalar","chi2_sf","lt","le","gt","ge","eq","flag","div","sas_sum","sas_min","sas_max","sas_log","sas_exp","sas_round","sql_sum","sql_mean","sql_min","sql_max","merge_one_to_one","proc_rank_groups","proc_rank_apply_groups","LogisticFit","_expit","_Pairs","_pairs","_ratio","RocAssociation","roc_association","AssociationTable","association_table","_hl_groups","hosmer_lemeshow","classification_table"],
 "credit_risk/feature_engineering.py": ["run"],
 "credit_risk/metrics_calculation.py": ["_into_float","confusion_metrics","run"],
 "credit_risk/predict.py": ["run"],
 "credit_risk/train.py": ["run"],
}
METH = {"fill_null":"FILL_NULL","is_null":"IS_NULL","is_not_null":"IS_NULL","cast":"CAST","astype":"CAST","group_by":"GROUP_BY",
 "join":"JOIN","sort":"SORT","rank":"RANK","filter":"FILTER","concat":"CONCAT","concatenate":"CONCAT","cum_sum":"CUMSUM","cumsum":"CUMSUM",
 "sum":"AGG","mean":"AGG","median":"AGG","min":"AGG","max":"AGG","count":"AGG","null_count":"AGG","len":"AGG","var":"AGG","count_nonzero":"AGG",
 "is_in":"IS_IN","searchsorted":"SEARCHSORTED","argsort":"SORT","drop_nulls":"DROP_NULLS","to_numpy":"TO_NUMPY","to_list":"TO_LIST",
 "to_series":"TO_LIST","item":"ITEM","get_column":"COLREF","implode":"IS_IN","map_batches":"MAP_BATCHES",
 "max_horizontal":"HORIZ","min_horizontal":"HORIZ","sum_horizontal":"HORIZ","all_horizontal":"HORIZ",
 "select":"FRAME_COLS","with_columns":"FRAME_COLS","agg":"FRAME_COLS","drop":"FRAME_COLS","rename":"FRAME_COLS",
 "abs":"UNARY","floor":"FLOOR_CEIL","ceil":"FLOOR_CEIL","sign":"UNARY","is_finite":"FINITE","isfinite":"FINITE","isnan":"FINITE",
 "log":"LOG_EXP_SQRT","exp":"LOG_EXP_SQRT","sqrt":"LOG_EXP_SQRT","log1p":"LOG_EXP_SQRT",
 "iter_columns":"DICT_ORDER","items":"DICT_ORDER","values":"DICT_ORDER","index":"LOOKUP","pop":"LOOKUP",
 "output_name":"META","serialize":"META","field":"LOOKUP","struct":"MAP_BATCHES",
 "DataFrame":"CONSTRUCT","Series":"CONSTRUCT","read_csv":"OOS_CALL","loads":"OOS_CALL","dump":"OOS_CALL","read_text":"OOS_CALL",
 "today":"DATE_TODAY","sf":"OOS_CALL","inv":"OOS_CALL","solve":"OOS_CALL","einsum":"OOS_CALL",
 "where":"NP_ELEMWISE","clip":"NP_ELEMWISE","divide":"DIV","repeat":"NP_ELEMWISE","arange":"NP_ELEMWISE","round":"NP_ELEMWISE",
 "column_stack":"NP_ELEMWISE","ones":"NP_ELEMWISE","asarray":"TO_NUMPY","errstate":None,"mkdir":None,"open":None,"append":None,"extend":None,
 "lit":"LIT","then":"LIT","otherwise":"LIT","when":None,"col":None,"alias":None,"split":None,"lower":None,"all":None}
BUILTIN = {"int":"F2I_INT","float":"FLOAT_CONV","str":"STR_CONV","bool":"BOOL_CONV","len":"LEN","max":"PY_MINMAX","min":"PY_MINMAX",
 "abs":"UNARY","zip":"ZIP","set":"SET","isinstance":"TYPE_DISPATCH","enumerate":None,"list":None,"dict":None,"print":None,"cast":None,"any":None,"range":"RANGE"}
out=[]
created=[]
INSCOPE={n for n in SCOPE["credit_risk/sas_compat.py"]}|{"_into_float","confusion_metrics","pct","run"}
def snippet(src,node,n=110):
    s=ast.get_source_segment(src,node) or ""
    s=" ".join(s.split())
    return s if len(s)<=n else s[:n-3]+"..."
class V(ast.NodeVisitor):
    def __init__(s,f,src,sym): s.f=f;s.src=src;s.sym=sym;s.ctx=[];s.encl=[]
    def add(s,node,tag,extra=""):
        sym=s.sym+(":"+s.ctx[-1] if s.ctx else "")
        line,col,snip=node.lineno,node.col_offset,snippet(s.src,node,100000)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            line,col=node.func.end_lineno,node.func.end_col_offset-len(node.func.attr)   # site = where the method name is
        if len(snip)>120: snip="..."+snip[-117:]
        cols=""
        if isinstance(node,ast.Call) and tag in ("FRAME_COLS","COLREF","SORT","GROUP_BY","JOIN","FILTER","ITEM"):
            found=[]
            for part in list(node.args)+[k.value for k in node.keywords]:
                for n in ast.walk(part):
                    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="col":
                        found+= [a.value for a in n.args if isinstance(a,ast.Constant) and isinstance(a.value,str)]
                        found+= ["*"+ast.unparse(a) for a in n.args if not isinstance(a,ast.Constant)]
                if isinstance(part,ast.Constant) and isinstance(part.value,str): found.append(part.value)
                if isinstance(part,ast.List): found+=[e.value for e in part.elts if isinstance(e,ast.Constant) and isinstance(e.value,str)]
                if isinstance(part,ast.Dict): found+=[e.value for e in part.keys if isinstance(e,ast.Constant)]
            for k in node.keywords:
                if k.arg in ("how","maintain_order","side","kind","format"): 
                    if isinstance(k.value,ast.Constant) and k.value.value in found: found.remove(k.value.value)
            cols=",".join(dict.fromkeys(found))
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in ("with_columns","select","agg"):
            for k in node.keywords:
                if k.arg: created.append((s.f,s.sym.split(":")[0],k.arg,k.value.lineno))
            for part in node.args:
                for n in ast.walk(part):
                    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="alias" and n.args and isinstance(n.args[0],ast.Constant): created.append((s.f,s.sym.split(":")[0],n.args[0].value,n.lineno))
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="rename" and node.args and isinstance(node.args[0],ast.Dict):
            for v in node.args[0].values: created.append((s.f,s.sym.split(":")[0],v.value,v.lineno))
        out.append((s.f,line,col,tag,sym,"<".join(reversed(s.encl[-3:])) or "-",cols or "-",snip))
    def visit_arguments(s,node):
        for d in node.defaults+node.kw_defaults:
            if d is not None: s.visit(d)
    def visit_AnnAssign(s,node):
        if node.value is not None: s.visit(node.value)
    def visit_FunctionDef(s,node):
        s.visit(node.args)
        for b in node.body: s.visit(b)
    def visit_BinOp(s,node):
        if isinstance(node.op,(ast.Div,ast.FloorDiv)):
            if not (isinstance(node.right,(ast.JoinedStr,)) or (isinstance(node.right,ast.Constant) and isinstance(node.right.value,str))): s.add(node,"DIV")   # pathlib joins excluded
        elif isinstance(node.op,ast.Pow): s.add(node,"POW")
        elif isinstance(node.op,ast.MatMult): s.add(node,"OOS_CALL","matmul@")
        elif isinstance(node.op,ast.Add) and isinstance(node.right,ast.Constant) and type(node.right.value) is float and node.right.value==0.0: s.add(node,"ADD_ZERO")
        elif isinstance(node.op,(ast.Add,ast.Sub,ast.Mult)):
            for o in (node.left,node.right):
                if isinstance(o,ast.Constant) and type(o.value) is int: s.add(node,"INT_PROMO"); break
        s.generic_visit(node)
    def visit_Assign(s,node):
        t=node.targets[0]
        nm=t.id if isinstance(t,ast.Name) else (",".join(e.id for e in t.elts if isinstance(e,ast.Name)) if isinstance(t,ast.Tuple) else snippet(s.src,t,40))
        s.ctx.append(nm); s.generic_visit(node); s.ctx.pop()
    def visit_Return(s,node):
        s.ctx.append("return"); s.generic_visit(node); s.ctx.pop()
    def visit_Compare(s,node): s.add(node,"CMP"); s.generic_visit(node)
    def visit_While(s,node): s.add(node,"WHILE"); s.generic_visit(node)
    def visit_Raise(s,node): s.add(node,"RAISE"); s.generic_visit(node)
    def visit_Subscript(s,node):
        if isinstance(node.ctx,ast.Load): s.add(node,"LOOKUP")
        s.generic_visit(node)
    def visit_Set(s,node): s.add(node,"SET"); s.generic_visit(node)
    def visit_Attribute(s,node):
        if node.attr in ("height","ndim","shape","T","columns"): s.add(node,{"height":"LEN","T":"NP_ELEMWISE","columns":"DICT_ORDER"}.get(node.attr,"TYPE_DISPATCH"))
        s.generic_visit(node)
    def visit_Call(s,node):
        f=node.func
        if isinstance(f,ast.Attribute):
            base=f.value
            if isinstance(base,ast.Name) and base.id=="sas_compat" and f.attr in OOS: s.add(node,"OOS_CALL")
            elif f.attr in METH:
                tag=METH[f.attr]
                if tag=="LIT":
                    a=node.args[0] if node.args else None
                    if isinstance(a,ast.Constant) and isinstance(a.value,str): pass   # string literal: no gap
                    elif f.attr=="lit" or (isinstance(a,ast.Constant) and (a.value is None or type(a.value) in (int,float))): s.add(node,"LIT",f.attr)
                elif tag: s.add(node,tag,f.attr)
            else: s.add(node,"HELPER_CALL" if isinstance(base,ast.Name) and base.id=="sas_compat" and f.attr!="chi2_sf" else ("OOS_CALL" if f.attr=="chi2_sf" else "OTHER_CALL"),f.attr)
        elif isinstance(f,ast.Name):
            if f.id in OOS: s.add(node,"OOS_CALL")
            elif f.id in BUILTIN:
                if BUILTIN[f.id]: s.add(node,BUILTIN[f.id],f.id)
            elif f.id in INSCOPE: s.add(node,"HELPER_CALL",f.id)
        for k in node.keywords:
            if k.arg=="strict" and isinstance(f,ast.Name) and f.id=="zip": s.add(node,"ZIP_STRICT")
            if k.arg=="nan_to_null": s.add(node,"NAN_TO_NULL")
        nm=f.attr if isinstance(f,ast.Attribute) else getattr(f,"id","?")
        # receiver chain: alias("x") names the context of its receiver
        pushed=False
        if nm=="alias" and node.args and isinstance(node.args[0],ast.Constant): s.ctx.append(node.args[0].value); pushed=True
        s.visit(f)
        if pushed: s.ctx.pop()
        s.encl.append(nm)
        for a in node.args: s.visit(a)
        for k in node.keywords:
            named = nm in ("with_columns","select","agg") and k.arg
            if named: s.ctx.append(k.arg)
            s.visit(k.value)
            if named: s.ctx.pop()
        s.encl.pop()
for f,names in SCOPE.items():
    src=open(f"{root}/{f}").read(); tree=ast.parse(src)
    mod=f.split("/")[-1][:-3]
    for node in tree.body:
        nm=None
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)): nm=node.name
        elif isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name): nm=node.targets[0].id
        elif isinstance(node,ast.AnnAssign): nm=node.target.id
        if nm in names:
            if any(isinstance(d,ast.Name) and d.id=="overload" for d in getattr(node,"decorator_list",[])): continue
            v=V(f,src,f"{mod}.{nm}" if mod!="sas_compat" else nm)
            if isinstance(node,ast.FunctionDef): v.visit(node)
            elif isinstance(node,ast.ClassDef): out.append((f,node.lineno,node.col_offset,"DATACLASS",v.sym,"-","-","class "+nm)); 
            else:
                out.append((f,node.lineno,node.col_offset,"CONST",v.sym,"-","-",snippet(src,node))); v.visit(node.value) if node.value else None
out=sorted(set(out))
seen=collections.Counter()
for r in out:
    k=(r[0],r[1],r[2],r[3]); seen[k]+=1
    print("\t".join(map(str,r[:4]+((seen[k],))+r[4:])))
import json; json.dump(sorted(set(created)),open(sys.argv[2],"w"))
c=collections.Counter(r[3] for r in out)
print(f"# total sites: {len(out)}",file=sys.stderr)
for k,v in sorted(c.items()): print(f"# {k}\t{v}",file=sys.stderr)
