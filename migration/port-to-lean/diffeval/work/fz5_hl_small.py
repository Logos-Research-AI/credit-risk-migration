"""Small direct run for def:hosmer_lemeshow(_precond) via def:train_run_07_hl with bit-encoding formatters
(no carrier item exists on the blueprint any more). Usage: python fz5_hl_small.py gen | show"""
import sys, json, math, struct
from pathlib import Path
import numpy as np, polars as pl
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "port"))
from credit_risk import sas_compat as sc
nan, inf = float("nan"), float("inf"); nx = math.nextafter
def bits(x): return struct.unpack("<Q", struct.pack("<d", float(x)))[0]
class Chi2:
    @staticmethod
    def sf(x, df): return float(x) / (float(df) + 3.0)
sc.chi2 = Chi2
def lf(x):
    return "none" if x is None else f"(some (Float.ofBits {bits(x)}))"
def col(xs): return "(Pl.Col.f64 [" + ", ".join(lf(x) for x in xs) + "])"
FW = '(fun (x : Option Float) (a b : Int) => (match x with | none => "N" | some v => toString v.toBits.toNat : String) ++ "/" ++ toString a ++ "/" ++ toString b)'
PV = '(fun (x : Option Float) => (match x with | none => "N" | some v => toString v.toBits.toNat : String))'
CH = '(fun (x : Float) (d : Int) => x / (Float.ofInt d + 3.0))'
P2 = '(fun (x : Float) => x * x)'
def term(y, p):
    return f'{FW} {PV} {CH} {P2} [("default_flag", {col(y)}), ("pd_logistic", {col(p)})] ["x"]'
def enc(x): return "N" if x is None else str(bits(x))
def pre(y, p):
    """new precondition on raw values (no 2^52 bounds)"""
    d = [(a, b) for a, b in zip(y, p) if a is not None and b is not None]
    if not d: return True
    n = len(d)
    p0 = np.array([b for _, b in d]); y0 = np.array([a for a, _ in d])
    o = np.argsort(p0, kind="stable"); pp, yy = p0[o], y0[o]
    blocks, i = [], 0
    while i < n:
        j = int(pp.searchsorted(float(pp[i]) + 1e-6, side="right")); blocks.append(j - i); i = j
    st = np.concatenate([[0], np.cumsum(blocks)[:-1]]).astype(np.int64)
    pp = np.repeat(pp[st], blocks)
    s = 0
    for size in sc._hl_groups(blocks, n, 10):
        o1 = float(yy[s:s+size].sum())
        avg = float(pp[s:s+size].sum()) / size
        lo = 1e-6 if 1e-6 > avg else avg; hi = 0.999999 if 0.999999 < lo else lo
        e1 = size * hi; s += size; o0, e0 = size - o1, size - e1
        if not math.isfinite(o1) or math.floor(o1) != o1: return False
        for x in (o1 - e1, o0 - e0):
            if math.isfinite(x) and not math.isfinite(x * x): return False
    return True
def expect(y, p):
    try:
        t, c, dof, pv = sc.hosmer_lemeshow(pl.Series(y, dtype=pl.Float64), pl.Series(p, dtype=pl.Float64))
    except Exception as e:
        return f"RAISE {type(e).__name__}: {str(e)[:50]}"
    if t.height < 3: return "NOFILES"
    rows = ["/".join(str(v) for v in (r[0], r[1], bits(float(r[2])), bits(r[3]), bits(float(r[4])), bits(r[5]))) for r in t.iter_rows()]
    return {"chisq": enc(c), "dof": dof, "pv": enc(pv), "ng": t.height, "rows": rows}
