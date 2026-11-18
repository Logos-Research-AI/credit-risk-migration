# Draft for the lead: tightening `SasLinks` (1) and (2), padded text (2026-11-18)

Status: draft, for approval. Nothing was changed on any blueprint, nothing committed. The Lean
below was not compiled (this task was read-only); it differs from the accepted Lean of
`def:SasLinks` (blueprint `3f5df696-7c80-45cc-809f-b2881714663d`, read 2026-11-18) in two
conjuncts and five comment lines.

Owner's decision 4 of 2026-11-18: the padded-text limit becomes an assumption in `SasLinks` (1)
and (2): delivered texts carry no blank at either end; the 34 dependents are proved again.

## 1. What is wrong today, and what is needed

- `credit_raw_clean` and `test_raw_clean` are `input(MonthlyIncome, best32.)` and the same for
  `NumberOfDependents` (`legacy/feature_engineering.sas:139-140`, `legacy/predict.sas:203-204`):
  no `strip`. The real informat reads the first 32 characters of the value. `Sas.inputBest`
  removes the blanks at both ends first and reads all of what is left.
- The two agree on a text exactly when the real text has at most 32 characters, blanks counted
  (BEST32. then sees all of it and ignores the blanks at its ends). They differ on 31 blanks then
  `55` (Lean 55, SAS 5).
- The links bound the trimmed length only, in clause (ii) of the delivery of a cell, and bound
  nothing in clause (iii), so that text is admitted.
- The input check is not concerned: `%num` is `input(strip(v), ?? best32.)` behind
  `lengthn(strip(v)) <= 32` (`feature_engineering.sas:60`, `predict.sas:125`), which is what
  `num_macro` and `test_num_macro` do.
- So one fact is enough: a delivered text cell has no blank at either end. With the bound
  already in (ii) the text then has at most 32 characters as it is, which is the length clause of
  `credit_raw_clean_precond` and `test_raw_clean_precond`.

## 2. The change

Only the local definition `deliveredCell` changes, in its clauses (ii) and (iii): one conjunct
is appended to each, `Sas.trimBlanks s.toList = s.toList` (removing the blanks at the ends
changes nothing). `deliveredRow`, `textColumn`, `deliveredTable`, the shape of clauses (1) and
(2), and clauses (2b) to (8) are untouched.

Why there and not in `deliveredRow` (c):

- `deliveredTable` is asserted of every raw table, so of every valid one. On a valid table no
  raw cell holds a text (`TrainOK`, `TestOK`), so every text cell of the imported table comes
  from (ii) or (iii). The tightening therefore reaches every text the clean units read on valid
  input.
- Every dependent proof I read discards the second half of clauses (1) and (2) (section 5).
  A change inside `deliveredCell` cannot reach them.
- A change to `deliveredRow` (c) would break every proof that keeps a literal copy of it
  (`FS.D` in `lem:sas_features_some`, `CRC.D` in the port's coverage lemmas) or picks its parts
  by position (`.2.2.2` in `lem:sas_features_some`).

Clause (i) is not changed: a raw cell holding a text is delivered as that same text. Adding "no
blank" there would make `SasLinks` unsatisfiable (a raw text with a blank would have to be
delivered equal to itself and without the blank). Such tables are outside valid input (ruling
G53: nothing is claimed). Defect D1 of the round 4 review stays as it was.

### Is it true of PROC IMPORT on the real files

- Character column (some row holds `NA` or another text): PROC IMPORT stores ` 7`, `7 `, `" 7"`,
  `"7 "` all as `7` (experiment x23 part I, RULEBOOK R33). Trailing blanks of a character value
  are not represented in the Lean (rule R7).
- Numeric column: SAS holds a number, and INPUT reads its BEST12. text, 12 characters, right
  aligned, so with leading blanks. The text cell of the model is that text without them. The
  real informat ignores them because 12 is at most 32. The revised wording says so.
- The real files hold plain digits and `NA`.

## 3. Informal text of `def:SasLinks`: sentences to replace

All other sentences stay word for word.

