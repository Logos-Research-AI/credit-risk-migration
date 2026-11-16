"""E09 (2026-11-16): the files one stage writes and the next reads, exactly. Real runs of the four
stages (valid input); write_sas_csv and proc_import_csv are wrapped to keep the frame written and
the frame read for the same file name; nothing of the stages is copied.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e09_readback.py > experiments/e09_readback.out.txt

A  for every file read back: per column, written dtype -> read dtype, nulls, and the test
   read == float(render(written)) cell for cell, where render is what write_sas_csv prints
   (sas_best12 for a Float64 column, str(int) for an integer column, sas_best(x, 32) for the two
   medians, fmt_percent(x, 8, 2) for interest_rate, read as text).
B  the String columns: their values and lengths, and what the first 20 rows hold (the files read
   with guessingrows=20 size a text column on those rows).
C  a valid training file (legacy lines, reordered) whose first 20 scored rows hold only the
   shortest texts: what the next stage reads.
"""
from __future__ import annotations
import contextlib, io, struct, sys, tempfile
from pathlib import Path
import polars as pl
from credit_risk import feature_engineering as fe, train as tr, metrics_calculation as mc, predict as pr
from credit_risk import sas_compat as sc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SC = ROOT / "judge" / "scenarios"
SPLIT = HERE.parent / "inputs" / "split_ids.csv"
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731
FILES = (("model_features_train.csv", None), ("model_features_validation.csv", None), ("risk_scores_validation.csv", 20),
         ("risk_scores_train.csv", 20), ("income_medians.csv", 20))


def pipeline(train_text: str, test_text: str):
    written, read, status = {}, {}, []
    o_w, o_r = sc.write_sas_csv, sc.proc_import_csv

    def w(df, path, formats=None):
        written[Path(path).name] = (df.clone(), dict(formats or {}))
        return o_w(df, path, formats)

    def r(path, guessingrows=20):
        out = o_r(path, guessingrows)
        read[Path(path).name] = out.clone()
        return out

    with tempfile.TemporaryDirectory() as d:
        dd, out = Path(d) / "data", Path(d) / "out"
        dd.mkdir()
        (dd / "cs-training.csv").write_text(train_text)
        (dd / "cs-test.csv").write_text(test_text)
        sc.write_sas_csv, sc.proc_import_csv = w, r
        try:
            for name, call in (("feature_engineering", lambda: fe.run(dd, out, split_ids=SPLIT)), ("train", lambda: tr.run(out, out)),
                               ("metrics", lambda: mc.run(out, out)),
                               ("predict", lambda: pr.run(out, out, data_dir=dd, income_medians=out / "income_medians.csv"))):
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        call()
                    status.append(f"{name}: completed")
                except Exception as e:  # noqa: BLE001
                    status.append(f"{name}: {type(e).__name__}: {str(e)[:70]}")
        finally:
            sc.write_sas_csv, sc.proc_import_csv = o_w, o_r
    return written, read, status


def render(s: pl.Series, fmt: str | None) -> list[str]:
    """the text write_sas_csv prints for the column (its own renderer)"""
    return sc._render_column(s, fmt)


def part_a(label, written, read):
    for fn, g in FILES:
        if fn not in written or fn not in read:
            print(f"A {label} {fn}: written={fn in written} read={fn in read}")
            continue
        (W, fm), R = written[fn], read[fn]
        print(f"A {label} {fn} (guessingrows={g}): written {W.height} x {W.width}, read {R.height} x {R.width}, names/order {'equal' if W.columns == R.columns else 'DIFFER'}, formats={fm}")
        groups: dict[str, list[str]] = {}
        for n in W.columns:
            ws, rs = W.get_column(n), R.get_column(n)
            txt = render(ws, fm.get(n))
            if rs.dtype == pl.String:
                ok = all((b is None and t == "") or b == t for t, b in zip(txt, rs.to_list(), strict=True))
                law = "read text == printed text, null iff printed empty"
            else:
                ok = all((b is None and t == "") or (b is not None and t != "" and bits(b) == bits(float(t))) for t, b in zip(txt, rs.to_list(), strict=True))
                law = "read == float(printed text) bit for bit, null iff printed empty"
            if ws.dtype == pl.String:
                same = ws.to_list() == rs.to_list()
            elif rs.dtype == pl.String:
                same = False
            else:
                same = all((a is None and b is None) or (a is not None and b is not None and bits(a) == bits(b)) for a, b in zip(ws.cast(pl.Float64).to_list(), rs.to_list(), strict=True))
            key = f"{ws.dtype}->{rs.dtype} fmt={fm.get(n)} | {law}: {'HOLDS' if ok else 'FAILS'} | read == written cell for cell: {'yes' if same else 'NO'}"
            groups.setdefault(key, []).append(f"{n}(nulls {ws.null_count()}/{rs.null_count()})")
        for k, v in groups.items():
            print(f"   {k}\n      {' '.join(v)}")


