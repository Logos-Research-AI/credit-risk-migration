"""Differential evaluation helpers: build Lean terms from CSV rows, run them through eval_decl
(migration/mcp_eval.py), read results back bit-exactly, compare with SAS's printed values."""
import csv, json, re, struct, math, sys
sys.path.insert(0, "migration")
from mcp_eval import Mcp

VIEW = ('(fun (t : Tabular.Table Float) => t.map (fun r => r.map (fun p => p.1 ++ "=" ++ '
        '(match p.2 with | Tabular.Cell.num (some v) => toString v.toBits | Tabular.Cell.num none => "." '
        '| Tabular.Cell.str (some s) => "$" ++ s | Tabular.Cell.str none => "$"))))')
NUMVIEW = '(fun (x : Option Float) => match x with | some v => toString v.toBits | none => ".")'

def lean_str(s): return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def lean_num(txt):
    """Lean term of type Option Float for a CSV numeric field ('' or '.' = missing)."""
    t = txt.strip()
    if t in ("", ".", "NA"): return "none"
    if t.startswith("-"): return f"(some (-{lean_lit(t[1:])}))"
    return f"(some {lean_lit(t)})"

def lean_lit(t):
    if re.fullmatch(r"\d+", t): return t
    if re.fullmatch(r"\d*\.\d*", t):
        if t.startswith("."): t = "0" + t
        if t.endswith("."): t = t + "0"
        return t
    m = re.fullmatch(r"(\d+(?:\.\d+)?)[eE]([+-]?\d+)", t)
    if m: return f"{m.group(1) if '.' in m.group(1) else m.group(1)+'.0'}e{int(m.group(2))}"
    raise ValueError(t)

def lean_row(cols):
    """cols: list of (name, kind, text) with kind 'n' or 's'."""
    cells = []
    for name, kind, txt in cols:
        if kind == "n": cells.append(f"({lean_str(name)}, Tabular.Cell.num {lean_num(txt)})")
        else: cells.append(f"({lean_str(name)}, Tabular.Cell.str {'none' if txt == '' else '(some ' + lean_str(txt) + ')'})")
    return "[" + ", ".join(cells) + "]"

def lean_table(rows, chunk=10):
    """A long list literal overflows the evaluator's recursion limit: build it as a balanced
    tree of concatenations of short literals."""
    if len(rows) <= chunk: return "[" + ", ".join(rows) + "]"
    h = len(rows) // 2
    return "(List.append " + lean_table(rows[:h], chunk) + " " + lean_table(rows[h:], chunk) + ")"

def parse_view(out):
    """Output of VIEW: list of rows, each a dict name -> float | None | str."""
    rows = []
    for rowtxt in re.findall(r"\[((?:\"(?:[^\"\\]|\\.)*\"(?:,\s*)?)*)\]", out):
        d = {}
        for cell in re.findall(r"\"((?:[^\"\\]|\\.)*)\"", rowtxt):
            cell = cell.replace('\\"', '"').replace("\\\\", "\\")
            k, v = cell.split("=", 1)
            if v == ".": d[k] = None
            elif v.startswith("$"): d[k] = v[1:]
            else: d[k] = struct.unpack(">d", struct.pack(">Q", int(v)))[0]
        rows.append(d)
    return rows

def bits(s):
    return None if s.strip('"') == "." else struct.unpack(">d", struct.pack(">Q", int(s.strip('"'))))[0]

def close_printed(v, txt, fmt="best12"):
    """Is the double v what SAS printed as txt? Missing prints as '' or '.'."""
    t = txt.strip()
    if v is None: return t in ("", ".")
    if t in ("", "."): return False
    if fmt == "pct":      # percent8.2 -> '35.04%'
        return abs(v * 100 - float(t.rstrip("%"))) <= 0.005 + 1e-9
    if fmt.startswith("f"):  # fixed decimals, e.g. f4
        dec = int(fmt[1:]); return abs(v - float(t)) <= 0.5 * 10 ** (-dec) + 1e-12
    x = float(t)
    if v == x: return True
    if "E" in t.upper():
        mant = t.upper().split("E")[0]; digs = len(mant.replace("-", "").replace(".", ""))
        return abs(v - x) <= abs(x) * 10 ** (-(digs - 1))
    dec = len(t.split(".")[1]) if "." in t else 0
    # half a unit of the last printed digit; BEST12. may round a decimal tie either way (X04)
    return abs(v - x) <= 0.5 * 10 ** (-dec) * 1.0000001 + 4 * math.ulp(x)

