"""x25: (Q-A) what the files written by one script hold and what PROC IMPORT of the next
script delivers; (Q-B) INPUT(MonthlyIncome, best32.) when PROC IMPORT typed the column numeric.

One session of SAS OnDemand (profile oda_eu), one submission per block, in this order:

  QB1  the real feature_engineering.sas (only its two path macros redirected) on a valid
       training file with NO missing income (so MonthlyIncome is imported numeric) holding
       1234567890123, 2499.9999999999 and 5400.12345678; then an observation block.
  QB2  the same file plus one row with income NA (the column is imported character): control.
  FULL the four real scripts on legacy/data (paths redirected), with observation blocks
       between them: PROC COMPARE of each table given to PROC EXPORT with the table the next
       script's PROC IMPORT delivers.
  T    a small table with the variables of risk_scores_validation_clean whose first 25 rows
       are 'Review': written by a PROC EXPORT statement of the same form, read by the real
       PROC IMPORT statement of metrics_calculation.sas (taken from the script).
  M    a medians table with non-integer medians, FORMAT BEST32. as feature_engineering.sas
       sets it, exported, then read by the real PROC IMPORT statement of predict.sas.

Observation only. Nothing in legacy/ is changed; the scripts' statements are submitted as
they are, apart from the two path macros (the substitution of judge/run_sas.py).

Usage (from migration/legacy-to-lean):
    uv run --with saspy python experiments/x25_handoff_income_run.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parents[2] / "legacy"
NAME = "x25_handoff_income"
SCRIPTS = ["feature_engineering.sas", "train.sas", "metrics_calculation.sas", "predict.sas"]

H = (",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,"
     "DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,"
     "NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents")
QB1 = [H,
       "1,1,0.766,45,2,0.80,1234567890123,13,0,6,0,2",
       "2,0,0.957,40,0,0.12,2499.9999999999,4,0,0,0,1",
       "3,0,0.658,38,1,0.08,5400.12345678,2,1,0,0,0",
       "4,0,0.233,30,0,0.03,3300,5,0,0,0,0",
       "5,0,0.907,49,1,0.02,63588,7,0,1,0,0",
       "6,0,0.213,74,0,0.37,3500,3,0,1,0,1"]
QB2 = QB1 + ["7,0,0.305,57,0,0.25,NA,8,0,3,0,0"]


def redirect(src: str, data_dir: str, out_dir: str) -> str:
    src, n1 = re.subn(r"%let\s+data_path\s*=\s*[^;]*;", f"%let data_path = {data_dir};", src)
    src, n2 = re.subn(r"%let\s+output_path\s*=\s*[^;]*;", f"%let output_path = {out_dir};", src)
    assert n2 == 1 and n1 <= 1, (n1, n2)
    return src


def statement(script: str, start: str) -> str:
    """One statement group of a script, verbatim: from `start` to the next `run;`."""
    src = (LEGACY / script).read_text()
    i = src.index(start)
    j = src.index("run;", i) + len("run;")
    return src[i:j] + "\n"


def mkdirs(*dirs: str) -> str:
    return "options dlcreatedir;\n" + "".join(f'libname _mk "{d}";\n' for d in dirs) + "libname _mk clear;\n"


def write_file(path: str, lines: list[str]) -> str:
    out = [f'data _null_;\n    file "{path}" lrecl=2000;\n']
    out += [f"    put '{ln}';\n" for ln in lines]
    out.append("run;\n")
    return "".join(out)


def show_file(tag: str, path: str, first: int = 8) -> str:
    return (f'data _null_;\n    infile "{path}" lrecl=5000 obs={first};\n    input;\n'
            f'    put "X25 {tag} FILE [" _infile_ $char400. "]";\nrun;\n')


def qb_blocks(tag: str, lines: list[str], work: str) -> list[str]:
    d, o = f"{work}/x25_{tag}_data", f"{work}/x25_{tag}_out"
    setup = (f"/* ================= X25 SUBMISSION {tag}_SETUP ================= */\n"
             + mkdirs(d, o) + write_file(f"{d}/cs-training.csv", lines))
    script = (f"/* ================= X25 SUBMISSION {tag}_SCRIPT (feature_engineering.sas, paths redirected) ================= */\n"
              + redirect((LEGACY / "feature_engineering.sas").read_text(), d, o))
    after = f"""/* ================= X25 SUBMISSION {tag}_AFTER ================= */
