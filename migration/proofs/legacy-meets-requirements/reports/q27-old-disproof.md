Blueprint sas-credit-risk-spec (3f5df696-7c80-45cc-809f-b2881714663d). Read neg:sas_Q27_neg in full, then called unflag_false on it: the call succeeded (returned thm:sas_Q27), which withdraws the false flag and deletes the negation item in one step. remove_item was not called: the tool refuses neg: items and unflag_false already removed it. Checked afterwards: neg:sas_Q27_neg is "not found"; thm:sas_Q27 is in state TheoremStated, statement text unchanged, proof dependency lem:sas_Q27_clause1. Nothing else touched. No hook block.

Note for the lead: the statement text of thm:sas_Q27 still carries the old wording of Q27 ("On an input that does not, the pipeline stops with an error and produces no result (rulings G3, G4, G11)"). The task says it keeps its text, so I left it.

RECORD OF THE REMOVED ITEM (state before removal: TheoremProved; kind theorem; statement dependencies def:sasPipeline, def:SasLinks; proof dependencies lem:sasLinks_witness, lem:sas_split_sat)

--- statement_text ---
Negation of `thm:sas_Q27` — it is not the case that: Q27 holds of sasPipeline, for all parameters satisfying SasLinks. Requirement Q27: On an input that meets the conditions of section 3, every step produces its result. On an input that does not, the pipeline stops with an error and produces no result (rulings G3, G4, G11).

--- proof_text (the finding) ---
Finding (legacy-violates-requirement, clause 2 of Q27: an invalid training file must stop feature engineering).

Input: a training table of one row whose twelve columns carry the required names except `AGE` in place of `age`, every cell a number: `VAR1=1`, `SeriousDlqin2yrs=1`, `AGE=45`, `MonthlyIncome=9120`, `NumberOfDependents=2`, `RevolvingUtilizationOfUnsecuredL=0.766`, `DebtRatio=0.8`, `NumberOfTime30-59DaysPastDueNotW=2`, `NumberOfTime60-89DaysPastDueNotW=0`, `NumberOfTimes90DaysLate=0`, `NumberOfOpenCreditLinesAndLoans=13`, `NumberRealEstateLoansOrLines=6` (the values of row 1 of x21_b.csv). It does not meet TrainOK, because TrainOK asks the exact names and `AGE` is not one of them (proved). With `AGE` renamed to `age` the row meets every clause of TrainOK (by reading, not proved).

What Q27 demands: the features step returns the error outcome on this table (no feature file).

What the SAS program does, according to its Lean: the input check passes (columns_ok=1, bad_rows=0, duplicate_ids=0, known_incomes=1), the script does not stop and the features step returns a pair of feature tables. This is proved for every import that link (1) of SasLinks admits on this table: the ten other numbers kept as numbers, MonthlyIncome and NumberOfDependents each delivered as the number or as a text of at most 32 characters that reads back to it. The links are witnessed through lem:sasLinks_witness and lem:sas_split_sat (join order the identity, a model with no term).

SAS lines responsible (feature_engineering.sas): line 70, `upcase(name) in (...)` in the columns_ok query (68-79) compares the column names in upper case; lines 52-61, the macro %num finds a column with VARNUM, whatever its capitalisation. SAS names ignore case throughout, so the rest of the script reads the column `AGE` as `age`.

