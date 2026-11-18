"""Evaluation inputs for def:logistic_no_fit, def:logit_scored_train_output_nofit and
def:logit_scored_valid_temp_nofit (2026-11-18): print one eval_decl input term per call, built
from a staged feature CSV. Every cell of these files is a present number, so each row is the
header zipped with a list of Float literals (nearest binary64, R27). Nothing is saved."""
import csv, re, sys


def lit(t):
    t = t.strip()
    neg = t.startswith('-')
    u = t[1:] if neg else t
    if re.fullmatch(r"\d+", u):
        s = u
    elif re.fullmatch(r"\d*\.\d*", u):
        s = '0' + u if u.startswith('.') else u
        s = s + '0' if s.endswith('.') else s
    else:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)[eE]([+-]?\d+)", u)
        if not m:
            raise ValueError(t)
        s = f"{m.group(1) if '.' in m.group(1) else m.group(1) + '.0'}e{int(m.group(2))}"
    return f"(-{s})" if neg else s


def tree(xs, chunk=8):
    # a long list literal overflows the evaluator's recursion limit (diffeval.lean_table)
    if len(xs) <= chunk:
        return "[" + ", ".join(xs) + "]"
    h = len(xs) // 2
    return "(List.append " + tree(xs[:h], chunk) + " " + tree(xs[h:], chunk) + ")"


def table(path, mode=""):
    rows = list(csv.reader(open(path)))
    hdr, body = rows[0], [list(r) for r in rows[1:]]
    for r in body:
        assert len(r) == len(hdr) and all(v.strip() != '' for v in r)
    if mode == "flip_last":  # contrast case: default_flag of the last row set to 1
        body[-1][hdr.index("default_flag")] = "1"
    if mode == "empty":
        body = []
    h = "[" + ", ".join('"%s"' % c for c in hdr) + "]"
    rs = ["mk [" + ", ".join(lit(v) for v in r) + "]" for r in body]
    return ("(let h : List String := " + h + "; let mk : List Float → Tabular.Row Float := "
            "fun vs => (h.zip vs).map (fun p => (p.1, Tabular.Cell.num (some p.2))); "
            "(" + (tree(rs) if rs else "[]") + " : Tabular.Table Float))")


if __name__ == "__main__":
    print("(α := Float) " + table(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""))
