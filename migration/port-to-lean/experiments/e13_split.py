"""E13 (2026-11-16): R3, the split file of feature engineering (argument split_ids of feature_engineering.run).

  PYTHONPATH=../../port uv run --project ../../port python experiments/e13_split.py > experiments/e13_split.out.txt

Real fe.run on training files made of the first n data lines of the real training file (ids 1 to n in the
first column) and on the real file; the split file is the real one (inputs/split_ids.csv) or a variant.
What is compared: credit_features, credit_train, credit_validation as fe.run holds them at its end.
"""
from __future__ import annotations
import tempfile
from pathlib import Path
import polars as pl
from e13_common import REAL, SPLIT, head_rows, run_stages

real_ids = [int(x) for x in SPLIT.read_text().split()[1:]]
print(f"real split file: header {SPLIT.read_text().splitlines()[0]!r}, {len(real_ids)} ids, distinct {len(set(real_ids))}, min {min(real_ids)}, max {max(real_ids)}, "
      f"all whole numbers written with digits only: {all(x.isdigit() for x in SPLIT.read_text().split()[1:])}, sorted: {real_ids == sorted(real_ids)}")


def fe_run(train_text, split_text=None, split_path=None, want=None):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        sp = split_path or (d / "split.csv")
        if split_text is not None:
            sp.write_text(split_text, newline="")
        status, locs, files = run_stages(d, train_text, None, sp, stages=("fe",))
        L = locs.get("fe", {})
        F, T, V = L.get("credit_features"), L.get("credit_train"), L.get("credit_validation")
        res = {"status": status["fe"], "files": {n: b.count(b"\n") for n, b in files["fe"].items()}}
        if T is not None and V is not None:
            fid = F.get_column("row_id").to_list()
            sel = L["train_ids"].to_list()
            selset = set(sel)
            exp_t = F.filter(pl.Series([i in selset for i in fid], dtype=pl.Boolean))
            exp_v = F.filter(pl.Series([i is not None and i not in selset for i in fid], dtype=pl.Boolean))
            res.update(n=F.height, train=T.height, validation=V.height, train_ids=T.get_column("row_id").to_list(), val_ids=V.get_column("row_id").to_list(),
                       partition=T.equals(exp_t, null_equal=True) and V.equals(exp_v, null_equal=True) and T.height + V.height == F.height,
                       same_columns=T.columns == F.columns == V.columns, id_kind=str(F.schema["row_id"]), split_kind=str(L["train_ids"].dtype), split_len=len(sel))
        return res


print("\n== sizes with the real split file, training file = first n data lines of the real file (first column 1 to n)")
for n in list(range(1, 21)) + [50, 100, 1000]:
    r = fe_run(head_rows(REAL / "cs-training.csv", n), split_path=SPLIT)
    exp = sum(1 for i in real_ids if i <= n)
    print(f"   n={n:>4}: {r['status']}; train {r.get('train')} validation {r.get('validation')}; ids of the real split file at most n: {exp}; "
          f"train ids {r.get('train_ids') if n <= 20 else '...'}; partition in file order: {r.get('partition')}; files {r['files']}")
r = fe_run((REAL / "cs-training.csv").read_text(), split_path=SPLIT)
print(f"   real file: {r['status']}; rows {r['n']}; train {r['train']} validation {r['validation']}; partition in file order: {r['partition']}; same columns in both sets as in credit_features: {r['same_columns']}; "
      f"row_id kind {r['id_kind']}; split ids kind {r['split_kind']}; files {r['files']}")
print(f"   real file: train row_id increasing: {r['train_ids'] == sorted(r['train_ids'])}; validation row_id increasing: {r['val_ids'] == sorted(r['val_ids'])}")

T20 = head_rows(REAL / "cs-training.csv", 20)
print("\n== split file variants, training file = first 20 data lines")
variants = {
    "ids 1,3,5 (column row_id only)": "row_id\n1\n3\n5\n",
    "ids in another order 5,1,3": "row_id\n5\n1\n3\n",
    "an id twice: 1,3,3,5": "row_id\n1\n3\n3\n5\n",
    "ids of no applicant too: 1,3,5,999,150001": "row_id\n1\n3\n5\n999\n150001\n",
    "only ids of no applicant: 999,1000": "row_id\n999\n1000\n",
    "every id 1 to 20": "row_id\n" + "".join(f"{i}\n" for i in range(1, 21)),
    "header only": "row_id\n",
    "header only, no line end": "row_id",
    "empty file (0 bytes)": "",
    "row_id second of three columns": "a,row_id,b\nx,1,y\nx,3,y\nx,5,y\n",
    "no row_id column (named id)": "id\n1\n3\n5\n",
    "name in capitals ROW_ID": "ROW_ID\n1\n3\n5\n",
    "quoted header and ids": '"row_id"\n"1"\n"3"\n"5"\n',
    "CRLF line ends": "row_id\r\n1\r\n3\r\n5\r\n",
    "no final line end": "row_id\n1\n3\n5",
    "a blank line between ids": "row_id\n1\n\n3\n5\n",
    "blank id in a two-column file": "row_id,b\n1,x\n,x\n5,x\n",
    "id written 3.0": "row_id\n1\n3.0\n5\n",
    "id written 3.7": "row_id\n1\n3.7\n5\n",
    "id with a space ' 3'": "row_id\n1\n 3\n5\n",
    "id written +3": "row_id\n1\n+3\n5\n",
    "id written 03": "row_id\n1\n03\n5\n",
    "id written 1e0": "row_id\n1e0\n3\n5\n",
    "id text abc": "row_id\n1\nabc\n5\n",
    "negative id -3": "row_id\n1\n-3\n5\n",
    "id beyond 64-bit integers": "row_id\n1\n99999999999999999999\n5\n",
}
for label, text in variants.items():
    r = fe_run(T20, split_text=text)
    print(f"   {label:44}: {r['status'][:150]}" + (f"; split ids read {r['split_len']}; train {r['train']} {r['train_ids']} validation {r['validation']}; partition in file order: {r['partition']}; files {r['files']}" if 'train' in r else f"; files {r['files']}"))
r = fe_run(T20, split_path=Path("/nonexistent/split.csv"))
print(f"   {'file absent':44}: {r['status'][:150]}; files {r['files']}")

print("\n== the first column of the training file is the id matched, not the position of the row")
lines = T20.splitlines(keepends=True)


def reid(ids):
    return lines[0] + "".join(f"{i}," + ln.split(",", 1)[1] for i, ln in zip(ids, lines[1:], strict=True))


for label, ids in {"ids 101 to 120": list(range(101, 121)), "ids 20 down to 1": list(range(20, 0, -1)), "ids 5,3,1 first then 21 up": [5, 3, 1] + list(range(21, 38)),
                   "an id twice in the training file (3,3)": [1, 3, 3] + list(range(4, 21)), "id 3.5 in the training file": [1, 2, "3.5"] + list(range(4, 21)),
                   "blank id in the training file": [1, 2, ""] + list(range(4, 21))}.items():
    r = fe_run(reid(ids), split_text="row_id\n1\n3\n5\n103\n")
    print(f"   {label:44}: {r['status'][:150]}" + (f"; train {r['train']} {r['train_ids']} validation {r['validation']} {r['val_ids']}; partition in file order: {r['partition']}" if 'train' in r else ""))