1. In (1), after "(Sas.blankDotNA: blank, a period or NA).", replace "The text cell of clause (c)
   stands for what the INPUT function of the SAS program reads." by:

   > The text cell of clause (c) stands for what the INPUT function of the SAS program reads,
   > without the blanks at its two ends. The text INPUT really reads has at most 32 characters,
   > blanks counted, so the BEST32. informat sees all of it and ignores those blanks: reading the
   > text cell with Sas.inputBest gives what the SAS program reads.

2. In the same passage, replace "SAS writes the number as 12-character text (BEST12.) and INPUT
   reads that text." by:

   > SAS writes the number as 12-character text (BEST12., right aligned, so with leading blanks)
   > and INPUT reads that text; the text cell holds it without the leading blanks.

3. Clause (ii), replace by:

   > (ii) A raw cell holding a number x is delivered either as the numeric cell holding x, or,
   > only when its column name is a text column of t, as a text cell whose text has no blank at
   > either end, has at most 32 characters, and reads as exactly x with the SAS informat
   > (Sas.inputBest).

4. Clause (iii), replace by:

   > (iii) A raw cell holding a missing value (the numeric missing or the missing text) is
   > delivered either as the numeric missing, or, only when its column name is a text column of
   > t, as a text cell (possibly the missing text) whose text has no blank at either end and, put
   > in upper case, is empty, a single period or NA.

5. After clause (iii), add:

   > That a delivered text has no blank at either end is an assumption about PROC IMPORT (owner's
   > decision of 2026-11-18; experiment x23 part I: ` 7`, `7 `, " 7" and "7 " are all stored as
   > `7`). Clause (i) is as before: on a table outside valid input a raw text is delivered as it
   > is.

In the Lean, "has at most 32 characters" stays written as the bound on the trimmed text, next to
the new conjunct; together they bound the text as it is.

## 4. Full new Lean of `def:SasLinks`

Changed lines are marked `-- CHANGED` or `-- NEW` here only; the marks are not part of the
statement.