%put X25 {tag} TOTALS columns_ok=&columns_ok bad_rows=&bad_rows duplicate_ids=&duplicate_ids known_incomes=&known_incomes;
title "x25 {tag} work.credit_raw";
proc contents data=work.credit_raw varnum; run;
data _null_;
    set work.credit_raw;
    length ty td $1;
    ty = vtype(MonthlyIncome); td = vtype(NumberOfDependents);
    if ty = 'N' then put "X25 {tag} credit_raw " VAR1= "MonthlyIncome numeric hex=" MonthlyIncome hex16.;
    else put "X25 {tag} credit_raw " VAR1= "MonthlyIncome character [" MonthlyIncome "]";
    put "X25 {tag} credit_raw " VAR1= "NumberOfDependents type=" td;
run;
data _null_;
    set work.credit_raw_clean;
    put "X25 {tag} credit_raw_clean " VAR1= "MonthlyIncome hex=" MonthlyIncome hex16. " best32=" MonthlyIncome best32.;
run;
data _null_;
    set work.credit_train work.credit_validation;
    put "X25 {tag} features " row_id= "monthly_income hex=" monthly_income hex16. " best32=" monthly_income best32.
        " " flag_low_income= "log_monthly_income hex=" log_monthly_income hex16.;
run;
""" + show_file(f"{tag} model_features_train.csv", f"{o}/model_features_train.csv") \
        + show_file(f"{tag} model_features_validation.csv", f"{o}/model_features_validation.csv") \
        + show_file(f"{tag} income_medians.csv", f"{o}/income_medians.csv")
    return [setup, script, after]


COMPARE = """title "x25 FULL compare: {base} (given to PROC EXPORT) with {comp} (delivered by PROC IMPORT)";
proc compare base={base} compare={comp} method=exact novalues listvar maxprint=(20,400); run;
"""


def full_blocks(work: str) -> list[str]:
    d, o = f"{work}/x25_full_data", f"{work}/x25_full_out"
    src = {s: redirect((LEGACY / s).read_text(), d, o) for s in SCRIPTS}
    blocks = []
    blocks.append("/* ================= X25 SUBMISSION FULL_feature_engineering ================= */\n"
                  + src["feature_engineering.sas"])
    blocks.append("""/* ================= X25 SUBMISSION FULL_O1 (after feature_engineering.sas) ================= */
data work.x25_cte; set work.credit_train_export; run;
data work.x25_cve; set work.credit_validation_export; run;
data work.x25_med; set work.income_medians_export; run;
title "x25 FULL work.credit_train_export";
proc contents data=work.x25_cte varnum; run;
""" + show_file("FULL model_features_train.csv", f"{o}/model_features_train.csv", 3)
                  + show_file("FULL income_medians.csv", f"{o}/income_medians.csv", 8))
    blocks.append("/* ================= X25 SUBMISSION FULL_train ================= */\n" + src["train.sas"])
    blocks.append("""/* ================= X25 SUBMISSION FULL_O2 (after train.sas) ================= */
title "x25 FULL work.model_features_train (PROC IMPORT of train.sas)";
proc contents data=work.model_features_train varnum; run;
""" + COMPARE.format(base="work.x25_cte", comp="work.model_features_train")
                  + COMPARE.format(base="work.x25_cve", comp="work.model_features_validation") + """
data work.x25_rsv; set work.risk_scores_validation_clean; run;
data work.x25_rst; set work.risk_scores_train_clean; run;
title "x25 FULL work.risk_scores_validation_clean (given to PROC EXPORT)";
proc contents data=work.x25_rsv varnum; run;
proc sql;
    title "x25 FULL distinct values before export";
    select 'validation' as tab, count(*) as n, count(distinct pd_logistic) as distinct_pd,
           count(distinct credit_risk_score) as distinct_score from work.x25_rsv
    union all
    select 'train', count(*), count(distinct pd_logistic), count(distinct credit_risk_score) from work.x25_rst;
quit;
""" + show_file("FULL risk_scores_validation.csv", f"{o}/risk_scores_validation.csv", 4))
    blocks.append("/* ================= X25 SUBMISSION FULL_metrics_calculation ================= */\n"
                  + src["metrics_calculation.sas"])
    blocks.append("""/* ================= X25 SUBMISSION FULL_O3 (after metrics_calculation.sas) ================= */
title "x25 FULL work.logit_scored_valid (PROC IMPORT of metrics_calculation.sas)";
proc contents data=work.logit_scored_valid varnum; run;
""" + COMPARE.format(base="work.x25_rsv", comp="work.logit_scored_valid")
                  + COMPARE.format(base="work.x25_rst", comp="work.logit_scored_train") + """