def part_b(label, written, read):
    for fn in ("risk_scores_validation.csv", "risk_scores_train.csv", "model_features_train.csv", "income_medians.csv"):
        if fn not in written:
            continue
        W, R = written[fn][0], read.get(fn)
        for n in W.columns:
            s = W.get_column(n)
            if s.dtype == pl.String:
                vals = sorted({v for v in s.to_list() if v is not None})
                first = sorted({v for v in s.head(20).to_list() if v is not None})
                print(f"B {label} {fn} String column {n}: values {[(v, len(v)) for v in vals]}; in the first 20 rows {first}; nulls {s.null_count()}")
        nulls20 = [n for n in W.columns if W.get_column(n).head(20).null_count() == min(20, W.height) and W.height > 0]
        print(f"B {label} {fn}: columns with no value in the first 20 rows: {nulls20}; numeric columns holding a null anywhere: {[n for n in W.columns if W.get_column(n).dtype != pl.String and W.get_column(n).null_count() > 0]}")


train_text = (ROOT / "legacy/data/cs-training.csv").read_text()
test_text = (ROOT / "legacy/data/cs-test.csv").read_text()
for label, a, b in (("legacy", train_text, test_text),
                    ("fix2/good", (SC / "fix2/good/cs-training.csv").read_text(), (SC / "fix2/good/cs-test.csv").read_text()),
                    ("fix_Q1 training (an age group with no known income)", (SC / "fix_Q1/cs-training.csv").read_text(), (SC / "fix_Q1/cs-test.csv").read_text())):
    W, R, st = pipeline(a, b)
    print(f"== {label}: {st}")
    part_a(label, W, R)
    part_b(label, W, R)
    if label == "legacy":
        LEG = (W, R)
    if "income_medians.csv" in W:
        print(f"   income_medians written: {W['income_medians.csv'][0].rows()}  read: {R['income_medians.csv'].rows() if 'income_medians.csv' in R else None}")

# ---- C: reorder legacy lines so that the first 20 rows of each scored set hold the shortest texts
W, R = LEG
print("== C: legacy lines reordered (a valid file: same lines, same ids, other order)")
for fn in ("risk_scores_train.csv", "risk_scores_validation.csv"):
    pass
rt, rv = W["risk_scores_train.csv"][0], W["risk_scores_validation.csv"][0]
strcols = [n for n in rt.columns if rt.get_column(n).dtype == pl.String]
print("String columns of the scored sets:", strcols)
# shortest value of the widest-varying text column, rows that hold it
def short_ids(fr, col):
    lens = fr.get_column(col).str.len_chars()
    mn = lens.min()
    return fr.filter(lens == mn).get_column("row_id").head(40).to_list(), mn, lens.max()
target = max(strcols, key=lambda c: (rt.get_column(c).str.len_chars().max() - rt.get_column(c).str.len_chars().min()))
ids_t, mn, mx = short_ids(rt, target)
ids_v, _, _ = short_ids(rv, target)
print(f"column chosen: {target} (lengths {mn}..{mx}); rows moved to the top: {len(ids_t)} training, {len(ids_v)} validation")
lines = train_text.split("\n")
hdr, data = lines[0], [x for x in lines[1:] if x]
front = {int(i) for i in ids_t + ids_v}
re_text = "\n".join([hdr] + [x for x in data if int(x.split(",")[0]) in front] + [x for x in data if int(x.split(",")[0]) not in front]) + "\n"
W2, R2, st = pipeline(re_text, test_text)
print("stages:", st)
part_a("reordered", W2, R2)
for fn in ("risk_scores_validation.csv", "risk_scores_train.csv"):
    if fn in W2 and fn in R2:
        ws, rs = W2[fn][0].get_column(target), R2[fn].get_column(target)
        bad = [(a, b) for a, b in zip(ws.to_list(), rs.to_list(), strict=True) if a != b]
        print(f"C {fn} {target}: first 20 written {sorted(set(ws.head(20).to_list()))}; cells read differently: {len(bad)} of {ws.len()}; e.g. {bad[:3]}")
