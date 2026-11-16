"""Seed 20912 of fz_psi: the Lean values (typed from the eval_decl result of the locating call) against Python."""
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "units"))
sys.path.insert(0, str(HERE.parent))
import fz_psi_gen as fz


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


LEAN = {
    "train_pct": [4595010527915232284, 4590506928287861788, 4594036776644449474, 4587950831202056912, 4594036776644449474,
                  4590506928287861788, 4587950831202056912, 4595984279186015094, 4587950831202056912, 4587950831202056912],
    "valid_pct": [0, 4602678819172646912, 0, 0, 0, 0, 0, 4602678819172646912, 0, 0],
    "psi_component": [4600325742689927151, 4605039424948649538, 4598716446528780061, 4588260256410711655, 4598716446528780061,
                      4593388060963654686, 4588260256410711655, 4599113135164957944, 4588260256410711655, 4588260256410711655],
}
LEAN_PSI = 4612450460026286012
t, v, meta = fz.frames(20912)
pc, ps = fz.run_slice(t, v)
for c, lean in LEAN.items():
    py = [bits(x) for x in pc[c].to_list()]
    print(c, "equal" if py == lean else [(i, p - q) for i, (p, q) in enumerate(zip(py, lean)) if p != q])
psi = ps.item(0, "PSI")
print("PSI python", repr(psi), bits(psi), "lean", LEAN_PSI, "ulps", bits(psi) - LEAN_PSI)
comp = pc["psi_component"].to_list()
acc = 0.0
for x in comp:
    acc += x
print("left fold from 0.0", bits(acc) - bits(psi), "fsum", bits(math.fsum(comp)) - bits(psi), "pl sum", bits(pc["psi_component"].sum()) - bits(psi))
# a minimal case: the ten components alone, summed by polars
import polars as pl
from credit_risk import sas_compat as sc
d = pl.DataFrame({"x": comp})
print("select sum", bits(d.select(pl.col("x").sum()).item()) - bits(acc), "sql_sum", bits(d.select(sc.sql_sum(pl.col("x"))).item()) - bits(acc),
      "sorted frame sum", bits(d.sort("x").select(pl.col("x").sum()).item()) - bits(math.fsum([0.0]) + sum(sorted(comp))))
print("components", [repr(x) for x in comp])
