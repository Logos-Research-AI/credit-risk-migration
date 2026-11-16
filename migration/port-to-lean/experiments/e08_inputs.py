"""E08 (2026-11-16): how the port meets its inputs, on VALID files. Real runs only.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e08_inputs.py > experiments/e08_inputs.out.txt

Part 1  sas_compat.proc_import_csv(path, guessingrows=None) on valid raw files, compared field by
        field with the text of the file (split on LF and on commas: valid files have no quotes).
Part 2  the header-only test file: `test_raw` of the real predict.run (profile hook on its locals).
Part 3  the files one stage writes and the next reads: the frame handed to write_sas_csv against
        the frame proc_import_csv returns for the same path, inside real runs of the four stages.
Part 4  the four stages in order: which input files exist before each stage, whether an import
        returned a frame, whether a stage stopped.
"""
from __future__ import annotations
import contextlib, io, re, struct, sys, tempfile
from pathlib import Path
import polars as pl
from credit_risk import feature_engineering as fe, train as tr, metrics_calculation as mc, predict as pr
from credit_risk import sas_compat as sc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SC = ROOT / "judge" / "scenarios"
SPLIT = HERE.parent / "inputs" / "split_ids.csv"
NUM = re.compile(sc._NUM_RE)
bits = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]  # noqa: E731


# ------------------------------------------------------------------ part 1
def describe(label: str, path: Path, show: bool = True) -> dict:
    text = path.read_bytes().decode()
    crlf = "\r\n" in text
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    header = lines[0].split(",")
    rows = [ln.split(",") for ln in lines[1:]]
    short = sum(1 for r in rows if len(r) != len(header))
    rows = [r + [""] * (len(header) - len(r)) for r in rows]
    f = sc.proc_import_csv(path, guessingrows=None)
    exp_names = [(h if h != "" else f"VAR{i + 1}")[:32] for i, h in enumerate(header)]
    res = {"names_ok": f.columns == exp_names, "height_ok": f.height == len(rows), "rule_ok": True, "cells_ok": True}
    kinds = []
    for j, n in enumerate(f.columns):
        fields = [r[j] for r in rows]
        stated = [v for v in fields if v != ""]
        pred = "Float64" if stated and all(NUM.match(v.strip()) for v in stated) else "String"
        got = str(f.schema[n])
        res["rule_ok"] &= pred == got
        col = f.get_column(n).to_list()
        if got == "Float64":
            ok = all((c is None and v == "") or (c is not None and v != "" and bits(c) == bits(float(v))) for c, v in zip(col, fields, strict=True))
        else:
            ok = all((c is None and v == "") or (c == v and v != "") for c, v in zip(col, fields, strict=True))
        res["cells_ok"] &= ok
        nblank = sum(v == "" for v in fields)
        nna = sum(v == "NA" for v in fields)
        nint = sum(bool(re.fullmatch(r"[+-]?\d+", v)) for v in fields)
        other = sorted({v for v in stated if not NUM.match(v.strip())} - {"NA"})[:4]
        kinds.append(f"{n}:{got}[blank={nblank},NA={nna},integers={nint},other={len(stated) - nna - nint}{',text=' + repr(other) if other else ''}{',null=' + str(f.get_column(n).null_count())}]")
    if show:
        print(f"{label}: data lines={len(rows)} frame height={f.height} crlf={crlf} short rows={short} "
              f"names={'as header (first empty -> VAR1, cut to 32)' if res['names_ok'] else 'DIFFER'} "
              f"kind rule={'holds' if res['rule_ok'] else 'FAILS'} cells in file order={'equal' if res['cells_ok'] else 'DIFFER'}")
        print("   " + " ".join(kinds))
    return res


print("== PART 1: proc_import_csv(guessingrows=None) on valid raw files")
print("   per column: kind [blank fields, NA fields, integer-looking fields, other stated fields, nulls in the frame]")
print("   kind rule tested: Float64 iff at least one field is not blank and every non-blank field is a number; else String")
print("   cells tested: Float64 cell == float(field) bit for bit, null iff blank; String cell == field text, null iff blank")
VALID = [("legacy/data", ROOT / "legacy/data"), ("fix2/good", SC / "fix2/good"), ("fix2/valid_unusual", SC / "fix2/valid_unusual"),
         ("fix2/q13_median_width", SC / "fix2/q13_median_width"), ("fix2/q14_negative_real", SC / "fix2/q14_negative_real"),
         ("fix_G34/income_zero", SC / "fix_G34/income_zero"), ("fix_round5/good", SC / "fix_round5/good"),
         ("fix_round5/train_age_exponent", SC / "fix_round5/train_age_exponent"), ("fix_round5/test_age_exponent", SC / "fix_round5/test_age_exponent"),
         ("fix_Q27_emptytest/good", SC / "fix_Q27_emptytest/good"), ("fix_Q27_textid/good", SC / "fix_Q27_textid/good"),
         ("fix_Q1", SC / "fix_Q1"), ("fix_Q13", SC / "fix_Q13"), ("fix_Q14", SC / "fix_Q14"), ("fix_Q7", SC / "fix_Q7"), ("fix_Q9", SC / "fix_Q9"),
         ("edge_predict", SC / "edge_predict")]