def run(mcp, item, inputs, decl=None):
    res = mcp.eval_decl(item, inputs, decl)
    if not res.get("success"): raise RuntimeError(str(res)[:2000])
    outs = []
    for c in res["cases"]:
        if c["kind"] != "returned": raise RuntimeError(str({k: v for k, v in c.items() if k != "input"})[:3000])
        outs.append(c["output"])
    return outs, res.get("elapsed_ms")

VIEWS = ('(fun (ts : List (Tabular.Table Float)) => ts.map (fun t => t.map (fun r => r.map (fun p => p.1 ++ "=" ++ '
         '(match p.2 with | Tabular.Cell.num (some v) => toString v.toBits | Tabular.Cell.num none => "." '
         '| Tabular.Cell.str (some s) => "$" ++ s | Tabular.Cell.str none => "$")))))')
AGG = "(Sas.SqlAgg.mk (fun (xs : List Float) => xs.foldl (· + ·) 0) (fun (xs : List Float) => xs.foldl (· + ·) 0 / xs.length.toFloat))"

def parse_views(out):
    """Output of VIEWS -> list of tables; a table is a list of ordered (name, value) lists."""
    tabs = []
    for t in json.loads(out):
        rows = []
        for r in t:
            row = []
            for cell in r:
                k, v = cell.split("=", 1)
                if v == ".": row.append((k, None))
                elif v.startswith("$"): row.append((k, v[1:]))
                else: row.append((k, struct.unpack(">d", struct.pack(">Q", int(v)))[0]))
            rows.append(row)
        tabs.append(rows)
    return tabs

def fbits(x): return "(Float.ofBits 0x%s)" % struct.pack(">d", x).hex()
def hexd(h): return struct.unpack(">d", bytes.fromhex(h))[0]

def read_dump(path):
    """migration/runs/<id>/dump.txt -> {dataset: [ {var: value} ]}: numeric vars as float|None (from HEX16), character as str."""
    plain, hexs = {}, {}
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("DUMPX "):
            _, ds, rest = line.split(" ", 2) if line.count(" ") >= 2 else (None, line.split(" ")[1], "")
            d = {}
            for k, v in re.findall(r"([A-Za-z_0-9]+)=(\S+)", rest): d[k] = None if v == "." else hexd(v)
            hexs.setdefault(ds, []).append(d)
        elif line.startswith("DUMP "):
            _, ds, rest = line.split(" ", 2)
            parts = re.split(r"(?:^| )([A-Za-z_][A-Za-z_0-9]*)=", rest)
            d = {}; order = []
            for k, v in zip(parts[1::2], parts[2::2]): d[k] = v.strip(); order.append(k)
            d["__order__"] = order
            plain.setdefault(ds, []).append(d)
    out = {}
    for ds, rows in plain.items():
        hx = hexs.get(ds, [{}] * len(rows))
        res = []
        for r, h in zip(rows, hx + [{}] * (len(rows) - len(hx))):
            res.append([(k, h[k] if k in h else (None if (r[k] == "." and k in h) else r[k])) for k in r["__order__"]])
        out[ds] = res
    return out

# one string per row (cells separated by U+0001): keeps the printed result shallow
ROWVIEW = ('(fun (t : Tabular.Table Float) => t.map (fun r => String.intercalate "|" (r.map (fun p => p.1 ++ "=" ++ '
           '(match p.2 with | Tabular.Cell.num (some v) => toString v.toBits | Tabular.Cell.num none => "." '
           '| Tabular.Cell.str (some s) => "$" ++ s | Tabular.Cell.str none => "$")))))')

def parse_rowview(out):
    rows = []
    for line in json.loads(out):
        row = []
        for cell in line.split("|"):
            if not cell: continue
            k, v = cell.split("=", 1)
            if v == ".": row.append((k, None))
            elif v.startswith("$"): row.append((k, v[1:]))
            else: row.append((k, struct.unpack(">d", struct.pack(">Q", int(v)))[0]))
        rows.append(row)
    return rows
