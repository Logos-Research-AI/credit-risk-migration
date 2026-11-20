"""Fidelity pass 2026-11-20 (label train-b): the REAL-DATA inputs of def:_kept, def:_solve_sas, def:_inv_sas and
def:_left_out, as the real port (HEAD 4a757fb) meets them on legacy/data.

1. fe.run(legacy/data, work/fz10_trainb_real, split_ids=inputs/split_ids.csv), then train.run(that, that), with
   sas_compat._kept / _solve_sas / _inv_sas / _left_out wrapped to record every call (arguments, result, caller
   line). Nothing else is changed: the wrappers call the originals.
2. Selected calls (the real run makes thousands; one eval input per call is typed by hand, so the selection is the
   calls of step 03 at the LAST stepwise step, the largest model, plus the final fit):
     _kept      train.py:208  x_k.T @ x_k of the last step
     _solve_sas train.py:234  (i0, u0) of the last step
     _left_out  sas_compat.py:841 (global_wald, train.py:239) on the last step's fit
     _inv_sas   sas_compat.py:952 the call whose result is stepwise.final.cov (the final model's covariance)
3. Each selected call is replayed alone with the REAL numpy: np.linalg.solve / np.linalg.inv are wrapped to record
   (argument bits -> result bits), and the array is viewed through an ndarray subclass whose 1-D @ 1-D records
   (operand bits -> np.matmul result). The replay must give the recorded result bit for bit (asserted).
   The Lean receives these recordings as its explicit parameters `solve`, `inv`, `dot` (RULEBOOK section 3): a
   lookup keyed by the digest of the argument bits; an argument that was never recorded returns [] / NaN, so a
   Lean that calls a routine on anything else than the real code did cannot reproduce the result.
4. The verdict is computed in Lean: each input returns [0] when the result equals the real Python result bit for
   bit (digest of length and bits, NaN canonical), else [1, digest].

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_trainb_real_gen.py
      [--rerun] runs the stages (minutes) and writes work/fz10_trainb_real.calls.pkl; then writes
      work/fz10_trainb_real.inputs.json; --show K; --cmp
"""
from __future__ import annotations

import contextlib
import io
import json
import pickle
import struct
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PTL = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train as tr  # noqa: E402

W = HERE.parent / "work"
OUT = W / "fz10_trainb_real"
DATA = PTL.parents[1] / "legacy" / "data"
SPLIT = PTL / "inputs" / "split_ids.csv"
PKL = W / "fz10_trainb_real.calls.pkl"
M64 = (1 << 64) - 1
OFF = 14695981039346656037
NANB = 0x7FF8000000000000


def fb(x):
    x = float(x)
    return NANB if x != x else struct.unpack("<Q", struct.pack("<d", x))[0]


def mx(h, x):
    g = ((h ^ x) * 1099511628211) & M64
    return g ^ (g >> 32)


def dg(toks):
    h = OFF
    for t in toks:
        h = mx(h, t & M64)
    return h


def vkey(v):
    return dg([len(v)] + [fb(x) for x in v])


def mkey(m):
    return dg([len(m)] + [t for r in m for t in [len(r)] + [fb(x) for x in r]])


