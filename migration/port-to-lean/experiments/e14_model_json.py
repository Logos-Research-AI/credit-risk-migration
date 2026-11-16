"""E14 (2026-11-16): R4, model.json written by train and read back by predict.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e14_model_json.py > experiments/e14_model_json.out.txt

Real four-stage runs. Compared: `intercept` and `coefficients` as train.run holds them at its end, the text of
model.json, and `intercept` and `coefficients` as predict.run holds them at its end (bit for bit, names, order).
The real run's folders are kept under experiments/work_e14 for e15.
"""
from __future__ import annotations
import json, math, random, shutil, struct, tempfile
from pathlib import Path
from e13_common import HERE, REAL, ROOT, SPLIT, bits, run_stages

SC = ROOT / "judge" / "scenarios"
KEEP = HERE / "experiments" / "work_e14"


def one(label, train_dir, test_dir, d):
    tt = (train_dir / "cs-training.csv").read_text()
    te = (test_dir / "cs-test.csv").read_text()
    status, locs, files = run_stages(d, tt, te, SPLIT)
    print(f"\n== {label}: {status}")
    if status["train"] != "completed":
        print("   train did not complete; model.json exists:", "model.json" in files["train"])
        return
    T = locs["train"]
    ti, tc = T["intercept"], T["coefficients"]
    raw = files["train"]["model.json"].decode()
    j = json.loads(raw)
    print(f"   train: intercept type {type(ti).__name__}; coefficients type {type(tc).__name__} of {len(tc)}; value types {sorted({type(v).__name__ for v in tc.values()})}; "
          f"all finite: {math.isfinite(ti) and all(math.isfinite(v) for v in tc.values())}")
    print(f"   model.json: {len(raw)} characters, top-level keys {list(j)}; intercept text reads as {type(j['intercept']).__name__}; "
          f"coefficient names equal and in the same order as train's: {list(j['coefficients']) == list(tc)}")
    print(f"   model.json parsed == train's values bit for bit: intercept {bits(float(j['intercept'])) == bits(float(ti))}, "
          f"coefficients {all(bits(float(j['coefficients'][k])) == bits(float(tc[k])) for k in tc)}")
    print(f"   names in order: {list(tc)}")
    if status["predict"] == "completed" or "coefficients" in locs.get("predict", {}):
        P = locs["predict"]
        pi, pc = P["intercept"], P["coefficients"]
        print(f"   predict: intercept type {type(pi).__name__}, coefficients {type(pc).__name__}, value types {sorted({type(v).__name__ for v in pc.values()})}")
        print(f"   predict's model == train's model: intercept bit for bit {bits(pi) == bits(float(ti))}; names and order {list(pc) == list(tc)}; "
              f"every coefficient bit for bit {all(bits(pc[k]) == bits(float(tc[k])) for k in tc)}")
        cols = P["test_features"].columns
        print(f"   every coefficient name is a column of predict's scoring frame: {all(k in cols for k in pc)}")
    mcv = files["train"].get("model_coefficients.csv", b"").decode().splitlines()
    print(f"   (model_coefficients.csv, the other file train writes about the model: {len(mcv)} lines, header {mcv[0] if mcv else None!r})")


if KEEP.exists():
    shutil.rmtree(KEEP)
KEEP.mkdir(parents=True)
one("real data", REAL, REAL, KEEP)
for s, tr_, te_ in [("fix2/good", None, None), ("fix_round5/good", None, None), ("fix_G34/income_zero", None, None), ("fix_Q13", None, None), ("fix_Q14", None, None),
                    ("fix_Q7", None, None), ("fix_Q9", None, None), ("fix_Q27_textid/good", None, None), ("fix_round5/train_age_exponent", None, None)]:
    a = SC / s
    trd = a if (a / "cs-training.csv").exists() else REAL
    ted = a if (a / "cs-test.csv").exists() else REAL
    with tempfile.TemporaryDirectory() as d:
        one(f"{s} (training file from {'the scenario' if trd == a else 'the real data'}, test file from {'the scenario' if ted == a else 'the real data'})", trd, ted, Path(d))

print("\n== the text form itself: float(json.loads(json.dumps(x))) == x bit for bit")
rng = random.Random(3)
xs = [struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))[0] for _ in range(1_000_000)]
xs = [x for x in xs if math.isfinite(x)] + [0.0, -0.0, 5e-324, 2.2250738585072014e-308, 1.7976931348623157e308, 0.1, 1 / 3, 1e22, 1e23, -1e-7, 123456789.0, 1.0, -2.0]
back = json.loads(json.dumps({"c": xs}))["c"]
print("   finite doubles tried:", len(xs), "changed:", sum(1 for a, b in zip(xs, back, strict=True) if bits(float(b)) != bits(a)))
print("   whole-valued doubles are written with '.0' and read as float:", json.dumps(3.0), type(json.loads(json.dumps(3.0))).__name__)
d = {"b": 1.0, "a": 2.0, "Intercept": 3.0, "z y": 4.0}
print("   key order kept:", list(json.loads(json.dumps(d))) == list(d))
for x in (float("nan"), float("inf"), -float("inf")):
    t = json.dumps(x)
    print(f"   non-finite {x!r}: written {t!r}, read back {json.loads(t)!r}")