allok = True
for name, d in VALID:
    for fn in ("cs-training.csv", "cs-test.csv"):
        r = describe(f"{name}/{fn}", d / fn)
        allok &= all(r.values())
print("PART 1 all files: names, heights, kind rule, cells:", "ALL HOLD" if allok else "SOME FAIL")

print("-- variants made from legacy/data lines (verbatim lines, chosen by content)")
L = (ROOT / "legacy/data/cs-training.csv").read_text().split("\n")
hdr, data = L[0], [x for x in L[1:] if x]
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "v.csv"
    def variant(label, lines):
        p.write_text("\n".join([hdr] + lines) + "\n")
        describe(label, p)
    noNA = [x for x in data if "NA" not in x][:2000]
    variant("training, no NA in any line (2000 lines)", noNA)
    incNA = [x for x in data if x.split(",")[6] == "NA" and x.split(",")[11] != "NA"][:50] + noNA[:500]
    variant("training, NA only in MonthlyIncome", incNA)
    variant("training, NA lines with NA replaced by a blank field", [",".join("" if v == "NA" else v for v in x.split(",")) for x in data[:2000]])
    variant("training, MonthlyIncome written with a decimal point (5700 -> 5700.0) and no NA", [",".join((v + ".0") if i == 6 else v for i, v in enumerate(x.split(","))) for x in noNA[:500]])
    variant("training, every NumberOfDependents blank", [",".join("" if i == 11 else v for i, v in enumerate(x.split(","))) for x in data[:500]])
    variant("training, one data line", data[:1])


