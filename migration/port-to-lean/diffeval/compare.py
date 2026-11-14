"""Exact comparison of Lean results (text returned by eval_decl) with Python results.

Canonical form of a value (JSON-serialisable), on both sides:
  column  {"type": "col", "kind": "f64"|"int"|"bool"|"str"|"cell"|"null", "values": [...]}
          f64 values are the IEEE bits as an int (every NaN is 0x7FF8000000000000, as Lean's
          Float.toBits gives), null is None. A null and a NaN are therefore different values.
          kind "null" is the polars dtype Null / `Pl.Col.null n`: n values, all None. It is a
          different kind from an all-null Float64 column (`.kind` difference).
  frame   {"type": "frame", "cols": [[name, column], ...]}            (column order kept)
  table   {"type": "table", "rows": [[[name, "num"|"str", value], ...], ...]}  (row order kept)

CLI:  uv run python migration/diffeval/compare.py work/<suite>.json work/<suite>.out.txt
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

M64 = (1 << 64) - 1
NAN_BITS = 0x7FF8000000000000
KINDS = {1: "f64", 2: "int", 3: "bool", 4: "str", 5: "cell", 6: "null"}
KCODE = {v: k for k, v in KINDS.items()}


def fbits(x: float) -> int:
    if x != x:
        return NAN_BITS
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def show_bits(b) -> str:
    if b is None:
        return "null"
    return f"0x{b:016x} ({struct.unpack('<d', struct.pack('<Q', b))[0]!r})"


# ------------------------------------------------------------------ Python values -> canonical
def canon_floats(xs) -> dict:
    """A list of floats / None (a numpy array, a to_list()) as an f64 column."""
    return {"type": "col", "kind": "f64", "values": [None if x is None else fbits(float(x)) for x in xs]}


def canon_ints(xs) -> dict:
    return {"type": "col", "kind": "int", "values": [None if x is None else int(x) for x in xs]}


def canon_bools(xs) -> dict:
    return {"type": "col", "kind": "bool", "values": [None if x is None else bool(x) for x in xs]}


def canon_strs(xs) -> dict:
    return {"type": "col", "kind": "str", "values": list(xs)}


def canon_nulls(n: int) -> dict:
    """A Null-dtype column of n nulls (`Pl.Col.null n`)."""
    return {"type": "col", "kind": "null", "values": [None] * n}


def canon_series(s) -> dict:
    from leanterm import col_kind

    k = col_kind(s.dtype)
    vals = s.to_list()
    if k == "f64":
        return canon_floats(vals)
    if k == "int":
        return canon_ints(vals)
    if k == "bool":
        return canon_bools(vals)
    if k == "str":
        return canon_strs(vals)
    if k == "null":
        return canon_nulls(len(vals))
    return {"type": "col", "kind": k, "values": [None if v is None else str(v) for v in vals]}


def canon_frame(df) -> dict:
    return {"type": "frame", "cols": [[n, canon_series(df.get_column(n))] for n in df.columns]}


def canon_table(df) -> dict:
    """The table a frame becomes at a stage boundary: ints and bools are numeric cells."""
    from leanterm import col_kind

    kinds = [col_kind(df.schema[n]) for n in df.columns]
    rows = []
    for r in df.iter_rows():
        row = []
        for n, k, v in zip(df.columns, kinds, r, strict=True):
            if k == "str":
                row.append([n, "str", v])
            else:
                row.append([n, "num", None if v is None else fbits(float(v))])
        rows.append(row)
    return {"type": "table", "rows": rows}


# ------------------------------------------------------------------ parser of Lean `repr` text
class _P:
    def __init__(self, s: str):
        self.s, self.i = s, 0

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \n\t\r":
            self.i += 1

    def peek(self) -> str:
        self.ws()
        return self.s[self.i] if self.i < len(self.s) else ""

    def eat(self, ch: str):
        self.ws()
        if not self.s.startswith(ch, self.i):
            raise ValueError(f"expected {ch!r} at {self.i}: {self.s[self.i:self.i + 30]!r}")
        self.i += len(ch)

    def value(self):
        c = self.peek()
        if c == "[" or (c == "#" and self.s.startswith("#[", self.i)):
            self.eat("#[" if c == "#" else "[")
            out = []
            if self.peek() == "]":
                self.eat("]")
                return out
            while True:
                out.append(self.value())
                if self.peek() == ",":
                    self.eat(",")
                else:
                    self.eat("]")
                    return out
        if c == "(":
            self.eat("(")
            if self.peek() == ")":
                self.eat(")")
                return ()
            items = [self.value()]
            while self.peek() == ",":
                self.eat(",")
                items.append(self.value())
            self.eat(")")
            return items[0] if len(items) == 1 else tuple(items)
        if c == '"':
            return self.string()
        if c == "-" or c.isdigit():
            j = self.i + 1
            while j < len(self.s) and self.s[j].isdigit():
                j += 1
            n = int(self.s[self.i:j])
            self.i = j
            return n
        j = self.i
        while j < len(self.s) and (self.s[j].isalnum() or self.s[j] in "_."):
            j += 1
        word = self.s[self.i:j]
        self.i = j
        if word == "none":
            return None
        if word == "some":
            return self.value()
        if word == "true":
            return True
        if word == "false":
            return False
        raise ValueError(f"unexpected token {word!r} at {self.i}: {self.s[self.i:self.i + 30]!r}")

    def string(self) -> str:
        self.eat('"')
        out = []
        while True:
            ch = self.s[self.i]
            self.i += 1
            if ch == '"':
                return "".join(out)
            if ch != "\\":
                out.append(ch)
                continue
            e = self.s[self.i]
            self.i += 1
            if e in "\\\"'":
                out.append(e)
            elif e == "n":
                out.append("\n")
            elif e == "t":
                out.append("\t")
            elif e == "r":
                out.append("\r")
            elif e == "x":
                out.append(chr(int(self.s[self.i:self.i + 2], 16)))
                self.i += 2
            elif e == "u":
                if self.s[self.i] == "{":
                    j = self.s.index("}", self.i)
                    out.append(chr(int(self.s[self.i + 1:j], 16)))
                    self.i = j + 1
                else:
                    out.append(chr(int(self.s[self.i:self.i + 4], 16)))
                    self.i += 4
            elif e == "\n":  # string gap
                while self.s[self.i] in " \t":
                    self.i += 1
            else:
                raise ValueError(f"unknown escape \\{e}")


def parse_lean(text: str):
    """Parse the `repr` of nested lists / tuples / Option / Nat / Int / Bool / String.
    `some x` becomes x and `none` becomes None."""
    p = _P(text)
    v = p.value()
    p.ws()
    if p.i != len(text):
        raise ValueError(f"trailing text at {p.i}: {text[p.i:p.i + 40]!r}")
    return v


# ------------------------------------------------------------------ dumps -> canonical
def _dump_col(d) -> dict:
    kind, f, i, b, s = d
    if kind == "f64":
        return {"type": "col", "kind": "f64", "values": list(f)}
    if kind == "int":
        return {"type": "col", "kind": "int", "values": list(i)}
    if kind == "bool":
        return {"type": "col", "kind": "bool", "values": list(b)}
    if kind == "str":
        return {"type": "col", "kind": "str", "values": list(s)}
    if kind == "null":  # DUMP_COL puts the n nulls in the ints list
        if any(v is not None for v in i) or f or b or s:
            raise ValueError("malformed null column dump")
        return canon_nulls(len(i))
    if kind != "cell":
        raise ValueError(f"unknown column kind {kind!r}")
    return {"type": "col", "kind": "cell",
            "values": [["num", x] if isnum else ["str", t] for x, isnum, t in zip(f, b, s, strict=True)]}


def dump_to_canon(kind: str, d) -> dict:
    """Convert one parsed DUMP_* result. kind: col | frame | table | floats | optfloats."""
    if kind == "col":
        return _dump_col(d)
    if kind == "frame":
        # Lean prints (name, (kind, ..)) as the flat tuple (name, kind, ..)
        return {"type": "frame", "cols": [[c[0], _dump_col(c[1:])] for c in d]}
    if kind == "table":
        return {"type": "table", "rows": [[[n, k, (x if k == "num" else t)] for n, k, x, t in r] for r in d]}
    if kind in ("floats", "optfloats"):
        return {"type": "col", "kind": "f64", "values": list(d)}
    raise ValueError(kind)


# ------------------------------------------------------------------ tokens and digest
def tok_str(s: str) -> list[int]:
    return [len(s)] + [ord(c) for c in s]


def _tok_cell(k: str, v) -> list[int]:
    if k == "num":
        return [1, 0] if v is None else [1, 1, v]
    return [2, 0] if v is None else [2, 1] + tok_str(v)


def tok_col(c: dict) -> list[int]:
    k, vals = c["kind"], c["values"]
    if k == "null":  # mirrors `| .null n => [6, n]`: no per-value tokens
        return [KCODE[k], len(vals)]
    out = [KCODE.get(k, 99), len(vals)]
    for v in vals:
        if k == "cell":
            out += _tok_cell(v[0], v[1])
        elif v is None:
            out.append(0)
        elif k == "f64":
            out += [1, v]
        elif k == "int":
            out += [2 if v < 0 else 1, abs(v)]
        elif k == "bool":
            out += [1, 1 if v else 0]
        elif k == "str":
            out += [1] + tok_str(v)
        else:
            out += [1] + tok_str(str(v))
    return out


def tokens(c: dict) -> list[int]:
    """Token stream of a canonical value; mirrors tC / tR / tA of kit.KIT.
    (tF/tI/tB/tT of the kit are tC without the leading kind code: use `tC (.f64 v)` etc.)"""
    if c["type"] == "col":
        return tok_col(c)
    if c["type"] == "frame":
        out = [len(c["cols"])]
        for n, col in c["cols"]:
            out += tok_str(n) + tok_col(col)
        return out
    out = [len(c["rows"])]
    for r in c["rows"]:
        out.append(len(r))
        for n, k, v in r:
            out += tok_str(n) + _tok_cell(k, v)
    return out


def digest(toks: list[int]) -> int:
    h = 14695981039346656037
    for x in toks:
        g = ((h ^ x) * 1099511628211) & M64
        h = g ^ (g >> 32)
    return h


class _T:
    def __init__(self, t):
        self.t, self.i = t, 0

    def n(self) -> int:
        v = self.t[self.i]
        self.i += 1
        return v

    def s(self) -> str:
        return "".join(chr(self.n()) for _ in range(self.n()))

    def cell(self):
        k = self.n()
        some = self.n()
        if k == 1:
            return ["num", self.n() if some else None]
        return ["str", self.s() if some else None]

    def col(self) -> dict:
        k = KINDS[self.n()]
        if k == "null":
            return canon_nulls(self.n())
        vals = []
        for _ in range(self.n()):
            if k == "cell":
                vals.append(self.cell())
                continue
            tag = self.n()
            if tag == 0:
                vals.append(None)
            elif k == "f64":
                vals.append(self.n())
            elif k == "int":
                vals.append(-self.n() if tag == 2 else self.n())
            elif k == "bool":
                vals.append(self.n() == 1)
            else:
                vals.append(self.s())
        return {"type": "col", "kind": k, "values": vals}


def decode_tokens(kind: str, toks: list[int]) -> dict:
    t = _T(toks)
    if kind == "col":
        out = t.col()
    elif kind == "frame":
        out = {"type": "frame", "cols": [[t.s(), t.col()] for _ in range(t.n())]}
    elif kind == "table":
        out = {"type": "table", "rows": [[(lambda n, c: [n, c[0], c[1]])(t.s(), t.cell()) for _ in range(t.n())] for _ in range(t.n())]}
    else:
        raise ValueError(kind)
    if t.i != len(toks):
        raise ValueError("trailing tokens")
    return out


def undo_cumsum(xs: list[int]) -> list[int]:
    return [x - (xs[i - 1] if i else 0) for i, x in enumerate(xs)]


# ------------------------------------------------------------------ structural comparison
def _ulp_close(a: int, b: int, tol: int) -> bool:
    if tol <= 0 or a is None or b is None or a == b:
        return False
    fa, fb = (struct.unpack("<d", struct.pack("<Q", x))[0] for x in (a, b))
    if not (math.isfinite(fa) and math.isfinite(fb)) or (a >> 63) != (b >> 63):
        return False
    return abs(a - b) <= tol


def _diff_col(path: str, e: dict, g: dict, out: list, ulps: list, tol: int):
    if e["kind"] != g["kind"]:
        out.append((path + ".kind", e["kind"], g["kind"]))
        # still compare numerically comparable values so the report says whether only the dtype differs
        if {e["kind"], g["kind"]} != {"f64", "int"}:
            return
        ev = [None if v is None else (fbits(float(v)) if e["kind"] == "int" else v) for v in e["values"]]
        gv = [None if v is None else (fbits(float(v)) if g["kind"] == "int" else v) for v in g["values"]]
        e, g = {"kind": "f64", "values": ev}, {"kind": "f64", "values": gv}
    if len(e["values"]) != len(g["values"]):
        out.append((path + ".len", len(e["values"]), len(g["values"])))
    for i, (a, b) in enumerate(zip(e["values"], g["values"], strict=False)):
        if a == b and type(a) is type(b):
            continue
        if e["kind"] == "f64":
            if _ulp_close(a, b, tol):
                ulps.append((f"{path}[{i}]", show_bits(a), show_bits(b)))
            else:
                out.append((f"{path}[{i}]", show_bits(a), show_bits(b)))
        else:
            out.append((f"{path}[{i}]", repr(a), repr(b)))


def diff(expected: dict, got: dict, ulp_tol: int = 0):
    """Return (differences, ulp_differences): lists of (path, expected, got). Exact on float
    bits, null vs NaN, kind, names, order and lengths. With ulp_tol > 0, finite floats of the
    same sign whose bits differ by at most ulp_tol go to the second list."""
    out, ulps = [], []
    if expected["type"] != got["type"]:
        return [("type", expected["type"], got["type"])], ulps
    if expected["type"] == "col":
        _diff_col("col", expected, got, out, ulps, ulp_tol)
    elif expected["type"] == "frame":
        ec, gc = expected["cols"], got["cols"]
        if [n for n, _ in ec] != [n for n, _ in gc]:
            out.append(("frame.columns", [n for n, _ in ec], [n for n, _ in gc]))
        for j, ((en, e), (gn, g)) in enumerate(zip(ec, gc, strict=False)):
            _diff_col(f"frame.col[{j}:{en}" + ("" if en == gn else f"|got {gn}") + "]", e, g, out, ulps, ulp_tol)
    else:
        er, gr = expected["rows"], got["rows"]
        if len(er) != len(gr):
            out.append(("table.height", len(er), len(gr)))
        for i, (e, g) in enumerate(zip(er, gr, strict=False)):
            if [c[0] for c in e] != [c[0] for c in g]:
                out.append((f"table.row[{i}].columns", [c[0] for c in e], [c[0] for c in g]))
            for j, (a, b) in enumerate(zip(e, g, strict=False)):
                if a[1] != b[1]:
                    out.append((f"table.row[{i}].cell[{j}:{a[0]}].kind", a[1], b[1]))
                elif a[2] != b[2]:
                    if a[1] == "num" and _ulp_close(a[2], b[2], ulp_tol):
                        ulps.append((f"table.row[{i}].cell[{j}:{a[0]}]", show_bits(a[2]), show_bits(b[2])))
                    else:
                        sh = show_bits if a[1] == "num" else repr
                        out.append((f"table.row[{i}].cell[{j}:{a[0]}]", sh(a[2]), sh(b[2])))
    return out, ulps


# ------------------------------------------------------------------ suite-level comparison
def compare_suite(suite: dict, outputs: list[str]) -> list[dict]:
    """suite: the JSON written by suite.Suite.write; outputs: one eval_decl output per input
    (a line starting with ERROR = the input did not run). Returns one result per case."""
    parsed: dict[int, object] = {}
    results = []
    for case in suite["cases"]:
        ii = case["input"]
        inp = suite["inputs"][ii]
        res = {"id": case["id"], "primitive": case["primitive"], "note": case.get("note", ""), "diffs": [], "ulps": []}
        results.append(res)
        if ii >= len(outputs) or outputs[ii].startswith("ERROR"):
            res["status"] = "ERROR"
            res["diffs"] = [("eval", "a result", outputs[ii] if ii < len(outputs) else "missing output")]
            continue
        try:
            if ii not in parsed:
                v = parse_lean(outputs[ii])
                # carrier: "cumsum" (Np.cumsumInt, running sums; also every suite written before
                # the field existed) or "identity" (zz_carrier, the values themselves)
                cumsum = inp["mode"] in ("digest", "tokens", "bits", "ints") and inp.get("carrier", "cumsum") == "cumsum"
                parsed[ii] = undo_cumsum(v) if cumsum else v
            v = parsed[ii]
            exp = case["expected"]
            if inp["mode"] == "digest":
                want = digest(tokens(exp))
                if case["pos"] >= len(v):
                    raise ValueError(f"{len(v)} digests returned, case at position {case['pos']}")
                d, u = ([] if v[case["pos"]] == want else [("digest", want, v[case["pos"]])]), []
            elif inp["mode"] == "ints":
                if case["pos"] >= len(v):
                    raise ValueError(f"{len(v)} values returned, case at position {case['pos']}")
                d, u = ([] if v[case["pos"]] == exp and type(v[case["pos"]]) is int else [("int", exp, v[case["pos"]])]), []
            elif inp["mode"] == "bits":
                d, u = diff(exp, {"type": "col", "kind": "f64", "values": v}, case.get("ulp_tol", 0))
            elif inp["mode"] == "tokens":
                d, u = diff(exp, decode_tokens(case["kind"], v), case.get("ulp_tol", 0))
            else:
                d, u = diff(exp, dump_to_canon(case["kind"], v[case["pos"]]), case.get("ulp_tol", 0))
        except Exception as ex:  # malformed output is a failure of the case, never a pass
            res["status"] = "ERROR"
            res["diffs"] = [("parse", "well-formed output", f"{type(ex).__name__}: {ex}")]
            continue
        res["diffs"], res["ulps"] = d, u
        if case.get("expect_diff"):
            res["status"] = "XFAIL" if d else "XPASS"
        else:
            res["status"] = "FAIL" if d else ("ULP" if u else "PASS")
    return results


def main(argv: list[str]) -> int:
    suite = json.loads(Path(argv[1]).read_text())
    outputs = [ln.strip() for ln in Path(argv[2]).read_text().splitlines() if ln.strip()]
    results = compare_suite(suite, outputs)
    Path(argv[1]).with_suffix(".result.json").write_text(json.dumps(results, indent=1))
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if r["status"] != "PASS":
            print(f"{r['status']:5} {r['id']}  [{r['primitive']}] {r['note']}")
            for p, e, g in (r["diffs"] + [("ulp:" + p, e, g) for p, e, g in r["ulps"]])[:12]:
                print(f"      {p}: expected {e}  got {g}")
            extra = len(r["diffs"]) + len(r["ulps"]) - 12
            if extra > 0:
                print(f"      ... {extra} more")
    print(f"{suite['suite']}: {len(results)} cases  " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
