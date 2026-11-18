"""fz3_p08, all-seeds form: Lean evaluates every seed 0..N-1 (short input: no seed list); this script holds the expected
digests of every seed (the real predict.py lines), the precondition verdict pre08, and compares an out file.

  generate:  python diffeval/units/fz3_p08_all.py gen [N [chunks]]  -> work/fz3_p08_all.expected.json, work/fz3_p08_all.inputs.txt
  compare:   python diffeval/units/fz3_p08_all.py cmp work/fz3_p08_all.out.txt   (one line per input: a JSON list of ints)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz3_p08_gen as g  # noqa: E402

WORK = HERE.parent / "work"


def gen(n, chunks):
    exp = []
    for s in range(n):
        df, an = g.mk(s)
        ok = g.pre08(df, an)
        try:
            a, b = g.real(df, an)
            da, db = g.cmp.digest(g.toks(a)), g.cmp.digest(g.toks(b))
            err = None
        except Exception as e:  # noqa: BLE001
            da = db = None
            err = f"{type(e).__name__}: {e}"
        exp.append({"s": s, "pre": ok, "da": da, "db": db, "err": err, "cols": df.columns, "age_name": an, "h": df.height})
    (WORK / "fz3_p08_all.expected.json").write_text(json.dumps(exp))
    step = -(-n // chunks)
    texts = []
    for c in range(chunks):
        lo, hi = c * step, min(n, (c + 1) * step)
        body = (f"((List.range {hi - lo}).flatMap (fun (i : Nat) => let s := i + {lo}; "
                "let r := predict_run_08_outputs (α := Float) (FR s) (ANS s); [dg (tR r.1), dg (tR r.2)]))")
        texts.append("(" + g.kit.KIT_NOTABLE + g.kit.GEN + g.LETS + body + ")")
    (WORK / "fz3_p08_all.inputs.json").write_text(json.dumps(texts, ensure_ascii=False))
    print(n, "seeds;", sum(e["pre"] for e in exp), "inside the precondition;", [len(t) for t in texts])


def cmpf(out):
    exp = json.loads((WORK / "fz3_p08_all.expected.json").read_text())
    got = []
    for line in Path(out).read_text().splitlines():
        got += json.loads(line)
    assert len(got) == 2 * len(exp), (len(got), len(exp))
    kept = diffs = 0
    outside_ran = outside_diff = 0
    for e in exp:
        la, lb = got[2 * e["s"]], got[2 * e["s"] + 1]
        if e["err"] is None:
            same = (la == e["da"], lb == e["db"])
        else:
            same = (None, None)
        if e["pre"]:
            kept += 1
            if same != (True, True):
                diffs += 1
                print("DIFF", e["s"], same, e["cols"], e["age_name"], e["h"])
        elif e["err"] is None:
            outside_ran += 1
            if same != (True, True):
                outside_diff += 1
                print("OUTSIDE-DIFF", e["s"], same, [c for c in e["cols"] if not c.isascii()], e["age_name"])
    print("kept", kept, "diffs", diffs, "outside-precondition where python ran", outside_ran, "differing", outside_diff)


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(int(sys.argv[2]) if len(sys.argv) > 2 else 3273, int(sys.argv[3]) if len(sys.argv) > 3 else 2)
    else:
        cmpf(sys.argv[2])
