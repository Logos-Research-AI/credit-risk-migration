"""E15 (2026-11-16): R5, a valid test file whose SeriousDlqin2yrs column is not all blank.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e15_test_target.py > experiments/e15_test_target.out.txt

Needs experiments/work_e14 (made by e14: the real run's output folder with the model and the medians).
Real predict.run on the real test file with only the SeriousDlqin2yrs field of each line rewritten.
Compared with the all-blank file: the bytes of every file predict writes; and the kind of the column in test_raw.
"""
from __future__ import annotations
import contextlib, io, sys, tempfile
from pathlib import Path
from credit_risk import predict as pr
from e13_common import HERE, REAL, head_rows

MODEL = HERE / "experiments" / "work_e14" / "out"
full = (REAL / "cs-test.csv").read_text()
head, *rows = full.splitlines(keepends=True)
print("real test file: data lines", len(rows), "; distinct SeriousDlqin2yrs texts:", sorted({r.split(",")[1] for r in rows}))


def retarget(rs, f):
    out = [head]
    for i, r in enumerate(rs):
        a = r.split(",")
        a[1] = f(i)
        out.append(",".join(a))
    return "".join(out)


def predict(text):
    locs = {}

    def prof(frm, ev, arg):
        if ev in ("return", "exception") and frm.f_code is pr.run.__code__:
            locs.update(frm.f_locals)

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "data").mkdir()
        (d / "data" / "cs-test.csv").write_text(text, newline="")
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                pr.run(MODEL, d / "out", data_dir=d / "data", income_medians=MODEL / "income_medians.csv")
            st = "completed"
        except BaseException as e:  # noqa: BLE001
            st = f"RAISED {type(e).__name__}: {str(e)[:100]}"
        finally:
            sys.setprofile(None)
        files = {p.name: p.read_bytes() for p in sorted((d / "out").glob("*"))} if (d / "out").exists() else {}
    tr_ = locs.get("test_raw")
    kind = None if tr_ is None else str(tr_.schema.get("SeriousDlqin2yrs"))
    nn = None if tr_ is None else tr_.get_column("SeriousDlqin2yrs").null_count()
    return st, files, kind, nn, (None if tr_ is None else tr_.height)


for title, rs in (("the real test file (101503 lines)", rows), ("its first 15 lines (fewer than 20)", rows[:15]), ("its first line only", rows[:1])):
    print(f"\n== {title}")
    st0, base, k0, n0, h0 = predict(retarget(rs, lambda i: ""))
    print(f"   all blank (as the real file): {st0}; column kind {k0}, nulls {n0} of {h0}; files written {dict((n, b.count(chr(10).encode())) for n, b in base.items())}")
    n = len(rs)
    variants = {
        "all NA": lambda i: "NA",
        "all 0": lambda i: "0",
        "all 1": lambda i: "1",
        "0 and 1 alternating": lambda i: str(i % 2),
        "blank, 0, 1, NA in turn": lambda i: ["", "0", "1", "NA"][i % 4],
        "NA, 1, 0, blank in turn": lambda i: ["NA", "1", "0", ""][i % 4],
        "blank on the first 30 lines, then 0/1": lambda i: "" if i < 30 else str(i % 2),
        "NA on the first 30 lines, then 0/1": lambda i: "NA" if i < 30 else str(i % 2),
        "0/1 on the first 30 lines, then NA": lambda i: str(i % 2) if i < 30 else "NA",
        "0/1 on the first 30 lines, then blank": lambda i: str(i % 2) if i < 30 else "",
        "only the last line holds 1": lambda i: "1" if i == n - 1 else "",
        "only the last line holds NA": lambda i: "NA" if i == n - 1 else "",
        "only the first line holds NA": lambda i: "NA" if i == 0 else "",
    }
    for label, f in variants.items():
        st, files, k, nn, h = predict(retarget(rs, f))
        same = st == st0 and files.keys() == base.keys() and all(files[x] == base[x] for x in base)
        print(f"   {label:40}: {st}; column kind {k}, nulls {nn} of {h}; every written file byte-identical to the all-blank run: {same}")
    for label, f in {"(not valid) a 2 on line 5": lambda i: "2" if i == 4 else "", "(not valid) text 'yes' on line 5": lambda i: "yes" if i == 4 else ""}.items():
        st, files, k, nn, h = predict(retarget(rs, f))
        print(f"   {label:40}: {st}; column kind {k}; files written {sorted(files)}")
