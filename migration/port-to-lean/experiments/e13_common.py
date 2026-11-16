"""Shared helper of experiments e13 to e17 (2026-11-16): run the port's real stages on given files and
keep what each stage held at its end (the locals of `run`) and what it wrote."""
from __future__ import annotations
import contextlib, io, struct, sys
from pathlib import Path
from credit_risk import feature_engineering as fe, metrics_calculation as mc, predict as pr, train as tr

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
REAL = ROOT / "legacy" / "data"
SPLIT = HERE / "inputs" / "split_ids.csv"
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731
CODES = {fe.run.__code__: "fe", tr.run.__code__: "train", mc.run.__code__: "metrics", pr.run.__code__: "predict"}


def head_rows(path: Path, n: int) -> str:
    """The header and the first n data lines of a file, as text."""
    with path.open(newline="") as fh:
        return "".join(line for _, line in zip(range(n + 1), fh))


def run_stages(d: Path, train_text: str | None, test_text: str | None, split: Path, stages=("fe", "train", "metrics", "predict")):
    """Runs the named stages with data folder d/data and output folder d/out. Returns (status, locals, files) per stage:
    status 'completed' or the exception; files = what the output folder holds after the stage (name to bytes)."""
    dd, out = d / "data", d / "out"
    dd.mkdir(parents=True, exist_ok=True)
    if train_text is not None:
        (dd / "cs-training.csv").write_text(train_text, newline="")
    if test_text is not None:
        (dd / "cs-test.csv").write_text(test_text, newline="")
    calls = {"fe": lambda: fe.run(dd, out, split_ids=split), "train": lambda: tr.run(out, out), "metrics": lambda: mc.run(out, out),
             "predict": lambda: pr.run(out, out, data_dir=dd, income_medians=out / "income_medians.csv")}
    locs, status, files = {}, {}, {}

    def prof(frm, ev, arg):
        if ev in ("return", "exception") and frm.f_code in CODES:
            locs[CODES[frm.f_code]] = dict(frm.f_locals)

    for s in stages:
        buf = io.StringIO()
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(buf):
                calls[s]()
            status[s] = "completed"
        except BaseException as e:  # noqa: BLE001
            status[s] = f"RAISED {type(e).__name__}: {str(e)[:160]}"
        finally:
            sys.setprofile(None)
        files[s] = {p.name: p.read_bytes() for p in sorted(out.glob("*"))} if out.exists() else {}
    return status, locs, files


def new_files(files, order=("fe", "train", "metrics", "predict")):
    """Per stage: the files that appeared or changed during it, with their line counts."""
    prev, res = {}, {}
    for s in order:
        if s not in files:
            continue
        cur = files[s]
        res[s] = {n: b.count(b"\n") for n, b in cur.items() if prev.get(n) != b}
        gone = [n for n in prev if n not in cur]
        if gone:
            res[s]["(removed)"] = gone
        prev = cur
    return res