```lean
open Tabular in
-- The links of the parameters of `sasPipeline`, in the order it takes them. Every contract
-- carries this one hypothesis and no other.
def SasLinks
    (importTrain : Table ℝ → Table ℝ)
    (importTest : Table ℝ → Table ℝ)
    (importTestColumns : Table ℝ → List String)
    (readFeatures : Table ℝ → Table ℝ)
    (readScoresTrain : Table ℝ → Table ℝ)
    (readScoresValid : Table ℝ → Table ℝ)
    (readMedians : Table ℝ → Table ℝ)
    (arrange : Table ℝ → Table ℝ)
    (split : ℕ → Table ℝ → Table ℝ)
    (fit : Table ℝ → Sas.Model ℝ)
    (agg : Sas.SqlAgg ℝ)
    (featTrainExists featValidExists : Table ℝ → Bool)
    (scoresTrainExists scoresValidExists : Table ℝ → Bool)
    (mediansExist : Table ℝ → Bool)
    (coefExists : Sas.Model ℝ → Bool) : Prop :=
  -- PROC IMPORT, one row: `q` is the imported row of the raw row `r`; `macro` is the reading
  -- macro of the input check (%num).
  -- (a) the same column names in the same order; (b) every column other than the two SAS reads
  -- as text is a numeric cell with the value the requirements read with `CreditRisk.num` (a
  -- missing value, however encoded, is the numeric missing); (c) MonthlyIncome and
  -- NumberOfDependents are text cells whose text reads (BEST32., `Sas.inputBest`) as the value
  -- the requirements read, the check's macro reads that same value, and a missing value is a
  -- text the SAS takes for missing (blank, `.` or NA: `Sas.blankDotNA`).
  let deliveredRow : (Row ℝ → String → Sas.Num ℝ) → Row ℝ → Row ℝ → Prop := fun rd r q =>
    q.map Prod.fst = r.map Prod.fst ∧
    (∀ c ∈ r.map Prod.fst, c ≠ "MonthlyIncome" → c ≠ "NumberOfDependents" →
      q.get c = some (Cell.num (CreditRisk.num r c))) ∧
    (∀ c ∈ ["MonthlyIncome", "NumberOfDependents"],
      (∃ s : Option String, q.get c = some (Cell.str s)) ∧
      (Sas.inputBest (Sas.chr q c) : Sas.Num ℝ) = CreditRisk.num r c ∧
      rd q c = CreditRisk.num r c ∧
      (CreditRisk.num r c = none → Sas.blankDotNA q c = true))
  -- PROC IMPORT, any raw table (round 4): the file is delivered as it is.
  -- A column name is a text column of the raw table when it is one of the two columns SAS
  -- reads as text, or some row of the raw table has a cell of that name holding a text.
  let textColumn : Table ℝ → String → Prop := fun raw c =>
    c = "MonthlyIncome" ∨ c = "NumberOfDependents" ∨
    ∃ r ∈ raw, ∃ p ∈ r, p.1 = c ∧ ∃ s : String, p.2 = Cell.str (some s)
  -- One cell: `x` is the raw cell of the column named `c`, `y` the imported cell.
  -- (i) a text is delivered as the same text; (ii) a number as the same number, or, in a text
  -- column only, as a text with no blank at either end, of at most 32 characters, that reads   -- CHANGED
  -- back to it (BEST32., `Sas.inputBest`); (iii) a missing value as the numeric missing, or,   -- CHANGED
  -- in a text column only, as a text cell with no blank at either end that SAS takes for       -- CHANGED
  -- missing (blank, `.` or NA, as `Sas.blankDotNA` tests a text cell). No blank at either end  -- CHANGED
  -- (`Sas.trimBlanks` changes nothing): an assumption about PROC IMPORT (2026-11-18; x23 I).   -- NEW
  let deliveredCell : Table ℝ → String → Cell ℝ → Cell ℝ → Prop := fun raw c x y =>
    match x with
    | Cell.str (some s) => y = Cell.str (some s)
    | Cell.num (some v) =>
      y = Cell.num (some v) ∨
      (textColumn raw c ∧ ∃ s : String, y = Cell.str (some s) ∧
        (Sas.trimBlanks s.toList).length ≤ 32 ∧ (Sas.inputBest s : Sas.Num ℝ) = some v ∧
        Sas.trimBlanks s.toList = s.toList)                                                   -- NEW
    | _ =>
      y = Cell.num none ∨
      (textColumn raw c ∧ ∃ s : Option String, y = Cell.str s ∧
        (let t := (Sas.trimBlanks (s.getD "").toList).map Char.toUpper
         t == [] || t == ['.'] || t == ['N', 'A']) = true ∧
        Sas.trimBlanks (s.getD "").toList = (s.getD "").toList)                               -- NEW
  -- The whole table: the rows in order, and in each row the cells in order, each with the
  -- name of the raw cell and a content delivered from it.
  let deliveredTable : Table ℝ → Table ℝ → Prop := fun raw imp =>
    List.Forall₂
      (fun (r q : Row ℝ) =>
        List.Forall₂
          (fun (p p' : String × Cell ℝ) => p'.1 = p.1 ∧ deliveredCell raw p.1 p.2 p'.2) r q)
      raw imp
  -- The pipeline at these same parameters (for the file-existence links)
  let P : CreditRisk.Pipeline :=
    sasPipeline importTrain importTest importTestColumns readFeatures readScoresTrain
      readScoresValid readMedians arrange split fit agg featTrainExists featValidExists
      scoresTrainExists scoresValidExists mediansExist coefExists
  -- (1) PROC IMPORT of the raw training file. First clause (round 3, unchanged): defined on
  -- every table that meets TrainOK, within the precondition of the first unit (the input
  -- check). Second clause (round 4): every raw table, valid or not, is delivered as it is. No
  -- unit precondition is asserted outside TrainOK, and nothing about what the checks return.
  ((∀ raw : Table ℝ, CreditRisk.TrainOK raw →
    List.Forall₂ (deliveredRow num_macro) raw (importTrain raw) ∧
    credit_raw_input_check_precond (importTrain raw)) ∧
   (∀ raw : Table ℝ, deliveredTable raw (importTrain raw))) ∧
  -- (2) PROC IMPORT of the raw test file: the same two clauses
  ((∀ raw : Table ℝ, CreditRisk.TestOK raw →
    List.Forall₂ (deliveredRow test_num_macro) raw (importTest raw) ∧
    test_raw_input_check_precond (importTest raw)) ∧
   (∀ raw : Table ℝ, deliveredTable raw (importTest raw))) ∧
  -- (2b) the column names PROC IMPORT gave the test table (first argument of
  -- test_raw_columns_ok): on a test table meeting TestOK, the twelve column names of section 5
  -- of the requirements, each once, in any order; within test_raw_columns_ok_precond. Nothing
  -- is said outside TestOK.
  (∀ raw : Table ℝ, CreditRisk.TestOK raw →
    List.Perm (importTestColumns raw)
      ["VAR1", "SeriousDlqin2yrs", "age", "MonthlyIncome", "NumberOfDependents",
       "RevolvingUtilizationOfUnsecuredL", "DebtRatio",
       "NumberOfTime30-59DaysPastDueNotW", "NumberOfTime60-89DaysPastDueNotW",
       "NumberOfTimes90DaysLate", "NumberOfOpenCreditLinesAndLoans",
       "NumberRealEstateLoansOrLines"] ∧
    test_raw_columns_ok_precond (importTestColumns raw)) ∧
  -- (3) a CSV file written by one script and read by the next: the identity (an idealisation, ruling G55)
  (∀ t : Table ℝ, readFeatures t = t) ∧
  (∀ t : Table ℝ, readScoresTrain t = t) ∧
  (∀ t : Table ℝ, readScoresValid t = t) ∧
  (∀ t : Table ℝ, readMedians t = t) ∧
  -- (4) the row order of the PROC SQL joins: a permutation (the condition on `arrange` in
  -- credit_imputed_precond and test_imputed_precond)
  (∀ t : Table ℝ, List.Perm (arrange t) t) ∧
  -- (5) PROC SURVEYSELECT with OUTALL, samprate 0.7: the rows in order, each with Selected 0 or
  -- 1; the number selected is 70 % of the rows rounded up, (7 n + 9) / 10 in ℕ (the size
  -- clause: the draw) (at least 4 rows since ruling G57, so the validation part is not empty)
  (∀ (seed : ℕ) (t : Table ℝ),
    List.Forall₂
      (fun (r q : Row ℝ) => ∃ v : ℝ, (v = 0 ∨ v = 1) ∧ q = Sas.setNum r "Selected" (some v))
      t (split seed t) ∧
    ((split seed t).filter (fun q => Sas.eq (Sas.num q "Selected") (some 1))).length
      = (7 * t.length + 9) / 10) ∧
  -- (6) the model fit: every term names a candidate variable of the MODEL statement
  -- (train.sas 72-98)
  (∀ F : Table ℝ, ∀ t ∈ (fit F).terms,
    t.1 ∈ ["credit_utilization_capped", "debt_ratio_capped",
      "num_late_30_59", "num_late_60_89", "num_late_90_plus",
      "total_late_payments", "has_delinquency", "has_serious_delinquency",
      "age", "monthly_income", "log_monthly_income",
      "num_credit_lines", "num_real_estate_loans", "log_num_credit_lines",
      "num_dependents", "income_per_dependent", "credit_lines_per_person",
      "flag_high_utilization", "flag_very_high_utilization",
      "flag_high_debt_ratio", "flag_very_high_debt_ratio",
      "flag_recent_late_payments", "flag_serious_delinquency",
      "flag_multiple_delinquencies", "flag_low_income",
      "flag_many_dependents", "flag_few_credit_lines",
      "total_risk_flags",
      "credit_util_category", "debt_category", "age_category",
      "financial_health",
      "age_income_interaction", "utilization_debt_interaction",
      "MonthlyIncome_missing", "Dependents_missing"]) ∧
  -- (7) PROC SQL SUM and MEAN: the real sum and mean of the list
  (∀ l : List ℝ, agg.sum l = l.sum ∧ agg.mean l = l.sum / ((l.length : ℕ) : ℝ)) ∧
  -- (8) file existence (ruling G36): a file exists exactly when the step that writes it
  -- returned a result
  (∀ F : Table ℝ, featTrainExists F = true ↔
    ∃ (train : Table ℝ) (seed : ℕ) (F1 F2 : Table ℝ),
      P.features train seed = some (F1, F2) ∧ (F = F1 ∨ F = F2)) ∧
  (∀ F : Table ℝ, featValidExists F = true ↔
    ∃ (train : Table ℝ) (seed : ℕ) (F1 F2 : Table ℝ),
      P.features train seed = some (F1, F2) ∧ (F = F1 ∨ F = F2)) ∧
  (∀ S : Table ℝ, scoresTrainExists S = true ↔
    ∃ (m : P.Model) (F : Table ℝ), P.score m F = some S) ∧
  (∀ S : Table ℝ, scoresValidExists S = true ↔
    ∃ (m : P.Model) (F : Table ℝ), P.score m F = some S) ∧
  (∀ train : Table ℝ, mediansExist train = true ↔
    ∃ (seed : ℕ) (F1 F2 : Table ℝ), P.features train seed = some (F1, F2)) ∧
  (∀ m : Sas.Model ℝ, coefExists m = true ↔ ∃ F : Table ℝ, P.fit F = some m)
```