# ---------------------------------------------------------------- 1. the real run, recorded
def record():
    import inspect
    calls = []
    orig = {k: getattr(sc, k) for k in ("_kept", "_solve_sas", "_inv_sas", "_left_out")}

    def wrap(name):
        f = orig[name]

        def w(*a):
            fr = inspect.stack()[1]
            res = f(*a)
            cp = [x.copy() if isinstance(x, np.ndarray) else x for x in a]
            if name == "_left_out":
                fit = a[0]
                cp = [(list(fit.names), np.array(fit.cov, dtype=np.float64).copy())]
            calls.append({"fn": name, "file": Path(fr.filename).name, "line": fr.lineno, "args": cp,
                          "res": res.copy() if isinstance(res, np.ndarray) else list(res)})
            return res
        return w
    for k in orig:
        setattr(sc, k, wrap(k))
    final_cov = {}
    o_sw = sc.stepwise_logistic

    def sw(*a, **k):
        r = o_sw(*a, **k)
        final_cov["cov"] = None if r.final is None else np.array(r.final.cov).copy()
        final_cov["steps"] = [(st.step, list(st.fit.names)) for st in r.steps]
        return r
    sc.stepwise_logistic = sw
    try:
        if OUT.exists():
            import shutil
            shutil.rmtree(OUT)
        OUT.mkdir(parents=True)
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            fe.run(DATA, OUT, split_ids=SPLIT)
            n0 = len(calls)
            tr.run(OUT, OUT)
        print("stages done in", round(time.time() - t0), "s; calls during fe", n0, "during train", len(calls) - n0)
    finally:
        for k, f in orig.items():
            setattr(sc, k, f)
        sc.stepwise_logistic = o_sw
    PKL.write_bytes(pickle.dumps({"calls": calls, "final": final_cov}))


# ---------------------------------------------------------------- 2./3. replay with recorders
class RA(np.ndarray):
    log: list = []

    def __matmul__(self, o):
        a, b = np.asarray(self), np.asarray(o)
        r = np.matmul(a, b)
        if a.ndim == 1 and b.ndim == 1:
            RA.log.append(("dot", [float(x) for x in a], [float(x) for x in b], float(r)))
        return r


def replay(fn, args):
    RA.log = []
    o_s, o_i = np.linalg.solve, np.linalg.inv

    def s(a, b):
        r = o_s(np.asarray(a), np.asarray(b))
        RA.log.append(("solve", np.asarray(a).tolist(), np.asarray(b).tolist(), np.asarray(r).tolist()))
        return r

    def i(a):
        r = o_i(np.asarray(a))
        RA.log.append(("inv", np.asarray(a).tolist(), None, np.asarray(r).tolist()))
        return r
    np.linalg.solve, np.linalg.inv = s, i
    try:
        res = getattr(sc, fn)(*[x.view(RA) if isinstance(x, np.ndarray) else x for x in args])
    finally:
        np.linalg.solve, np.linalg.inv = o_s, o_i
    return res, list(RA.log)


# ---------------------------------------------------------------- 4. Lean text
def lf(x):
    """a Float literal with the bits of x: Python's shortest round-trip repr (Lean's OfScientific Float rounds
    correctly, so the literal denotes the same double; checked for every literal by the same generator in fz5_kept,
    which matched); subnormals, zeros, NaN and infinities by bits"""
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")) or x == 0.0 or abs(x) < 2.3e-308:
        return f"(Float.ofBits {fb(x)})"
    r = repr(abs(x))
    if "e" not in r and "." not in r:
        r += ".0"
    if "e" in r:
        m, e = r.split("e")
        r = (m if "." in m else m + ".0") + "e" + str(int(e))
    return r if x > 0 else f"(-{r})"


def lvec(v):
    return "[" + ", ".join(lf(x) for x in v) + "]"


def lmat(m):
    return "[" + ", ".join(lvec(r) for r in m) + "]"


LET_DG = ("let mx := fun (h x : UInt64) => let g := (h ^^^ x) * 1099511628211; g ^^^ (g >>> 32); "
          "let fb := fun (x : Float) => if x.isNaN then (9221120237041090560 : UInt64) else x.toBits; "
          "let vk := fun (v : List Float) => (v.length.toUInt64 :: v.map fb).foldl mx 14695981039346656037; "
          "let mk := fun (m : List (List Float)) => (m.length.toUInt64 :: m.flatMap (fun (r : List Float) => r.length.toUInt64 :: r.map fb)).foldl mx 14695981039346656037; ")


