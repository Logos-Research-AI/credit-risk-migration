"""Check the PORT (credit_risk.sas_compat) against the SAS logs of X07 and X08 (finding P1).
Usage (repo root): uv run python migration/experiments/x07_port_check.py"""

import json
import re
import struct
from pathlib import Path

import polars as pl

from credit_risk import sas_compat

HERE = Path(__file__).parent


def unhex(h: str) -> float | None:
    return None if set(h) <= {"."} else struct.unpack(">d", bytes.fromhex(h))[0]


def series(rows: list[tuple[float, int]]) -> tuple[pl.Series, pl.Series]:
    return pl.Series([float(y) for _, y in rows]), pl.Series([p for p, _ in rows], dtype=pl.Float64)


text = re.sub(
    r"\n(?=(StdErr|LowerArea|UpperArea|SomersD|Gamma|TauA|Label2|nValue\d)=)", " ", (HERE / "x07_roc_ties.log").read_text()
)
roc = {int(m["g"]): m for m in (dict(re.findall(r"(\w+)=(\S+)", ln)) for ln in text.splitlines() if ln.startswith("X07 roc "))}
groups = json.loads((HERE / "x07_groups.json").read_text())
cols = {"Area": "area", "StdErr": "std_err", "LowerArea": "lower", "UpperArea": "upper", "SomersD": "somers_d", "Gamma": "gamma", "TauA": "tau_a"}
exact = dict.fromkeys(cols, 0)
worst = dict.fromkeys(cols, 0.0)
for g in groups:
    r = sas_compat.roc_association(*series([(unhex(p) or 0.0, y) for p, y in g["rows"]]))
    for c, attr in cols.items():
        port, sas = getattr(r, attr), unhex(roc[g["g"]][c])
        if port == sas:
            exact[c] += 1
        elif port is None or sas is None:
            worst[c] = float("inf")
        else:
            worst[c] = max(worst[c], abs(port - sas))
print(f"X07 A+B: {len(groups)} BY groups; port roc_association against SAS ROCAssociation")
for c in cols:
    print(f"  {c:10s} bit-exact {exact[c]:3d}/{len(groups)}   largest difference {worst[c]:.3g}")

g8 = json.loads((HERE / "x08_groups.json").read_text())
a8 = {int(a): float(b) for a, b in re.findall(r"^X08 roc g=(\d+) Area=(\S+)", (HERE / "x08_roceps_boundary.log").read_text(), re.M)}
ok = 0
for g in g8:
    rows = [(unhex(g["v"]) or 0.0, 0), (unhex(g["top"]) or 0.0, 1), (0.9, 1), (0.95, 0)]
    ok += sas_compat.roc_association(*series(rows)).area == a8[g["g"]]
print(f"X08: port Area equals SAS on {ok}/{len(g8)} boundary groups")

for seed in (1, 2, 3, 4):
    rows, assoc = [], {}
    for ln in text.splitlines():
        if ln.startswith(f"X07 C{seed} row "):
            kv = dict(re.findall(r"(\w+)=(\S+)", ln))
            rows.append((unhex(kv["p"]) or 0.0, int(kv["y"])))
        elif ln.startswith(f"X07 C{seed} assoc "):
            m = re.match(r"X07 C\d assoc Label1=(.+?) nValue1=(\S+) nValue1=\S+ Label2=(.+?) nValue2=(\S+)", ln)
            assert m
            assoc[m.group(1)], assoc[m.group(3)] = unhex(m.group(2)), unhex(m.group(4))
    t = sas_compat.association_table(*series(rows))
    port = {"Percent Concordant": t.concordant_pct, "Percent Discordant": t.discordant_pct, "Percent Tied": t.tied_pct,
            "Pairs": float(t.pairs), "Somers' D": t.somers_d, "Gamma": t.gamma, "Tau-a": t.tau_a, "c": t.c}
    print(f"X07 C seed {seed}: " + ", ".join(f"{k} {'exact' if port[k] == assoc[k] else f'off {port[k] - assoc[k]:.2g}'}" for k in port))