The new conjunct is last in each clause on purpose: a proof that takes the earlier parts by
position keeps working.

## 5. The 34 dependents on the SAS blueprint (`get_graph consumers_of def:SasLinks`)

All 34 are statement consumers; the change clears all 34 statements and proofs. No statement
text or statement Lean changes: they are restated from the stored drafts as in round 6 and
should hash equal to `snapshot-round6.json`.

How much I read: the proofs total about 22,000 lines; I read each proof where it takes
`hLinks` apart for the items marked "read", and the tail only for the others.

| Item | Proof after the change | Basis |
|---|---|---|
| `lem:sasLinks_witness` | mechanical edit (below) | read in full |
| `lem:sas_links_sat` | the same mechanical edit | tail read; same `SLS` file with `id` reads (704 lines against 707) |
| `lem:sas_features_some` | unchanged | read in full: `obtain ⟨⟨hl1, -⟩, -⟩ := hLinks`; its copy `FS.D` is `deliveredRow` |
| `lem:sas_feature_rows` | unchanged | read: uses `hLinks.1.1` and links (4), (5) |
| `lem:sas_test_feature_rows` | unchanged | read: `⟨⟨hImpTr, -⟩, ⟨hImpTe, -⟩, -, -, -, -, hRM, hArr, -⟩` |
| `lem:sas_Q27_clause1` | unchanged | read: `⟨-, ⟨hl2, -⟩, hl2b, …⟩` and `sas_features_some` |
| `lem:sas_split_sat` | unchanged | tail read; link (5) only |
| `thm:sas_Q1`, `Q2`, `Q3`, `Q10` | unchanged | read: `⟨⟨h, -⟩, …⟩`, second half discarded |
| `thm:sas_Q7` | unchanged | first line read: `hLinks.2.2.2.2.2.2.2.2.1` (link 5) |
| `thm:sas_Q11` | unchanged | read in full: `hLinks` not used |
| `thm:sas_Q12` | unchanged | read: `⟨-, -, -, hRF, -⟩` and `sas_test_feature_rows` |
| `thm:sas_Q13` | unchanged (expected) | main theorem read: passes `hLinks` to `Q13P.core`, not read |
| `thm:sas_Q27` | unchanged | read in full: passes `hlinks` to `sas_Q27_clause1` |
| `thm:sas_Q4`, `Q6`, `Q9`, `Q25` | unchanged (expected) | tail read, uses links (4), (5), (6), (3); the line taking `hLinks` apart not read |
| `thm:sas_Q5`, `Q8`, `Q14`, `Q15`, `Q16`, `Q18` to `Q24`, `Q26`, `thm:score_chains_agree` | unchanged (expected) | not read at that line |