def routines(log):
    sv = [(mkey(a), vkey(b), r) for k, a, b, r in log if k == "solve"]
    iv = [(mkey(a), r) for k, a, b, r in log if k == "inv"]
    dt = [(vkey(a), vkey(b), r) for k, a, b, r in log if k == "dot"]
    st = ("let ST : List (UInt64 × UInt64 × List Float) := [" + ", ".join(f"({a}, {b}, {lvec(r)})" for a, b, r in sv) + "]; "
          "let solve := fun (a : List (List Float)) (b : List Float) => ((ST.find? (fun (e : UInt64 × UInt64 × List Float) => e.1 == mk a && e.2.1 == vk b)).map (fun (e : UInt64 × UInt64 × List Float) => e.2.2)).getD []; ")
    it = ("let IT : List (UInt64 × List (List Float)) := [" + ", ".join(f"({a}, {lmat(r)})" for a, r in iv) + "]; "
          "let inv := fun (a : List (List Float)) => ((IT.find? (fun (e : UInt64 × List (List Float)) => e.1 == mk a)).map (fun (e : UInt64 × List (List Float)) => e.2)).getD []; ")
    dtt = ("let DT : List (UInt64 × UInt64 × Float) := [" + ", ".join(f"({a}, {b}, {lf(r)})" for a, b, r in dt) + "]; "
           "let dot := fun (a b : List Float) => ((DT.find? (fun (e : UInt64 × UInt64 × Float) => e.1 == vk a && e.2.1 == vk b)).map (fun (e : UInt64 × UInt64 × Float) => e.2.2)).getD (0.0 / 0.0); ")
    return st, it, dtt


