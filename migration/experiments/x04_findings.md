# X04: division by a constant and BEST12. rounding (prompt 02 review)

Question: `utilization_debt_interaction = credit_utilization * debt_ratio / 100`
(feature_engineering.sas:197) prints differently from Python in 424 of 149,987 reference cells.
Does SAS divide differently, or print differently?

Run: `x04_division_by_constant.sas` on ODA, 40 of the mismatching rows, every intermediate
printed with `hex16.` (log: `x04_division_by_constant.log`; picker `fanout/evidence/udi_pick.py`).

Results:
1. The inputs (`input(s, best32.)`), `R*100`, `D*100` and the product are bit-identical to
   Python on 40/40 rows.
2. `p / 100` in the DATA step is **IEEE division**: it matches Python's `p / 100` bit for bit on
   40/40 rows. It is not `p * 0.01` (37/40 equal by chance, 3 differ). So SAS divides like IEEE,
   and RULEBOOK amendment A13 (strict element-wise division) is the faithful translation.
3. SAS's `put q best12.` reproduces the reference cell on 40/40 rows. The judge's `sas_best12`
   (Python formatting of the exact binary value, which rounds half to even) gives the other text
   on 40/40 rows: `174544.687515` → SAS `174544.68752`, Python `174544.68751`. The difference is
   in printing.
4. BEST12. rounding rule, fitted on all 149,987 cells (`fanout/evidence/best12_rule.py`).
   Mismatching cells per rule:

   | Rule | Mismatches |
   |---|---|
   | Exact binary value, Python formatting (today) | 424 |
   | Shortest repr, half up | 152 |
   | **15 significant digits, then half up** | **39** |
   | 16 significant digits, half up | 72 |
   | 17 significant digits, half up | 340 |
   | Double `x·10^d`, then `floor(+0.5)` | 163 |

   The residual 39 cells sit within ~1e-16 relative of a half, below double precision, so SAS's
   exact digit algorithm cannot be recovered from outputs. Every residual is 1 unit in the 12th
   character, inside the judge's value tolerance, and passes its format check (the candidate's
   text is BEST12. of its own value).

Consequences:
- A13 stands (SAS divides like IEEE).
- New amendment A18: `sas_compat.sas_best12` rounds half up from the value's 15-significant-digit
  form.
