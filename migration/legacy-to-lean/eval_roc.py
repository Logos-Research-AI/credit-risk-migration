"""Differential evaluation of the ROC units against experiments X07, X08, X15B, X15D.
Writes the Lean inputs for `eval_decl` (item def:model_performance_metrics, declaration
model_performance_metrics.evalApply); the comparison with SAS is done inside the Lean term, which
returns (number of cases, ids of the cases whose bits differ from SAS)."""
import re, struct, collections, sys
def f2h(x): return struct.pack(">d", x).hex().upper()
def chunks(xs, n): return [xs[i:i + n] for i in range(0, len(xs), n)]
def lst(items, n=24): return "(" + " ++ ".join("[" + ", ".join(c) + "]" for c in chunks(items, n)) + ")" if items else "[]"

AREA = ("(fun (x : List UInt64 × List (Nat × UInt64 × List Nat)) => (x.2.length, x.2.filterMap (fun c => "
        "if Option.map Float.toBits (Sas.rocArea (c.2.2.map fun k => (k % 2 == 1, Float.ofBits (x.1.getD (k / 2) 0)))) == some c.2.1 "
        "then none else some c.1)))")
ASSOC = ("(fun (x : List UInt64 × List (Nat × Nat) × List UInt64) => "
         "let t : Tabular.Table Float := x.2.1.flatMap (fun kc => List.replicate kc.2 "
         "[(\"default_flag\", Tabular.Cell.num (some (if kc.1 % 2 == 1 then 1 else 0))), (\"pd_logistic\", Tabular.Cell.num (some (Float.ofBits (x.1.getD (kc.1 / 2) 0))))]); "
         "let got := (logistic_association t).flatMap (fun r => [Option.map Float.toBits (Sas.num r \"nValue1\"), Option.map Float.toBits (Sas.num r \"nValue2\")]); "
         "(t.length, got == x.2.2.map some, got))")

def area_batch(cases):
    """cases: list of (id, expected hex, [(p hex, y)])"""
    d = sorted({h for _, _, rows in cases for h, _ in rows}); ix = {h: i for i, h in enumerate(d)}
    cs = [f"({i}, 0x{e}, [" + ", ".join(str(2 * ix[h] + y) for h, y in rows) + "])" for i, e, rows in cases]
    return f"{AREA} ({lst(['0x' + h for h in d])}, {lst(cs, 8)})"

def read_cases(sas):
    G = collections.OrderedDict()
    for l in open(sas).read().splitlines():
        m = re.match(r"^(\d+) ([0-9A-F]{16}) ([01])$", l)
        if m: G.setdefault(int(m[1]), []).append((m[2], int(m[3])))
    return G