proc sql;
    title "x25 FULL distinct values after import";
    select 'validation' as tab, count(*) as n, count(distinct pd_logistic) as distinct_pd,
           count(distinct credit_risk_score) as distinct_score from work.logit_scored_valid
    union all
    select 'train', count(*), count(distinct pd_logistic), count(distinct credit_risk_score) from work.logit_scored_train;
    title "x25 FULL text columns after import (validation)";
    select risk_grade, recommendation, interest_rate, count(*) as n
    from work.logit_scored_valid group by risk_grade, recommendation, interest_rate;
quit;
data _null_;
    merge work.x25_rsv(keep=row_id pd_logistic credit_risk_score rename=(row_id=id0 pd_logistic=pd0 credit_risk_score=sc0))
          work.logit_scored_valid(keep=row_id pd_logistic credit_risk_score);
    if _n_ <= 5 then put "X25 FULL scores row " _n_= id0= row_id= "pd before=" pd0 hex16. " after=" pd_logistic hex16.
        " score before=" sc0 hex16. " after=" credit_risk_score hex16.;
run;
""")
    blocks.append("/* ================= X25 SUBMISSION FULL_predict ================= */\n" + src["predict.sas"])
    blocks.append("""/* ================= X25 SUBMISSION FULL_O4 (after predict.sas) ================= */
title "x25 FULL work.train_income_medians (PROC IMPORT of predict.sas)";
proc contents data=work.train_income_medians varnum; run;
""" + COMPARE.format(base="work.x25_med", comp="work.train_income_medians") + """
data _null_;
    merge work.x25_med(rename=(median_income=m0 overall_median_income=o0)) work.train_income_medians;
    put "X25 FULL medians " age_group= "median before=" m0 hex16. " after=" median_income hex16.
        " overall before=" o0 hex16. " after=" overall_median_income hex16.;
run;
""")
    return blocks


def t_block(work: str) -> str:
    o = f"{work}/x25_t_out"
    imp = statement("metrics_calculation.sas", 'proc import datafile="&output_path/risk_scores_validation.csv"')
    return ("/* ================= X25 SUBMISSION T (text columns and ties through the score file) ================= */\n"
            + mkdirs(o) + f"%let output_path = {o};\n" + """
data work.x25_t;
    length risk_grade $1 recommendation $7;
    format row_id default_flag best12.;
    do row_id = 1 to 30;
        default_flag = (mod(row_id, 7) = 0);
        if row_id <= 25 then do; pd_logistic = 0.2 + row_id * 1e-13; risk_grade = 'C'; end;
        else if row_id = 26 then do; pd_logistic = 1 / 30; risk_grade = 'A'; end;
        else if row_id = 27 then do; pd_logistic = 0.3; risk_grade = 'D'; end;
        else if row_id = 28 then do; pd_logistic = 2 / 3; risk_grade = 'F'; end;
        else if row_id = 29 then do; pd_logistic = 0.12; risk_grade = 'B'; end;
        else do; pd_logistic = 0.4; risk_grade = 'E'; end;
        credit_risk_score = 600 + 250 * (1 - pd_logistic);
        if risk_grade in ('A', 'B') then recommendation = 'Approve';
        else if risk_grade = 'C' then recommendation = 'Review';
        else recommendation = 'Decline';
        base_rate = 0.05;
        if risk_grade = 'A' then interest_rate = base_rate;
        else if risk_grade = 'B' then interest_rate = base_rate + 0.02;
        else if risk_grade = 'C' then interest_rate = base_rate + 0.04;
        else if risk_grade = 'D' then interest_rate = base_rate + 0.07;
        else if risk_grade = 'E' then interest_rate = base_rate + 0.10;
        else interest_rate = base_rate + 0.15;
        output;
    end;
    format interest_rate percent8.2;
run;
/* the form of train.sas 370-374 */
proc export data=work.x25_t
    outfile="&output_path/risk_scores_validation.csv"
    dbms=csv
    replace;
run;
""" + show_file("T risk_scores_validation.csv", f"{o}/risk_scores_validation.csv", 31)
            + "/* metrics_calculation.sas, verbatim */\n" + imp + """
title "x25 T work.logit_scored_valid (PROC IMPORT of metrics_calculation.sas)";
proc contents data=work.logit_scored_valid varnum; run;
proc print data=work.logit_scored_valid(firstobs=24); run;
data _null_;
    merge work.x25_t(keep=row_id pd_logistic credit_risk_score interest_rate recommendation
                     rename=(pd_logistic=pd0 credit_risk_score=sc0 interest_rate=ir0 recommendation=rec0))
          work.logit_scored_valid;
    length ti $1;
    ti = vtype(interest_rate);
    put "X25 T row " row_id= "pd before=" pd0 hex16. " after=" pd_logistic hex16. " score before=" sc0 hex16.
        " after=" credit_risk_score hex16. " rec before=[" rec0 +(-1) "] after=[" recommendation +(-1) "] interest_rate type=" ti
        " before=" ir0 hex16. " after=" interest_rate;
