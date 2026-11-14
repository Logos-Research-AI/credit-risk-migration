"""Build the eval_decl inputs of a differential test suite and the expected Python results.

A suite is a list of inputs (Lean terms, each one eval_decl case) and a list of cases (one
compared value each). Kinds of input (CARRIER = the suite's carrier, see below):
  digest  CARRIER:  (KIT GEN <lets> [dg t1, dg t2, ...])
          one 64-bit digest per case; a mismatch only says "differs" -> rerun the case as tokens
  tokens  CARRIER:  (KIT GEN <lets> tk t)
          the whole value of ONE case; exact structural comparison with paths
  ints    CARRIER:  (KIT GEN <lets> <body : List Int>)
          one integer per case, compared with the integer the generator computed (a Bool as 0/1,
          a float's bits, a digest of a token list the generator built with compare.digest)
  bits    CARRIER:  (<List Float term>).map (fun x => x.toBits.toNat)
          a list of floats (Np results) without the kit; exact comparison with paths
  dump    item def:ExprOrNum, decl Pl.zipB:  DUMP_x (<lets> [term1, term2, ...]) [()]
          nested lists; exact structural comparison with paths. PRELUDE TERMS ONLY: def:ExprOrNum
          does not depend on any unit (nor on Np), so a unit's result cannot be dumped; use tokens.
where t is a token term: `tR <frame>`, `tC <col>`, `tA <table>`.

Carriers (a `List Int -> List Int` declared by the evaluated item):
  "identity"  def:zz_carrier / zz_carrier   the default. The item depends on both preludes and on
              every unit, so the terms may call any unit; the output is the list itself.
  "cumsum"    def:FloatArray_ / Np.cumsumInt  the prelude suites (no unit in scope); the output is
              the running sums and compare.py takes the differences back.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import kit

HERE = Path(__file__).parent
WORK = HERE / "work"
UNIT_ITEM, UNIT_DECL = "def:zz_carrier", "zz_carrier"
NP_ITEM, NP_DECL = "def:FloatArray_", "Np.cumsumInt"
PL_ITEM, PL_DECL = "def:ExprOrNum", "Pl.zipB"
CARRIERS = {"identity": (UNIT_ITEM, UNIT_DECL), "cumsum": (NP_ITEM, NP_DECL)}
DUMPS = {"col": kit.DUMP_COL, "frame": kit.DUMP_FRAME, "table": kit.DUMP_TABLE,
         "floats": kit.DUMP_FLOATS, "optfloats": kit.DUMP_OPTFLOATS}


def _generator() -> str:
    """The script being run, relative to the workspace root (recorded in the suite and receipts)."""
    try:
        return str(Path(sys.argv[0]).resolve().relative_to(HERE.parent.parent))
    except ValueError:
        return sys.argv[0]


class Suite:
    def __init__(self, name: str, carrier: str = "identity", generator: str | None = None):
        """carrier: "identity" (units, default) or "cumsum" (prelude suites)."""
        self.name = name
        self.carrier = carrier
        self.item, self.decl = CARRIERS[carrier]
        self.generator = generator or _generator()
        self.notes: dict[str, str] = {}  # unit -> note for receipts/units.tsv
        self.inputs: list[dict] = []
        self.cases: list[dict] = []

    def use_carrier(self, carrier: str):
        """Switch the carrier of the inputs added from now on."""
        self.carrier = carrier
        self.item, self.decl = CARRIERS[carrier]

    def _case(self, cid, prim, expected, pos, kind, **kw):
        self.cases.append({"id": f"{self.name}/{cid}", "primitive": prim, "input": len(self.inputs), "pos": pos,
                           "kind": kind, "expected": expected, **kw})

    def _input(self, mode: str, text: str):
        self.inputs.append({"mode": mode, "item": self.item, "decl": self.decl, "carrier": self.carrier, "text": text})

    def digest(self, lets: str, cases: list[tuple], gen: bool = True, chunk: int = 10**9, table: bool = True):
        """cases: (id, primitive, token term, expected canonical[, dict of extra case fields])."""
        k_ = kit.KIT if table else kit.KIT_NOTABLE
        for k in range(0, len(cases), chunk):
            part = cases[k:k + chunk]
            for pos, c in enumerate(part):
                self._case(c[0], c[1], c[3], pos, "digest", **(c[4] if len(c) > 4 else {}))
            body = "[" + ", ".join(f"dg ({c[2]})" for c in part) + "]"
            self._input("digest", f"({k_}{kit.GEN if gen else ''}{lets}{body})")

    def digest_body(self, lets: str, body: str, cases: list[tuple], gen: bool = True, table: bool = False):
        """Like digest, but `body` is any Lean term of type List Int giving one digest per case, in
        the order of `cases` = (id, primitive, expected canonical[, extra]). Lets the Lean side
        enumerate the cases itself (short inputs)."""
        for pos, c in enumerate(cases):
            self._case(c[0], c[1], c[2], pos, "digest", **(c[3] if len(c) > 3 else {}))
        self._input("digest", f"({kit.KIT if table else kit.KIT_NOTABLE}{kit.GEN if gen else ''}{lets}{body})")

    def ints(self, lets: str, body: str, cases: list[tuple], gen: bool = False, table: bool = False, use_kit: bool = True):
        """`body` : List Int, one integer per case in the order of `cases` = (id, primitive,
        expected int[, extra]). For results that are not a column / frame / table: a Bool
        (`if b then 1 else 0`), the bits of a float (`(x.toBits.toNat : Int)`), a record tokenised
        by hand (`dg (<List UInt64>)`, expected `compare.digest([...])`)."""
        for pos, c in enumerate(cases):
            if type(c[2]) is not int:
                raise TypeError(f"{c[0]}: expected value must be an int, got {type(c[2]).__name__}")
            self._case(c[0], c[1], c[2], pos, "int", **(c[3] if len(c) > 3 else {}))
        pre = ((kit.KIT if table else kit.KIT_NOTABLE) if use_kit else "") + (kit.GEN if gen else "")
        self._input("ints", f"({pre}{lets}{body})")

    def tokens(self, lets: str, cid, prim, term: str, kind: str, expected, gen: bool = True, cells: bool = False, **kw):
        """kind: col | frame | table (what `term` tokenises). cells=True: the column / frame may
        hold `.cell` columns (Date), so the full kit is used (KIT_NOTABLE tokenises a cell column
        as `[5, length]` only, which cannot be decoded)."""
        self._case(cid, prim, expected, 0, kind, **kw)
        k_ = kit.KIT if kind == "table" or cells else kit.KIT_NOTABLE
        self._input("tokens", f"({k_}{kit.GEN if gen else ''}{lets}tk ({term}))")

    def bits(self, cid, prim, term: str, expected, **kw):
        """`term` : List Float (Np results); no kit: the bits go through the carrier directly."""
        self._case(cid, prim, expected, 0, "col", **kw)
        self._input("bits", f"(({term}).map (fun (x : Float) => (x.toBits.toNat : Int)))")

    def dump(self, lets: str, kind: str, cases: list[tuple], gen: bool = False):
        """cases: (id, primitive, Lean term of the dumped type, expected canonical[, extra]).
        Runs on def:ExprOrNum (Pl.zipB): prelude terms only, no unit and no Np in scope."""
        for pos, c in enumerate(cases):
            self._case(c[0], c[1], c[3], pos, kind, **(c[4] if len(c) > 4 else {}))
        body = "[" + ", ".join(c[2] for c in cases) + "]"
        pre = (kit.GEN if gen else "") + lets
        self.inputs.append({"mode": "dump", "item": PL_ITEM, "decl": PL_DECL, "carrier": "none",
                            "text": f"{DUMPS[kind]} ({pre}{body}) [()]" if pre else f"{DUMPS[kind]} {body} [()]"})

    def write(self) -> Path:
        WORK.mkdir(exist_ok=True)
        p = WORK / f"{self.name}.json"
        p.write_text(json.dumps({"suite": self.name, "generator": self.generator, "notes": self.notes,
                                 "inputs": self.inputs, "cases": self.cases}))
        calls: list[dict] = []
        for i, inp in enumerate(self.inputs):
            if calls and (calls[-1]["item"], calls[-1]["decl"]) == (inp["item"], inp["decl"]):
                calls[-1]["inputs"].append(inp["text"])
            else:
                calls.append({"item": inp["item"], "decl": inp["decl"], "first_input": i, "inputs": [inp["text"]]})
        (WORK / f"{self.name}.inputs.json").write_text(json.dumps(calls, indent=1, ensure_ascii=False))
        size = sum(len(i["text"]) for i in self.inputs)
        print(f"{self.name}: {len(self.inputs)} inputs ({size} chars), {len(self.cases)} cases -> {p}")
        return p
