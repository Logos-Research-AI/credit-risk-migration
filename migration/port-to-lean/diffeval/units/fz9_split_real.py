"""Real-data evaluation of def:fe_run_06_split after port commit 4a757fb (T0, 2026-11-19).

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz9_split_real.py build
      -> diffeval/work/fz9_split_real.inputs.json (eval_decl: item def:zz_carrier_e, decl dg_frame2)
         diffeval/work/fz9_split_real.expected.json
  ... python diffeval/units/fz9_split_real.py compare   (outputs, one line per input, in fz9_split_real.out.txt)

credit_features: the REAL port's run() body up to the split (feature_engineering.py:28-351, executed
verbatim, returning credit_features) on the first n lines of legacy/data/cs-training.csv.
Split file: the real split file (inputs/split_ids.csv, 105,000 ids) restricted to the ids of those n
rows, in the file's order. Expected: the REAL lines 352-370 on the real CSV bytes of that file.
The frame is cut to 4 of its 42 columns (row_id, default_flag, age, monthly_income) to keep the eval
input small; the unit filters every column alike. Cases: n = 10 (8 ids, n_train 7: does not fit, drawn), n = 20 (14 ids = n_train: fits), n = 12
(8 ids, n_train 9: drawn). The full file (105,000 ids) on a small frame does not fit by its count
alone; it is run on the Python side only (the eval input would hold 105,000 ids).
"""
from __future__ import annotations

import io
import json
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402

ROOT = HERE.parents[3]
WORK = HERE.parent / "work"
LINES = Path(fe.__file__).read_text().splitlines(keepends=True)
assert LINES[27].startswith("def run(") and LINES[351].lstrip().startswith("file_ids = ("), (LINES[27], LINES[351])
RUN_HEAD = compile("".join(LINES[27:351]) + "    return credit_features\n", f"{fe.__file__}:28-351", "exec")
SPLIT = compile(textwrap.dedent("".join(LINES[351:370])), f"{fe.__file__}:352-370", "exec")
REAL_SPLIT = (HERE.parent.parent / "inputs" / "split_ids.csv").read_bytes()


def features(n: int) -> pl.DataFrame:
    d = WORK / f"fz9_real_{n}"
    d.mkdir(parents=True, exist_ok=True)
    raw = (ROOT / "legacy" / "data" / "cs-training.csv").read_text().splitlines(keepends=True)
    (d / "cs-training.csv").write_text("".join(raw[: n + 1]))
    ns = dict(vars(fe))
    exec(RUN_HEAD, ns)  # noqa: S102
    return ns["run"](d, d / "out", split_ids=d / "unused.csv")


def split(cf: pl.DataFrame, data: bytes):
    ns = dict(vars(fe))
    ns["split_ids"] = io.BytesIO(data)
    ns["credit_features"] = cf
    exec(SPLIT, ns)  # noqa: S102
    return ns["credit_train"], ns["credit_validation"], ns["file_ids"]


def restricted(cf: pl.DataFrame) -> tuple[bytes, list[float]]:
    have = set(cf.get_column("row_id").to_list())
    lines = REAL_SPLIT.decode().splitlines()
    keep = [ln for ln in lines[1:] if float(ln) in have]
    return ("row_id\n" + "".join(k + "\n" for k in keep)).encode(), [float(k) for k in keep]


def build():
    inputs, exp, notes = [], [], []
    for n in (10, 20, 12):
        cf = features(n).select(["row_id", "default_flag", "age", "monthly_income"])  # 4 of the 42 columns (input size)
        data, ids = restricted(cf)
        tr, va, used = split(cf, data)
        nt = (7 * cf.height + 9) // 10
        table = "[" + ", ".join(f'[("row_id", Tabular.Cell.num (some {lt.lean_float(x)}))]' for x in ids) + "]"
        inputs.append(f"(fe_run_06_split (α := Float) {table} {lt.lean_frame(cf)})")
        exp.append([cmp.digest(cmp.tokens(cmp.canon_frame(tr))), cmp.digest(cmp.tokens(cmp.canon_frame(va)))])
        notes.append({"n": n, "height": cf.height, "cols": cf.width, "file_ids": len(ids), "n_train": nt,
                      "fits": used == ids, "train": tr.get_column("row_id").to_list(),
                      "validation": va.get_column("row_id").to_list()})
        # the full real file on the same frame (Python side only)
        trf, vaf, usedf = split(cf, REAL_SPLIT)
        notes[-1]["full_file"] = {"fits": len(usedf) == 105000, "train": trf.get_column("row_id").to_list()}
    (WORK / "fz9_split_real.inputs.json").write_text(json.dumps(
        [{"item": "def:zz_carrier_e", "decl": "dg_frame2", "text": t} for t in inputs], indent=1))
    (WORK / "fz9_split_real.expected.json").write_text(json.dumps({"expected": exp, "notes": notes}, indent=1))
    for x in notes:
        print(x)
    print("input chars", [len(t) for t in inputs])


def compare():
    exp = json.loads((WORK / "fz9_split_real.expected.json").read_text())["expected"]
    lines = [ln for ln in (WORK / "fz9_split_real.out.txt").read_text().splitlines() if ln.strip()]
    res = [json.loads(ln) == e for ln, e in zip(lines, exp, strict=True)]
    (WORK / "fz9_split_real.result.json").write_text(json.dumps(res))
    print(res)


if __name__ == "__main__":
    build() if sys.argv[1] == "build" else compare()
