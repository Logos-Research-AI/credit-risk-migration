"""Fidelity pass 2026-11-20, third attempt (label train-c): receipts in receipts/fuzz_2026-11-20c-train-c.tsv.

  cd migration/port-to-lean && python3 diffeval/units/fz10c_train_c_receipt.py

1. Prefixes the scope of each generated suite (current Lean vs current port HEAD 4a757fb, carrier, stand-ins)
   to the note of work/<suite>.fuzz.json (idempotent), then runs fuzz_receipt.py on fz10c_cv fz10c_ct fz10c_ctw.
2. Adds one row per real-data suite (fz10c_cv_real, fz10c_ctr: no generator seeds, so no .fuzz.json), from the
   compared work/<suite>.json + .result.json, with the exact reason the whole real call is not evaluated.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = HERE.parent
W = D / "work"
TSVN = "fuzz_2026-11-20c-train-c.tsv"
TSV = D / "receipts" / TSVN
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
FUZZER = "port-translator (fidelity pass 2026-11-20 third attempt, train-c)"
TAG = "[train-c scope] "

SCOPE = {
    "fz10c_cv": TAG + "Lean of the CURRENT item def:train_run_11_confusion_valid evaluated through the carrier "
    "def:zz_carrier_fid_2 vs the CURRENT port/credit_risk/train.py (HEAD 4a757fb) lines 640-700, sliced by text "
    "markers and executed. No stand-in routine (the step calls none). Digest of the tokens of input + "
    "confusion_matrix + validation_metrics per seed, blocks of 600 seeds per Lean call, generated inside Lean "
    "(hsh) and mirrored in Python. ",
    "fz10c_ct": TAG + "Lean of the CURRENT item def:train_run_08_ctable through def:zz_carrier_fid_2 vs the "
    "CURRENT train.py (HEAD 4a757fb) lines 479-535 executed. Explicit parameters (RULEBOOK section 3) as "
    "injective/simple stand-ins identical on both sides: FMT (bits of the float, w, d), INV (a at [0][0], 0 "
    "elsewhere), SOLVE (Cramer 1x1 / 2x2), DOT, MATMUL, MATVEC, EINSUM (sequential loops), LOG1P = log(1+x). "
    "Blocks of 650 seeds per Lean call. ",
    "fz10c_ctw": TAG + "Supplement for def:train_run_08_ctable with the EXACT routines of the model: Gaussian "
    "elimination with partial pivoting (fz4_cim_gen.LEAN) for solve, sequential @ and einsum loops "
    "(fz4_cim_gen.NA, NPXE), wide designs of 2-5 predictors. Blocks of 350 seeds. ",
}


def scope_notes() -> None:
    for s, pre in SCOPE.items():
        p = W / f"{s}.fuzz.json"
        f = json.loads(p.read_text())
        for u in f["units"].values():
            if not u.get("note", "").startswith(TAG):
                u["note"] = pre + u.get("note", "")
        f["fuzzer"] = FUZZER
        p.write_text(json.dumps(f, indent=1))


REAL = {
    "fz10c_cv_real": ("train_run_11_confusion_valid", "real rows 0..44999 in 4 windows",
        "REAL input: logit_scored_valid of the real train.run on legacy/data (work/fz10c_real.pkl, captured by "
        "fz10c_real_capture.py; 45000 x 44, real confusion 41521/461/2412/606) projected on the two columns the "
        "step reads (default_flag Float64, pred_logistic Int64; asserted in fz10c_real11_gen.py that the slice "
        "gives the same confusion_matrix and validation_metrics on the projection as on the full frame and as the "
        "real run). Every real row is evaluated, in 4 consecutive windows (0-11999, 12000-23999, 24000-35999, "
        "36000-44999), each a real input in its own right, digests of input, confusion_matrix, validation_metrics. "
        "NOT REACHED: the whole 45000-row frame in one call: eval_decl timed out on it (the unit's Lean is "
        "superlinear in rows under eval_decl: 2000 rows 0.4 s, 12000 rows 2.8 s, 24000 rows 31 s)."),
    "fz10c_ctr": ("train_run_08_ctable", "real rows 0..39 and 104960..104999",
        "REAL rows of the real step 08 input (fit_frame 105000 x 15 predictors + Intercept, final names, y_train, "
        "pd_logistic of logit_scored_train, from work/fz10c_real.pkl) in two windows of 40 rows (27 and 43 "
        "levels), EXACT routines (Gaussian solve, sequential @, einsum loop), the fit's covariance reduced to its "
        "diagonal (the generator asserts the Python result is identical with the full covariance). "
        "NOT REACHED: the real call itself (105000 rows x 16 columns, about 1.7M floats, far beyond an eval_decl "
        "input; and the smaller step 11 already times out at 45000 x 2)."),
}


def real_rows() -> list[str]:
    out = []
    for s, (unit, seeds, note) in REAL.items():
        cs = json.loads((W / f"{s}.json").read_text())["cases"]
        rs = json.loads((W / f"{s}.result.json").read_text())
        if len(cs) != len(rs):
            raise SystemExit(f"{s}: stale result, rerun compare.py")
        diff = sum(r["status"] not in ("PASS",) for r in rs)
        st = "PASS" if diff == 0 else "DIFF (FINDING)"
        note2 = TAG + f"{note} Cases {len(rs)} digests, PASS {len(rs) - diff}. Carrier def:zz_carrier_fid_2, port HEAD 4a757fb."
        gen = "migration/port-to-lean/diffeval/units/" + ("fz10c_real11_gen.py" if s == "fz10c_cv_real" else "fz10c_ctw_gen.py")
        out.append("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in (
            unit + " [real data]", FUZZER, seeds, len(rs), len(rs), "1.000", len(rs), diff, 0, 0, st, note2, BP, gen)))
    return out


def main() -> int:
    scope_notes()
    env = {**os.environ, "FUZZ_RECEIPTS": TSVN}
    subprocess.run([sys.executable, str(D / "fuzz_receipt.py"), "fz10c_cv", "fz10c_ct", "fz10c_ctw"], env=env, check=True)
    lines = TSV.read_text().splitlines()
    head, rows = lines[0], [r for r in lines[1:] if not r.split("\t")[0].endswith("[real data]")]
    rows += real_rows()
    TSV.write_text("\n".join([head, *rows]) + "\n")
    for r in rows:
        print(r[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
