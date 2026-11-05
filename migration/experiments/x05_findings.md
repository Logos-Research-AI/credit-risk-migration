# X05: latent SAS semantics found by the stress test (run on ODA, 2026-11-05)

Source: `x05_edge_semantics.sas`; log: `x05_edge_semantics.log`.

| Question | SAS result | Rule for the port |
|---|---|---|
| PROC SQL `sum/mean/max` over zero rows | `.` (missing) for all three | S10: SQL aggregates over 0 rows (or all missing) → missing |
| `round()` near .5 | 2.4999999999999996 → 3; 2.49999999999999 (1e-14 below) → 3; 2.4999999999 (1e-10 below) → 2; 712.49999999999989 → 713; -2.5 → -3; 4503599627370497 → itself | round half away from zero with a FUZZ: \|frac − 0.5\| ≤ 1e-12·max(1,\|x\|) counts as half. The 1e-12 is bracketed by the observations (1e-14 is fuzzed, 1e-10 is not). Integers ≥ 2^52 are returned unchanged |
| −0.00001 in 8.4 | ` -0.0000` | w.d keeps the minus sign of a negative value that rounds to zero |
| −0.05 in percent8.2 | `( 5.00%)` | PERCENTw.d prints negatives in parentheses, and the width includes them |
| 0.000015 in BEST6. / BEST8. / BEST12. | `15E-6` / `0.000015` / `0.000015` | E-notation is chosen when plain notation cannot show the value within the width; the 1e-5 threshold holds for BEST12. only |
| 123456789 in 8.4 | `1.2346E8` | w.d that cannot fit falls back to BESTw. |
| exp(1000) | `.` (missing) | S1: exp overflow → missing |