run;
proc sql;
    title "x25 T distinct pd before and after";
    select (select count(distinct pd_logistic) from work.x25_t) as distinct_pd_before,
           (select count(distinct pd_logistic) from work.logit_scored_valid) as distinct_pd_after
    from work.x25_t(obs=1);
quit;
""")


def m_block(work: str) -> str:
    o = f"{work}/x25_m_out"
    imp = statement("predict.sas", 'proc import datafile="&output_path/income_medians.csv"')
    return ("/* ================= X25 SUBMISSION M (medians through income_medians.csv) ================= */\n"
            + mkdirs(o) + f"%let output_path = {o};\n" + """
data work.income_medians_all;
    age_group = 1; median_income = 1234567.123456789; overall_median_income = 5400.12345678; output;
    age_group = 2; median_income = .; output;
    age_group = 3; median_income = 2499.9999999999; output;
    age_group = 4; median_income = (5400.1 + 5400.2) / 2; output;
    age_group = 5; median_income = 1234567890123.5; output;
run;
/* feature_engineering.sas 382-391, the same statements */
data work.income_medians_export;
    set work.income_medians_all;
    format median_income overall_median_income best32.;
run;
proc export data=work.income_medians_export
    outfile="&output_path/income_medians.csv"
    dbms=csv
    replace;
run;
""" + show_file("M income_medians.csv", f"{o}/income_medians.csv", 8)
            + "/* predict.sas, verbatim */\n" + imp + """
title "x25 M work.train_income_medians (PROC IMPORT of predict.sas)";
proc contents data=work.train_income_medians varnum; run;
data _null_;
    merge work.income_medians_export(rename=(median_income=m0 overall_median_income=o0)) work.train_income_medians;
    put "X25 M medians " age_group= "median before=" m0 hex16. " after=" median_income hex16.
        " overall before=" o0 hex16. " after=" overall_median_income hex16.;
run;
""")


def main() -> int:
    import saspy
    sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    header = (f"X25 RUN saspy={saspy.__version__} (uv run --with saspy, not pinned to the judge's) "
              f"python={sys.version.split()[0]} profile=oda_eu sasver={sas.sasver}\n")
    log, lst, progs = [header], [], []
    try:
        first = sas.submit("%put X25 SYSVLONG=&sysvlong VALIDVARNAME=%sysfunc(getoption(validvarname));\n"
                           "%put X25WORK=%sysfunc(pathname(work));")["LOG"]
        log.append(first)
        work = next(l.split("=", 1)[1].strip() for l in first.splitlines() if l.startswith("X25WORK="))
        (HERE / f"{NAME}_QB1.csv").write_text("\n".join(QB1) + "\n")
        (HERE / f"{NAME}_QB2.csv").write_text("\n".join(QB2) + "\n")
        progs += qb_blocks("QB1", QB1, work) + qb_blocks("QB2", QB2, work)
        progs += [t_block(work), m_block(work)]
        d, o = f"{work}/x25_full_data", f"{work}/x25_full_out"
        progs.append("/* ================= X25 SUBMISSION FULL_SETUP (legacy/data uploaded) ================= */\n"
                     + mkdirs(d, o) + f'ods listing gpath="{work}";\n')
        progs += full_blocks(work)
        (HERE / f"{NAME}.sas").write_text(
            "/* x25: generated by x25_handoff_income_run.py; each SUBMISSION block is submitted on its own,\n"
            "   in order, in one session. Script blocks are the legacy scripts with the two path macros\n"
            "   redirected; the other blocks are observation. */\n" + "".join(progs))
        for p in progs:
            if "SUBMISSION FULL_feature_engineering" in p:
                for f in ("cs-training.csv", "cs-test.csv"):
                    res = sas.upload(str(LEGACY / "data" / f), f"{d}/{f}", overwrite=True)
                    if not res.get("Success"):
                        raise RuntimeError(f"upload failed: {res}")
            res = sas.submit(p)
            log.append(res["LOG"])
            lst.append(res["LST"])
            print(p.splitlines()[0], flush=True)
            for ln in res["LOG"].splitlines():
                if ln.startswith(("X25", "ERROR")):
                    print("   ", ln[:300], flush=True)
    finally:
        sas.endsas()
        (HERE / f"{NAME}.log").write_text("\n".join(log))
        (HERE / f"{NAME}.lst").write_text("\n".join(lst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