Why "expected" is a fair word for the unread ones: since ruling G53 no statement speaks of an
invalid table, the second half of (1) and (2) is the only place `deliveredCell` appears, and the
12 proofs read at that line either discard that half or do not touch clauses (1) and (2). A proof would break only if it names that half and
opens a cell. The resubmission shows it at once; the repair would be one more `-` or name in a
pattern.

### The edit to `lem:sasLinks_witness` and `lem:sas_links_sat` (namespace `SLS`)

The witness texts already have no blank (digits and a decimal point; `SLS.D_nb`, `SLS.trim_id`),
and the missing text is `none`. Edits, the same in both files:

1. `SLS.Good`: add a fourth part at the end, `∧ Sas.trimBlanks s.toList = s.toList`.
2. `SLS.good_int`, `SLS.good_dec`: `refine ⟨?_, ?_, ?_, ?_⟩`, and a fourth bullet
   `· rw [hs]; exact trim_id _ hnb`.
3. `SLS.pre_all`: `(sp_good r (h r hr) c hs x hx).2.2` becomes `.2.2.1`.
4. `SLS.deliveredCell` (the local copy): the two new conjuncts, as in section 4.
5. `SLS.imp_cell`: `⟨tc raw c hc, enc v, rfl, g.2.1, g.1⟩` becomes
   `⟨tc raw c hc, enc v, rfl, g.2.1, g.1, g.2.2.2⟩`; the two
   `⟨tc raw c hc, none, rfl, miss_ok⟩` become
   `⟨tc raw c hc, none, rfl, miss_ok, by simp [Sas.trimBlanks]⟩`.