def build():
    d = pickle.loads(PKL.read_bytes())
    calls, final = d["calls"], d["final"]
    sel = {}
    k208 = [c for c in calls if c["fn"] == "_kept" and c["file"] == "train.py" and c["line"] == 208]
    s234 = [c for c in calls if c["fn"] == "_solve_sas" and c["file"] == "train.py" and c["line"] == 234]
    l841 = [c for c in calls if c["fn"] == "_left_out" and c["file"] == "sas_compat.py" and c["line"] == 841]
    inv_final = [c for c in calls if c["fn"] == "_inv_sas" and final["cov"] is not None and c["res"].shape == final["cov"].shape
                 and all(fb(x) == fb(y) for x, y in zip(c["res"].ravel(), final["cov"].ravel()))]
    print("calls by fn:", {f: sum(c["fn"] == f for c in calls) for f in ("_kept", "_solve_sas", "_inv_sas", "_left_out")},
          "| step03 _kept", len(k208), "_solve_sas", len(s234), "_left_out", len(l841), "| _inv_sas giving final.cov", len(inv_final))
    print("steps", [(s, len(n)) for s, n in final["steps"]])
    sel["_kept"], sel["_solve_sas"], sel["_left_out"], sel["_inv_sas"] = k208[-1], s234[-1], l841[-1], inv_final[-1]
    out = []
    # _kept: eval on def:_solve_sas (the only evaluable item that has _kept in scope and takes a function argument):
    # solve0 computes the verdict and returns it as a 1-element vector
    c = sel["_kept"]
    a = c["args"][0]
    res, log = replay("_kept", [a])
    assert [int(x) for x in res] == [int(x) for x in c["res"]]
    st, it, dtt = routines(log)
    exp = dg([len(res)] + [int(x) for x in res])
    body = (LET_DG + st + dtt + f"let A : List (List Float) := {lmat(a.tolist())}; "
            "let k := _kept solve dot (Np.NDArray.d2 A); let h := ((k.length : Int) :: k).foldl (fun (h : UInt64) (t : Int) => mx h (UInt64.ofInt t)) 14695981039346656037; "
            f"if h == {exp} then [0.0] else [1.0, Float.ofNat (h.toNat % 4503599627370496)]")
    out.append({"unit": "_kept", "item": "def:_solve_sas", "decl": "_solve_sas", "n": a.shape[0], "py": [int(x) for x in res],
                "input": "(α := Float) (fun (_ : List (List Float)) (_ : List Float) => " + body + ") (fun (_ _ : List Float) => 0.0) (Np.NDArray.d2 [[1.0]]) (Np.NDArray.d1 [0.0])"})
    # _solve_sas: on def:_solve_sas, the same wrapping, the inner call is the real one
    c = sel["_solve_sas"]
    a, g = c["args"]
    res, log = replay("_solve_sas", [a, g])
    assert [fb(x) for x in res] == [fb(x) for x in c["res"]]
    st, it, dtt = routines(log)
    exp = vkey(list(res))
    body = (LET_DG + st + dtt + f"let A : List (List Float) := {lmat(a.tolist())}; let G : List Float := {lvec(g.tolist())}; "
            "let r := _solve_sas solve dot (Np.NDArray.d2 A) (Np.NDArray.d1 G); let h := vk r; "
            f"if h == {exp} then [0.0] else [1.0, Float.ofNat (h.toNat % 4503599627370496)]")
    out.append({"unit": "_solve_sas", "item": "def:_solve_sas", "decl": "_solve_sas", "n": a.shape[0], "kept": len(sc._kept(a)),
                "input": "(α := Float) (fun (_ : List (List Float)) (_ : List Float) => " + body + ") (fun (_ _ : List Float) => 0.0) (Np.NDArray.d2 [[1.0]]) (Np.NDArray.d1 [0.0])"})
    # _inv_sas: on def:_inv_sas, inv0 computes the verdict
    c = sel["_inv_sas"]
    a = c["args"][0]
    res, log = replay("_inv_sas", [a])
    assert [fb(x) for x in np.asarray(res).ravel()] == [fb(x) for x in c["res"].ravel()]
    st, it, dtt = routines(log)
    exp = mkey(np.asarray(res).tolist())
    body = (LET_DG + st + it + dtt + f"let A : List (List Float) := {lmat(a.tolist())}; "
            "let r := _inv_sas inv solve dot (Np.NDArray.d2 A); let h := mk r; "
            f"if h == {exp} then [[0.0]] else [[1.0, Float.ofNat (h.toNat % 4503599627370496)]]")
    out.append({"unit": "_inv_sas", "item": "def:_inv_sas", "decl": "_inv_sas", "n": a.shape[0], "kept": len(sc._kept(a)),
                "input": "(fun (_ : List (List Float)) => " + body + ") (fun (_ : List (List Float)) (b : List Float) => b) (fun (_ _ : List Float) => (0.0 : Float)) (Np.NDArray.d2 [[1.0]])"})
    # _left_out: on def:_left_out itself (List String prints exactly): the real fit's names and cov
    names, cov = c2 = sel["_left_out"]["args"][0]
    pyres = sel["_left_out"]["res"]
    assert pyres == [n for i, n in enumerate(names) if float(cov[i, i]) == 0.0]
    out.append({"unit": "_left_out", "item": "def:_left_out", "decl": "_left_out", "n": len(names), "py": pyres,
                "input": "({ names := [" + ", ".join(json.dumps(n) for n in names) + "], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 "
                         + lmat(cov.tolist()) + ", loglik := 0.0, n_iter := 0, converged := true } : LogisticFit Float)"})
    for o in out:
        print(o["unit"], o["item"], "n", o["n"], "chars", len(o["input"]), {k: v for k, v in o.items() if k in ("py", "kept")})
    (W / "fz10_trainb_real.inputs.json").write_text(json.dumps(out))


def main():
    if sys.argv[1:2] == ["--show"]:
        print(json.loads((W / "fz10_trainb_real.inputs.json").read_text())[int(sys.argv[2])]["input"])
        return
    if sys.argv[1:2] == ["--cmp"]:
        ins = json.loads((W / "fz10_trainb_real.inputs.json").read_text())
        outs = (W / "fz10_trainb_real.out.txt").read_text().splitlines()
        res = []
        for c, o in zip(ins, outs):
            if c["unit"] == "_left_out":
                ok = json.loads(o) == c["py"]
            else:
                ok = o.replace(" ", "") in ("[0.000000]", "[[0.000000]]")
            res.append((c["unit"], ok))
        print(json.dumps({"compared": len(res), "differences": sum(not ok for _, ok in res), "per_unit": res}))
        return
    if sys.argv[1:2] == ["--rerun"] or not PKL.exists():
        record()
    build()


if __name__ == "__main__":
    main()
