"""Evaluation carrier def:zz_carrier_e (harness only, not part of the package; removed at the close).

Restored 2026-11-18 by the lead's decision (RULEBOOK G20; diffeval/README.md, carrier section).
`eval_decl` resolves `decl` only among the declarations of the item it evaluates, while the
input terms may use everything that item depends on. def:zz_carrier_e depends on the units it
evaluates and declares, besides the identity on List Int, the printing helpers: functions from a
unit's result (at Float) to a List Int of tokens (the encoding of diffeval/kit.py: tS, tF, tI,
tB, tT, tX, tC, tR, tA; compare.tok_* decodes them), so that a result comes back exactly
(a Float is never printed). Nothing depends on the carrier.
"""


def zz_carrier_e(xs: list[int]) -> list[int]:
    return xs