SAS evidence: experiments/x24_round4_q27 (.sas, .log, .lst; input file x24_round4_q27_A.csv), cases A and A_FULL: this exact one-row file, header `AGE`, through the current legacy/feature_engineering.sas. Case A (the script's import and check steps verbatim, with observation lines added): columns_ok=1, bad_rows=0, duplicate_ids=0, known_incomes=1. Case A_FULL (the whole script, paths redirected): the same totals, no stop, the script reaches its closing statements and the three files income_medians.csv, model_features_train.csv, model_features_validation.csv are written; model_features_train.csv holds the row (row_id 1, default_flag 1, 45, income 9120) and its third header is `AGE`. As the log shows it, PROC IMPORT read MonthlyIncome and NumberOfDependents with the numeric informat best32. (case A prints NumberOfDependents as numeric, 2), so the delivery SAS made is one of those the proof covers; the proof does not depend on which. Earlier and weaker: experiments/x21_review_round2, part B, a three-row file with the headers `AGE`, `DEBTRATIO`, `monthlyincome`, `seriousdlqin2yrs`, `numberofdependents` gave columns_ok=1, bad_rows=0, duplicate_ids=0, known_incomes=2 and %num(age)=45; that run executed a copy of the check steps (the experiment's %check macro, which reports and does not stop, written before ruling G42: `missing(VAR1)`, not `missing(%num(VAR1))`), not feature_engineering.sas itself.

Preconditions checked: credit_raw_input_check_precond (the precondition of the check units, the only units the proof uses) holds of every table link (1) admits for this input: proved inside the proof file (precond_all, applied to the imported table in the main proof; not part of the statement). For a text delivery of MonthlyIncome or NumberOfDependents it rests on the helper noexp_of_read: a text that Sas.inputBest reads as a number is not in the exponent form the precondition excludes. The proof uses only credit_raw_columns_ok, credit_raw_input_check, credit_raw_check_totals and credit_raw_stop; it says nothing about what the later units compute on this table. In particular credit_raw_clean_precond, of the next unit, asks text cells in the two columns, so it does not hold where a delivery has a number in one of them; it bears on the content of the feature tables, not on whether the script stops. None of the defects D1 to D5 of the links is involved: no text cell in the raw table, one row, no repeated name, no column of mixed kinds, no empty column.

Smallest change that would meet the requirement (described, not made): in the columns_ok query compare the names as they are, `name in ('VAR1', 'SeriousDlqin2yrs', 'age', 'MonthlyIncome', 'NumberOfDependents', ...)` without `upcase`, so that a header in other capitalisation gives columns_ok=0 and the script stops. The alternative is a ruling that column names are matched whatever their capitalisation (owner point O3), which changes TrainOK and not the program.

--- statement_lean ---
theorem sas_Q27_neg : ∃ (importTrain : Tabular.Table ℝ → Tabular.Table ℝ) (importTest : Tabular.Table ℝ → Tabular.Table ℝ) (importTestColumns
  : Tabular.Table ℝ → List String) (readFeatures : Tabular.Table ℝ → Tabular.Table ℝ) (readScoresTrain :
  Tabular.Table ℝ → Tabular.Table ℝ) (readScoresValid : Tabular.Table ℝ → Tabular.Table ℝ) (readMedians :
  Tabular.Table ℝ → Tabular.Table ℝ) (arrange : Tabular.Table ℝ → Tabular.Table ℝ) (split :
  ℕ → Tabular.Table ℝ → Tabular.Table ℝ) (fit : Tabular.Table ℝ → Sas.Model ℝ) (agg : Sas.SqlAgg ℝ) (featTrainExists :
  Tabular.Table ℝ → Bool) (featValidExists : Tabular.Table ℝ → Bool) (scoresTrainExists : Tabular.Table ℝ → Bool)
  (scoresValidExists : Tabular.Table ℝ → Bool) (mediansExist : Tabular.Table ℝ → Bool) (coefExists :
  Sas.Model ℝ → Bool),
  SasLinks importTrain importTest importTestColumns readFeatures readScoresTrain readScoresValid readMedians arrange
      split fit agg featTrainExists featValidExists scoresTrainExists scoresValidExists mediansExist coefExists ∧
    ¬CreditRisk.Q27
        (sasPipeline importTrain importTest importTestColumns readFeatures readScoresTrain readScoresValid readMedians
          arrange split fit agg featTrainExists featValidExists scoresTrainExists scoresValidExists mediansExist
          coefExists) := sorry

The proof Lean (proof_lean) was not requested and was not read; it is gone with the item.