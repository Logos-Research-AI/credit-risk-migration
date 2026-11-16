# Corrections, round 6: plan for rulings G54 and G55 (SAS blueprint)

Plan only. Nothing here has been applied to the blueprint `sas-credit-risk-spec`
(`3f5df696-7c80-45cc-809f-b2881714663d`). It is to be applied in one revision, after the
requirements blueprint is updated for G54 and the owner has refreshed the profile.

Written by the SAS translator on 2026-11-16. This file is in `migration/legacy-to-lean/`
because this role may not write (or read) under `migration/proofs/`; move it to
`migration/proofs/legacy-meets-requirements/reports/corrections-round6.md` if it belongs there.

## 1. What the rulings change

| Ruling | Effect on the SAS blueprint |
|---|---|
| G54: a present `MonthlyIncome` or `NumberOfDependents` is written in at most 12 characters | No Lean change. `CreditRisk.TrainOK` and `CreditRisk.TestOK` become narrower in the requirements blueprint; link (1) and link (2) quantify over them, so they narrow with them. One paragraph of text is added to link (1), clause (c) (section 3) |
| G55: files passed between scripts are taken at full precision | No Lean change. The text of link (3) is replaced (section 2) |

No unit changes. `credit_raw_clean`, `test_raw_clean`, their preconditions, the three export units
and `risk_scores_validation_clean` stay as they are.

## 2. Link (3) of `def:SasLinks`: new text (Lean unchanged)

In the item's text, replace the sentence

> (3) readFeatures, readScoresTrain, readScoresValid and readMedians are each the identity on tables.

by

> (3) Files passed from one script to the next (ruling G55 of the requirements, which extends
> ruling G38 from the published columns to these files). readFeatures, readScoresTrain,
> readScoresValid and readMedians are each the identity on tables. This is an idealisation and
> not a description of the SAS program: the values are taken as carried from one script to the
> next at full precision. The program writes each table to a CSV file and the next script reads
> the text back with PROC IMPORT. The feature files and the score files hold 12 characters per
> number (BEST12.); income_medians.csv holds 15 significant digits (BEST32.); interest_rate is
> written as a percent text and read back as a text column; and in the score files a text column
> is given the width of its longest value among the first 20 rows. What is lost on the way is
> outside the verification (experiment x25: on the reference data 11 of the 42 feature columns
> change, by at most 0.005, and every probability and score of the training score file, by at
> most 5E-11 and 5E-9). Every contract that reads a table through one of these four parameters
> (the contracts on score, scoreTest and metrics: Q12 to Q16, Q18 to Q26, and
> score_chains_agree) is a statement about the program with exact hand-offs.

The Lean of link (3) stays `∀ t, readFeatures t = t` and the three others. Its comment line
(`-- (3) a CSV file written by one script and read by the next: the identity`) can stay; if the
revision touches the Lean of `def:SasLinks` for any other reason, extend the comment with
"(an idealisation, ruling G55)".

## 3. Links (1) and (2): text added to clause (c), Lean unchanged

### Is clause (c) true of the real program under G54?

Clause (c) says: each of MonthlyIncome and NumberOfDependents is, in the imported row, a text
cell whose text read with BEST32. (`Sas.inputBest`) is exactly the value the requirements read.

What SAS does depends on the type PROC IMPORT gave the column:

- **Character column** (some row holds `NA` or another text). INPUT reads the text of the file.
  The clause describes this literally.
- **Numeric column** (no row holds a text; blanks allowed). There is no text cell in the SAS
  table. `input(MonthlyIncome, best32.)` first writes the number as 12-character text (BEST12.)
  and reads that text. The clause is true in effect exactly when that text reads back as the
  number.

Under G54 it does, as far as experiment x26 tested it (the real feature_engineering.sas, and the
import and `test_raw_clean` statements of predict.sas, both columns numeric, stored doubles
compared in hex before and after):

| Values | Rows | Changed by INPUT |
|---|---|---|
| Income, at most 12 characters with the zero before the point counted: every split of integer and decimal digits (67 classes, 120 random values each), small values `0.00…0ddd`, all-nines and `10…01` edges, 0, 999999999999, 0.0000000001 | 9,307 | 0 |
| Dependents, whole numbers of 1 to 12 digits and the edges (about 750 distinct values, repeated over the rows) | 9,509 | 0 |
| Blank income, blank dependents (stay missing) | 3 and 3 | 0 |
| Income written `.ddddddddddd` (eleven decimals, no zero before the point: 12 characters as typed, 13 with the zero) | 200 | 200 |
| Two 13-character values put among the edges by mistake (`99999999999.9`, `12345678901.5`) | 2 | 2 |

The same counts hold on the training and the test side. PROC IMPORT stored the nearest double
of the text on every row. The test is a sample, not a proof.