6. `SLS.asCell_ok` (`simp [deliveredCell, asCell]`, left disjuncts only) should close as it is.

`exists_good`, `enc`, `enc_good`, `deliv`, `dt_valid`, `dt_asis` and the main proofs do not
change. So the tightened links stay satisfiable, by the same witness.

## 6. The port blueprint (`5365851c-5549-44b7-9207-4bd4c422031d`)

The port blueprint uses `SasLinks` and the SAS lemmas through the profile. After the SAS
blueprint is signed off again the owner refreshes the port profile; nothing below can be done
before that.

Items whose statement names `SasLinks`: `def:SasLinksOf`, `thm:T0`, the 20 `lem:sas_cov_*`,
`lem:sas_fit_term_names`; `def:Paired` copies its four local definitions "word for word".
(Proofs are not searchable; `lem:ex_F4_model_summary` uses `SasLinksOf` in its proof, and
`thm:G2_train_coverage`, `thm:G3_predict_coverage`, `thm:G4_metrics_coverage`, `lem:ex_G2_run`
use `thm:T0`.)

### T0 must be proved again. How.

T0 (read in full, 273 lines) takes its importers from the profile lemma `sas_links_sat` and
uses the same two facts `hI1`, `hI2` twice:

- For `SasLinksOf sas`: `exact ⟨hI1, hI2, hI3, …⟩`. Compiles unchanged: the witness now meets
  the tightened clauses because `sas_links_sat` proves them.
- For `Paired py sas`: `exact ⟨hI1, hI2, hI3, …⟩` against clause 1 of `def:Paired`, which holds
  the old `deliveredCell`. This no longer type-checks.

Two ways, for the lead to choose:

- **P1, `def:Paired` untouched.** Add one helper to the T0 file: the tightened `deliveredTable`
  implies the old one (`List.Forall₂.imp` twice; on the cell, four cases of the raw cell, and in
  the two text branches drop the last conjunct). About 25 lines, no mathematics. Give
  `⟨hI1.1, weaken hI1.2⟩` and `⟨hI2.1, weaken hI2.2⟩` to the `Paired` half. T0's statement is
  unchanged. Cost: the comment "word for word" in `def:Paired` and item 1 of section 3 of
  `definitions-v3.md` are then no longer exact (Paired asks the old, weaker import clause); to be
  recorded in `changes.md`.
- **P2, `def:Paired` clause 1 tightened the same way.** T0 compiles unchanged. It clears the 36
  statement consumers of `def:Paired` (E1 to E11, F1 to F6, A4, T0 and 17 lemmas).

Recommendation: P2 only if correction C-g to `def:PyLinks` clears those contracts anyway, in the
same pass; otherwise P1. No equality contract needs the tightening (prover-1's check, round
record of 2026-11-17): `PyLinks` 1 to 4 admit no padded number text.

### The coverage lemmas