def main(out):
    files = []
    def emit(name, text): open(f"{out}/{name}.txt", "w").write(text); files.append((name, len(text)))
    # X08
    G = read_cases("experiments/x08_roceps_boundary.sas")
    A = dict(re.findall(r"X08 roc g=(\d+) Area=([\d.]+)", open("experiments/x08_roceps_boundary.log").read()))
    cases = [(g, f2h(float(A[str(g)])), rows) for g, rows in G.items()]
    # every X08 case is (lo, non-event), (hi, event), (0.9, event), (0.95, non-event); consecutive
    # cases step hi by one unit in the last place, so a series is (lo, first hi, cases, tied cases)
    runs = []
    for g, e, rows in cases:
        assert [y for _, y in rows] == [0, 1, 1, 0] and rows[2][0] == "3FECCCCCCCCCCCCD" and rows[3][0] == "3FEE666666666666"
        lo, hi, tied = rows[0][0], int(rows[1][0], 16), e == f2h(0.375)
        assert tied or e == f2h(0.5)
        r = runs[-1] if runs else None
        if r and r[0] == lo and r[1] + r[2] == hi and (tied == (r[3] == r[2])  or not tied): r[2] += 1; r[3] += tied
        else: runs.append([lo, hi, 1, int(tied)])
    assert sum(r[2] for r in runs) == len(cases)
    X08 = ("(fun (rs : List (UInt64 × UInt64 × Nat × Nat)) => ((rs.map fun r => r.2.2.1).foldl (· + ·) 0, (rs.zip (List.range rs.length)).flatMap (fun ri => "
           "(List.range ri.1.2.2.1).filterMap (fun j => if Option.map Float.toBits (Sas.rocArea [(false, Float.ofBits ri.1.1), (true, Float.ofBits (ri.1.2.1 + j.toUInt64)), "
           "(true, Float.ofBits 0x3FECCCCCCCCCCCCD), (false, Float.ofBits 0x3FEE666666666666)]) == some (Float.toBits (if j < ri.1.2.2.2 then 0.375 else 0.5)) then none else some (ri.2, j)))))")
    emit("x08", f"{X08} {lst([f'(0x{lo}, 0x{hi:016X}, {n}, {nt})' for lo, hi, n, nt in runs], 12)}")
    # X07 roc
    G = read_cases("experiments/x07_roc_ties.sas"); log = open("experiments/x07_roc_ties.log").read()
    A = dict(re.findall(r"X07 roc g=(\d+) Area=(\w+)", log))
    cases = [(g, A[str(g)], rows) for g, rows in G.items()]
    for k, c in enumerate([cases[:46], cases[46:92], cases[92:116], cases[116:139], cases[139:]]): emit(f"x07_{k}", area_batch(c))
    # X15B
    src = open("experiments/x15_merge_roc_fit.sas").read(); l15 = open("experiments/x15_merge_roc_fit.log").read()
    exp = dict(re.findall(r"^X15B (r\d) ROCModel=M Area=(\w+)", l15, re.M)); cases = []
    for tag, body in re.findall(r"data (r\d); input p y @@; datalines;\n(.*?)\n;", src, re.S):
        v = body.split(); rows = [(f2h(float(v[i])), int(v[i + 1])) for i in range(0, len(v), 2)]
        cases.append((int(tag[1]), exp[tag], rows))
    # r2, r3, r4 are built by assignment statements in the SAS program (binary64 sums)
    built = {2: [(0.3, 1), (0.3 + 5e-9, 0), (0.6 + 2e-8, 1), (0.6, 0)],
             3: [(0.5, 1), (0.5 + 0.6e-8, 0), (0.5 + 1.2e-8, 1), (0.1, 0), (0.9, 1)],
             4: [(0.3, 0), (0.3 + 5e-9, 1), (0.8, 0), (0.2, 1)]}
    for k, rows in built.items(): cases.append((k, exp[f"r{k}"], [(f2h(p), y) for p, y in rows]))
    emit("x15b", area_batch(sorted(cases))); print("X15B sets:", sorted(c[0] for c in cases))
    # association: X07 C1..C4 and X15D
    def assoc(rows, a):
        d = sorted({p for _, p in rows}); ix = {h: i for i, h in enumerate(d)}
        cnt = collections.Counter(2 * ix[p] + y for y, p in rows)
        order = ["Percent Concordant", "Percent Discordant", "Percent Tied", "Pairs"]
        e = []
        for l1 in order: e += ["0x" + a[l1][0], "0x" + a[l1][1]]
        return f"{ASSOC} ({lst(['0x' + h for h in d])}, {lst([f'({k}, {c})' for k, c in sorted(cnt.items())])}, [{', '.join(e)}])"
    for c in "1234":
        rows = [(int(y), p) for y, p in re.findall(rf"X07 C{c} row i=\d+ y=(\d) p=(\w+)", log)]
        a = {l1.strip(): (v1, v2) for l1, v1, l2, v2 in re.findall(rf"X07 C{c} assoc Label1=(.*?) nValue1=(\w+) nValue1=\S+ Label2=(.*?) nValue2=(\w+)", log)}
        emit(f"assoc_c{c}", assoc(rows, a))
    rows = [(int(y), p) for y, p in re.findall(r"^X15D row i=\d+ y=(\S+) x1=\S+ p=(\S+)", l15, re.M)]
    a = {l1.strip(): (v1, v2) for l1, v1, l2, v2 in re.findall(r"^X15D assoc Label1=(.+?) nValue1=(\S+) Label2=(.+?) nValue2=(\S+)", l15, re.M)}
    emit("assoc_x15d", assoc(rows, a))
    for f in files: print(f)

if __name__ == "__main__":
    main(sys.argv[1])