So clause (c) is true of the program in effect under G54, **provided "12 characters" counts a
zero before the decimal point**, as `CreditRisk.decimal32` already counts for the 32-character
bound. If G54 were formalised by the characters as typed, `.12345678901` would be a valid input
that the program changes. This is a point for the owner or the formaliser, not for this blueprint.

One thing the text must say: when the column is numeric, the text cell of the model is the
plain decimal writing of the number, not the text BEST12. produces. BEST formats can print a
small number in E notation (x09: `1.2345679E-6`), and `Sas.inputBest` does not model exponent
notation; the plain decimal writing has no exponent letter and at most 12 characters, so it meets
`credit_raw_clean_precond` and `test_raw_clean_precond` as they stand.

### Text to add

In the item's text, after the sentence that defines clause (c) ("… and when that value is
missing the text is one the SAS takes for a missing value (Sas.blankDotNA: blank, a period or
NA)."), add:

> The text cell of clause (c) stands for what the INPUT function of the SAS program reads. When
> PROC IMPORT gave the column the character type (some row holds NA or another text), it is the
> text of the file. When PROC IMPORT gave it the numeric type, the SAS table holds a number and
> no text: SAS writes the number as 12-character text (BEST12.) and INPUT reads that text. Under
> ruling G54 (a present MonthlyIncome or NumberOfDependents is a decimal number of at most 12
> characters, a zero before the decimal point counted) that text reads back as exactly the
> number (experiment x26), and the text cell of clause (c) is then the decimal writing of the
> number, which has no exponent letter. A missing value in a numeric column is written as a
> period and read as missing. Before ruling G54 this clause was not true of the program on
> every valid input (experiment x25: 2499.9999999999 in a numeric column was used as 2500).

The same paragraph serves link (2): its text says "the same two clauses for importTest".

### Lean

No change to links (1) and (2). They quantify over `CreditRisk.TrainOK` and `CreditRisk.TestOK`,
which the requirements blueprint narrows.

Outside valid inputs nothing is claimed (ruling G53), and one known gap stays: the second clause
of link (1) lets a number be delivered as a numeric cell, and on a numeric cell
`credit_raw_clean` returns missing where SAS does the 12-character round trip. No contract
reads that case.

## 4. Items the revision clears

From the dependency graph of the blueprint today:

- **If only the text of `def:SasLinks` is edited** (sections 2 and 3): I do not know whether a
  text-only edit clears dependents on this server; rule DEV-012 was observed for changes to an
  item's Lean.
- **If the Lean of `def:SasLinks` changes, or the profile refresh re-checks it** (it names
  `CreditRisk.TrainOK` and `CreditRisk.TestOK`): its 34 statement consumers are cleared.
  - The 26 contracts: `thm:sas_Q1` to `thm:sas_Q16`, `thm:sas_Q18` to `thm:sas_Q27`.
  - `thm:score_chains_agree`.
  - Seven lemmas: `lem:sasLinks_witness`, `lem:sas_links_sat`, `lem:sas_split_sat`,
    `lem:sas_Q27_clause1`, `lem:sas_feature_rows`, `lem:sas_features_some`,
    `lem:sas_test_feature_rows`.
- **Not consumers of `def:SasLinks`:** `lem:sas_score_rows`, `lem:sas_features_row_total`,
  `lem:sas_test_chain_agree`, `def:sasPipeline` and every unit. Whether the profile refresh
  clears any of them depends on which requirement declarations they name; I have not checked.

Expected work after the clearing: resubmit the 34 items unchanged. The contracts use the links
only on tables meeting `TrainOK` and `TestOK`, and a narrower input condition makes each
contract and the two satisfiability lemmas easier, not harder. This is an expectation from
reading the statements, not a result: no proof has been resubmitted.

## 5. Record to update with the revision

- `RULEBOOK.md`, parameter P6: add that the numeric-column case of the two INPUT calls is covered
  by ruling G54 (x25, x26), and that the hand-off files are an idealisation under ruling G55
  (x25).
- `RULEBOOK.md`, rule R9: add the evidence X26 for "a numeric column passes through BEST12.
  text; values of at most 12 characters are unchanged".

## 6. Evidence

All under `migration/legacy-to-lean/experiments/`:

- `x25_handoff_income.sas`, `.log`, `.lst`, `_QB1.csv`, `_QB2.csv`, `_run.py`: hand-off files on
  the reference data; the numeric-column round trip through the real feature_engineering.sas.
- `x26_g54_12chars.sas`, `.log`, `.lst`, `_run.py`; inputs `_train.csv`, `_test.csv`; the value
  of each row in `_values.csv`; the stored doubles in `_train_hex.csv`, `_test_hex.csv`.
- `migration/legacy-to-port/experiments/x09_input_numeric.sas`, `.log` (read, not mine).