`lem:sas_cov_credit_raw_clean` (read in full) uses only the first half of clause (1); it
compiles unchanged, and so should the other 19. But the statements of
`lem:sas_cov_credit_raw_clean` and `lem:sas_cov_test_raw_clean` leave out the length clause and
say in their text that `SasLinks` does not imply it (witness: 33 blanks and `5`). After the
tightening it is implied, and the text is false as worded. They should be restated with the
full precondition (`t.length ≤ 32` back in). New proof work, short: `q.get c` is the first cell
of `q` named `c`; by `deliveredTable` it sits opposite the first cell of `r` named `c`, which
on a valid table is a number or a missing value; the cell is a text, so the text branch of (ii)
or (iii) applies and gives no blank, hence `t.length ≤ 32`. Row 2 of the table in section 4a of
`informal-spec.md` ("holds, from `SasLinks` (1) c") then reads "(1), both clauses".

## 7. Items cleared

SAS blueprint, by the change to `def:SasLinks` (34): `lem:sasLinks_witness`,
`lem:sas_Q27_clause1`, `lem:sas_feature_rows`, `lem:sas_features_some`, `lem:sas_links_sat`,
`lem:sas_split_sat`, `lem:sas_test_feature_rows`, `thm:sas_Q1` to `thm:sas_Q16`, `thm:sas_Q18`
to `thm:sas_Q27`, `thm:score_chains_agree`. Not cleared: `lem:sas_score_rows`,
`lem:sas_features_row_total`, `lem:sas_test_chain_agree` (not consumers), every `def:`.

Port blueprint, after the profile refresh: `thm:T0` (proof edit under P1) and whatever depends
on its proof (`thm:G2_train_coverage`, `thm:G3_predict_coverage`, `thm:G4_metrics_coverage`,
`lem:ex_F4_model_summary`, `lem:ex_G2_run`); the 20 `lem:sas_cov_*`, `lem:sas_fit_term_names`
and `def:SasLinksOf` to be resubmitted against the new profile; two of the coverage lemmas
restated (section 6). Under P2 also the 36 consumers of `def:Paired`. I do not know whether a
profile refresh clears port items by itself; `port-lean-update-procedure` should say.

## 8. Risks

1. **Not compiled.** The new Lean and every edit above were written by reading. The two new
   conjuncts are plain equalities of `List Char`; the first submission will tell.
2. **Evidence for the assumption is one experiment on another column.** x23 part I was run on
   the id column `VAR1` of the training file, with the training check only. It was not run on
   `MonthlyIncome` or `NumberOfDependents`, nor on the test file. A short run would close this:
   a file with ` 5000`, `5000 `, `" 5000"` and 40 blanks then `55` in `MonthlyIncome`, printing
   the stored value in `$quote.` and `input(MonthlyIncome, best32.)`.
3. **Other white space.** `Sas.trimBlanks` removes the blank character only. A tab or a
   non-breaking space next to a number is not covered by the clause; such a file is outside the
   stated limit on number forms (plain digits, blank, `.`, `NA`).
4. **Clause (i) and tables outside valid input.** A raw text there is still delivered with its
   blanks (D1). Nothing is claimed there (G53), but "every admitted text" in the strict sense
   holds on valid input only. Tightening (i) is not possible without changing what a raw text is.
5. **The text cell of a numeric column** is the BEST12. text without its leading blanks: the
   assumption is about the model's cell, and the agreement with the real informat rests on
   "12 is at most 32", now said in the text.
6. **The tightening reaches the clean units through both halves of (1) and (2) together**, not
   through `deliveredRow` (c). A proof that wants the length needs the position argument of
   section 6. The alternative (a conjunct in `deliveredRow` (c)) makes that immediate and breaks
   every proof holding a copy of `deliveredRow`.
7. **Sign-off.** `def:SasLinks` is a signed-off item; this is its third revision after
   sign-off. The round 6 audit steps apply again: 34 statements against the snapshot by hash,
   109 definitions with only `def:SasLinks` differing, no `sorry`/`axiom` in 37 proofs.
8. **Reports to amend once done:** final report section 2 ("Padded text on the SAS side" becomes
   an assumption of links (1) and (2), no longer a limit candidate; the third finding about the
   SAS side is closed) and section 5.

## 9. Questions for the lead

1. P1 or P2 for `def:Paired` (section 6).
2. Restate `lem:sas_cov_credit_raw_clean` and `lem:sas_cov_test_raw_clean` with the full
   precondition?
3. Run the experiment of risk 2 before the change is signed off?