def ramp(n, f): return [f(i) for i in range(n)]
B = 2.0**52; C = 2.0**53
CASES = {
 "ramp20": (ramp(20, lambda i: float(i % 2)), ramp(20, lambda i: (i+1)/21)),
 "ties": ([1.0,0.0]*10, [0.2]*7+[0.5]*6+[0.8]*7),
 "chain+1e-6": ([1.0,0.0,0.0,1.0]*5, [0.3+1e-6*(i%3) for i in range(20)]),
 "chain+1e-6+ulp": ([1.0,0.0]*10, [0.3, nx(0.3+1e-6,1)]*10),
 "chain+1e-6-ulp": ([1.0,0.0]*10, [0.3, nx(0.3+1e-6,0)]*5+[0.6]*10),
 "nan_pd": ([1.0,0.0]*10, [0.1,nan,0.3,0.4,0.5,0.6,nan,0.8,0.9,0.2]*2),
 "null_rows": ([1.0,None,0.0,1.0]*6, [0.1*(i%9+1) if i%5 else None for i in range(24)]),
 "inf_pd": ([1.0,0.0]*10, [inf,-inf,0.5,0.4,0.3,0.2,0.1,0.6,0.7,0.8]*2),
 "pd_gt1_lt0": ([1.0,0.0]*10, [2.0,-1.0,1.5,-0.5,0.5,0.4,0.3,0.2,0.7,0.8]*2),
 "negzero": ([1.0,0.0]*10, [-0.0,0.0]*5+[0.5]*10),
 "pd_all0": ([1.0,0.0]*10, [0.0]*20),
 "pd_all1": ([1.0,0.0]*10, [1.0]*20),
 "pd_1e-6": ([1.0,0.0]*10, [1e-6]*5+[0.5]*10+[0.999999]*5),
 "y_big53": ([C,1.0,0.0,0.0]*5, ramp(20, lambda i: (i+1)/21)),
 "y_big52+1": ([B+1,1.0,0.0,0.0]*5, ramp(20, lambda i: (i+1)/21)),
 "y_big2^53+2": ([C+2,1.0,0.0,0.0]*5, ramp(20, lambda i: (i+1)/21)),
 "y_2^62": ([2.0**62,0.0]*10, ramp(20, lambda i: (i+1)/21)),
 "y_2^62_single": ([2.0**62]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_2^63": ([2.0**63]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_-2^63": ([-2.0**63]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_2^64": ([2.0**64]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_1e300": ([1e300]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_-2^62": ([-2.0**62]+[1.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_2^62+1k": ([2.0**62, 1.0, 1.0, 0.0]*5, ramp(20, lambda i: (i+1)/21)),
 "y_cancel": ([C, -C, 1.0, 0.0]*5, ramp(20, lambda i: (i+1)/21)),
 "y_inf": ([inf]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_nan": ([nan]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "y_half": ([0.5]+[0.0]*19, ramp(20, lambda i: (i+1)/21)),
 "n3": ([1.0,0.0,1.0], [0.2,0.5,0.8]),
 "n1": ([1.0], [0.5]),
 "n2": ([1.0,0.0], [0.5,0.6]),
 "n0": ([], []),
 "all_null_pd": ([1.0,0.0], [None, None]),
 "n10": ([1.0,0.0]*5, ramp(10, lambda i: (i+1)/11)),
 "n11": ([1.0,0.0]*5+[1.0], ramp(11, lambda i: (i+1)/12)),
 "n100": (ramp(100, lambda i: float(i%3==0)), ramp(100, lambda i: ((i*37)%100+0.5)/100)),
 "y_all1": ([1.0]*20, ramp(20, lambda i: (i+1)/21)),
 "y_all0": ([0.0]*20, ramp(20, lambda i: (i+1)/21)),
}
if __name__ == "__main__":
    out = {}
    for k, (y, p) in CASES.items():
        out[k] = {"pre": pre(y, p), "exp": expect(y, p), "in": term(y, p)}
    Path(__file__).with_name("fz5_hl_small.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        e = v["exp"]; print(k, v["pre"], e if isinstance(e, str) else (e["ng"], e["dof"]))