# ------------------------------------------------------------------ parts 2, 3, 4
def pipeline(label: str, train_dir: Path, test_dir: Path, detail: bool = True) -> None:
    written: dict[str, pl.DataFrame] = {}
    read: dict[str, pl.DataFrame] = {}
    locs: dict[str, dict] = {}
    o_w, o_r = sc.write_sas_csv, sc.proc_import_csv

    def w(df, path, formats=None):
        written[Path(path).name] = df.clone()
        return o_w(df, path, formats)

    def r(path, guessingrows=20):
        out = o_r(path, guessingrows)
        read[f"{Path(path).name}@{guessingrows}"] = out.clone()
        return out

    codes = {fe.run.__code__: "fe", tr.run.__code__: "train", mc.run.__code__: "metrics", pr.run.__code__: "predict"}

    def prof(frm, ev, arg):
        if ev in ("return", "exception") and frm.f_code in codes:
            locs[codes[frm.f_code]] = dict(frm.f_locals)

    print(f"\n== PIPELINE {label}: training file {train_dir.relative_to(ROOT)}, test file {test_dir.relative_to(ROOT)}")
    with tempfile.TemporaryDirectory() as d:
        dd, out = Path(d) / "data", Path(d) / "out"
        dd.mkdir()
        (dd / "cs-training.csv").write_bytes((train_dir / "cs-training.csv").read_bytes())
        (dd / "cs-test.csv").write_bytes((test_dir / "cs-test.csv").read_bytes())
        sc.write_sas_csv, sc.proc_import_csv = w, r
        sys.setprofile(prof)
        stages = [
            ("feature_engineering", [dd / "cs-training.csv"], lambda: fe.run(dd, out, split_ids=SPLIT)),
            ("train", [out / "model_features_train.csv", out / "model_features_validation.csv"], lambda: tr.run(out, out)),
            ("metrics", [out / "risk_scores_validation.csv", out / "risk_scores_train.csv"], lambda: mc.run(out, out)),
            ("predict", [out / "income_medians.csv", out / "model_coefficients.csv", out / "model.json", dd / "cs-test.csv"],
             lambda: pr.run(out, out, data_dir=dd, income_medians=out / "income_medians.csv")),
        ]
        try:
            for name, needs, call in stages:
                ex = {p.name: p.exists() for p in needs}
                err = None
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        call()
                except Exception as e:  # noqa: BLE001
                    err = f"{type(e).__name__}: {str(e)[:100]}"
                print(f"PART 4 {name}: inputs exist before the stage {ex}; stage {'STOPPED/RAISED ' + err if err else 'completed'}")
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.proc_import_csv = o_w, o_r
        cr = locs.get("fe", {}).get("credit_raw")
        tw = locs.get("predict", {}).get("test_raw")
        print(f"PART 4 imports: credit_raw is {'None' if cr is None else 'a frame'}; test_raw is {'None' if tw is None else 'a frame'}; "
              f"read back: {sorted(read)}")
        if tw is not None:
            print(f"PART 2 test_raw of predict.run: height={tw.height} test_lines={locs['predict'].get('test_lines')} "
                  f"columns={[(n, str(t)) for n, t in tw.schema.items()]}")
            for fn in ("kaggle_submission.csv", "test_predictions.csv"):
                if fn in written:
                    print(f"PART 2 written {fn}: height={written[fn].height} columns={written[fn].columns}")
    if not detail:
        return
    for fn, g in (("model_features_train.csv", None), ("model_features_validation.csv", None), ("risk_scores_validation.csv", 20),
                  ("risk_scores_train.csv", 20), ("income_medians.csv", 20)):
        key = f"{fn}@{g}"
        if fn not in written or key not in read:
            print(f"PART 3 {fn}: written={fn in written} read={key in read}")
            continue
        W, R = written[fn], read[key]
        head = f"PART 3 {fn} (read with guessingrows={g}): written {W.height} x {W.width}, read {R.height} x {R.width}; names and order {'equal' if W.columns == R.columns else 'DIFFER'}"
        same, diffs = [], []
        for n in W.columns:
            if n not in R.columns:
                diffs.append(f"{n}: not read back")
                continue
            ws, rs = W.get_column(n), R.get_column(n)
            wk = "str" if ws.dtype == pl.String else "num"
            rk = "str" if rs.dtype == pl.String else "num"
            wl = ws.to_list() if wk == "str" else ws.cast(pl.Float64).to_list()
            rl = rs.to_list()
            if len(wl) != len(rl):
                diffs.append(f"{n}: lengths {len(wl)} / {len(rl)}")
                continue
            if wk == rk == "num":
                bad = [(a, b) for a, b in zip(wl, rl, strict=True) if not ((a is None and b is None) or (a is not None and b is not None and (bits(a) == bits(b) or a == b == 0)))]
                nullchg = sum(1 for a, b in bad if (a is None) != (b is None))
                if not bad:
                    same.append(n)
                else:
                    rel = max((abs(a - b) / abs(a) for a, b in bad if a is not None and b is not None and a != 0 and a == a), default=0.0)
                    diffs.append(f"{n} ({ws.dtype}->{rs.dtype}): {len(bad)} of {len(wl)} cells differ, {nullchg} null/value changes, max relative difference {rel:.3g}, e.g. written {bad[0][0]!r} read {bad[0][1]!r}")
            elif wk == rk == "str":
                bad = [(a, b) for a, b in zip(wl, rl, strict=True) if a != b]
                (same if not bad else diffs).append(n if not bad else f"{n} (String): {len(bad)} cells differ, e.g. written {bad[0][0]!r} read {bad[0][1]!r}")
            else:
                ex = next(((a, b) for a, b in zip(wl, rl, strict=True) if a is not None or b is not None), (None, None))
                diffs.append(f"{n}: KIND written {ws.dtype} read {rs.dtype}; nulls written {ws.null_count()} read {rs.null_count()}; e.g. written {ex[0]!r} read {ex[1]!r}")
        print(head)
        print(f"   identical columns ({len(same)}): {same}")
        for x in diffs:
            print("   DIFF " + x)


print("\n== PARTS 2-4: the four stages in order, real runs")
pipeline("legacy", ROOT / "legacy/data", ROOT / "legacy/data")
pipeline("fix2/good", SC / "fix2/good", SC / "fix2/good")
pipeline("fix2/valid_unusual", SC / "fix2/valid_unusual", SC / "fix2/valid_unusual")
pipeline("fix_G34/income_zero", SC / "fix_G34/income_zero", SC / "fix_G34/income_zero")
pipeline("fix2/q13_median_width", SC / "fix2/q13_median_width", SC / "fix2/q13_median_width")
pipeline("fix_round5/good", SC / "fix_round5/good", SC / "fix_round5/good", detail=False)
pipeline("fix_Q27_emptytest/good", SC / "fix_Q27_emptytest/good", SC / "fix_Q27_emptytest/good", detail=False)
pipeline("header-only test file (LF)", SC / "fix_Q27_emptytest/header_only", SC / "fix_Q27_emptytest/header_only", detail=False)
pipeline("header-only test file (CR LF)", SC / "fix_Q27_emptytest/crlf_header_only", SC / "fix_Q27_emptytest/crlf_header_only", detail=False)
pipeline("header-only test file (no line end)", SC / "fix_Q27_emptytest/header_only_noterminator", SC / "fix_Q27_emptytest/header_only_noterminator", detail=False)
pipeline("legacy training, header-only test", ROOT / "legacy/data", SC / "fix_Q27_emptytest/header_only", detail=False)
