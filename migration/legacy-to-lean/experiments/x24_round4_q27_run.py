"""x24: the input checks of the CURRENT legacy/feature_engineering.sas (PROC IMPORT of
cs-training.csv, columns check, row check, stop) on small training files, for Q27.

Builds experiments/x24_round4_q27.sas from the legacy script (the statements from the
PROC IMPORT of cs-training.csv to the end of the stopping step, verbatim), writes the
input files next to it, submits one case per submission (ABORT CANCEL cancels the rest
of a submission) in ONE session of SAS OnDemand (profile oda_eu, as judge/run_sas.py and
run_experiment.py), and saves the log and the listing.

Observation only. Added to the script's statements, and marked X24 in the .sas:
  * before: the file is written to the WORK folder and data_path points there;
  * after the script's PROC IMPORT step: PROC CONTENTS, PROC PRINT, the rows in the log;
  * after the script's second PROC SQL: a %PUT of the four totals;
  * after the stopping step: a step that creates work.x24_after_<case>; the next
    submission reports whether it exists (it does not when the script stopped).

Usage (from migration/legacy-to-lean):
    uv run --project ../../judge python experiments/x24_round4_q27_run.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parents[2] / "legacy" / "feature_engineering.sas"
NAME = "x24_round4_q27"

H = (",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,"
     "DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,"
     "NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents")
R1 = "1,1,0.766,45,2,0.80,9120,13,0,6,0,2"
R2 = "2,0,0.957,40,0,0.12,NA,4,0,0,0,1"
R3 = "3,0,0.658,38,1,0.08,3042,2,1,0,0,NA"


def ids(a, b, c):
    return [H] + [i + r[1:] for i, r in zip((a, b, c), (R1, R2, R3))]


CASES = {
    "A": [H.replace(",age,", ",AGE,"), R1],
    "B": [H, R1, "2,0,0.957,40,0,0.12345678901234567890123456789012345,NA,4,0,0,0,1", R3],
    "C": [H, R1, '2,0,0.957,"45",0,0.12,NA,4,0,0,0,1', R3],
    "C2": [H, R1, "2,0,0.957,4.5e1,0,0.12,NA,4,0,0,0,1", R3],
    "D": ids("7", "07", "8"),
    "D2": ids("7", "7.0", "8"),
    "D3": ids("7", "+7", "8"),
    "E": [H, R1, R2 + ",9", R3],
    "E2": [H, R1, "2,0,0.957,40,0,0.12,NA,4,0,0,0", R3],
}

OBSERVE_TABLE = """
/* X24 observation (not in the script): the imported table */
%macro x24_show(v);
    %local dsid pos vtype;
    %let vtype = none;
    %let dsid = %sysfunc(open(work.credit_raw));
    %if &dsid > 0 %then %do;
        %let pos = %sysfunc(varnum(&dsid, &v));
        %if &pos > 0 %then %let vtype = %sysfunc(vartype(&dsid, &pos));
        %let dsid = %sysfunc(close(&dsid));
    %end;
    %if &vtype = N %then %do; put "X24 @CASE@ &v numeric " "&v"n best32. " hex=" "&v"n hex16.; %end;
    %else %if &vtype = C %then %do; x24_len = lengthn("&v"n); put "X24 @CASE@ &v character [" "&v"n +(-1) "] " x24_len=; %end;
    %else %do; put "X24 @CASE@ &v absent"; %end;
%mend;
title "x24 @CASE@ work.credit_raw";
proc contents data=work.credit_raw varnum; run;
proc print data=work.credit_raw; format _numeric_ best32.; run;
data _null_;
    set work.credit_raw;
    put "X24 @CASE@ ROW " _n_= (_all_)(=);
    %x24_show(VAR1)
    %x24_show(age)
    %x24_show(DebtRatio)
    %x24_show(NumberOfDependents)
run;
/* X24 end of observation */
"""

OBSERVE_TOTALS = """
/* X24 observation (not in the script): the totals */
%put X24 @CASE@ TOTALS columns_ok=&columns_ok bad_rows=&bad_rows duplicate_ids=&duplicate_ids known_incomes=&known_incomes;
proc print data=work.input_check; title "x24 @CASE@ work.input_check"; run;
/* X24 end of observation */
"""


def legacy_check() -> tuple[str, str, str]:
    """The script's statements, verbatim, cut at the two observation points."""
    src = LEGACY.read_text()
    start = src.index('proc import datafile="&data_path/cs-training.csv"')
    cut1 = src.index("/* Check the input conditions", start)
    cut2 = src.index("data _null_;\n    if &columns_ok ne 1", cut1)
    end = src.index("abort cancel;", cut2)
    end = src.index("run;\n", end) + len("run;\n")
    return src[start:cut1], src[cut1:cut2], src[cut2:end]


def program(case: str, lines: list[str], previous: str | None, parts) -> str:
    imp, checks, stop = parts
    out = [f"/* ================= X24 SUBMISSION {case} ================= */\n"]
    if previous:
        out.append(f"%put X24 {previous} STEP_AFTER_STOP_RAN=%sysfunc(exist(work.x24_after_{previous}));\n")
    out.append("proc datasets lib=work nolist; delete credit_raw input_check; quit;\n")
    out.append("%let data_path = %sysfunc(pathname(work));\n")
    out.append('data _null_;\n    file "&data_path/cs-training.csv" lrecl=1000;\n')
    for ln in lines:
        assert "'" not in ln
        out.append(f"    put '{ln}';\n")
    out.append("run;\n")
    out.append('data _null_;\n    infile "&data_path/cs-training.csv" lrecl=1000 length=n;\n    input;\n'
               f'    put "X24 {case} FILE [" _infile_ +(-1) "] " n=;\nrun;\n')
    out.append(f"/* X24 {case}: feature_engineering.sas, verbatim from here */\n")
    out.append(imp)
    out.append(OBSERVE_TABLE.replace("@CASE@", case))
    out.append(checks)
    out.append(OBSERVE_TOTALS.replace("@CASE@", case))
    out.append(stop)
    out.append(f"/* X24 {case}: end of the script's statements */\n")
    out.append(f"data work.x24_after_{case}; run;\n")
    return "".join(out)


def full_script_run(lines: list[str], work: str) -> list[str]:
    """File A through the real feature_engineering.sas: the script as it stands, only its
    two path macros redirected (as judge/run_sas.py does), in a submission of its own."""
    import re
    data_dir, out_dir = f"{work}/x24_data", f"{work}/x24_out"
    src = LEGACY.read_text()
    src, n1 = re.subn(r"%let\s+data_path\s*=\s*[^;]*;", f"%let data_path = {data_dir};", src)
    src, n2 = re.subn(r"%let\s+output_path\s*=\s*[^;]*;", f"%let output_path = {out_dir};", src)
    assert n1 == 1 and n2 == 1
    setup = ["/* ================= X24 SUBMISSION A_FULL_SETUP ================= */\n",
             f'options dlcreatedir;\nlibname _mk "{data_dir}"; libname _mk "{out_dir}"; libname _mk clear;\n',
             f'ods listing gpath="{work}";\n',
             f'data _null_;\n    file "{data_dir}/cs-training.csv" lrecl=1000;\n']
    setup += [f"    put '{ln}';\n" for ln in lines]
    setup.append("run;\n")
    after = f"""/* ================= X24 SUBMISSION A_FULL_AFTER ================= */
%put X24 A_FULL AFTER syscc=&syscc columns_ok=&columns_ok bad_rows=&bad_rows duplicate_ids=&duplicate_ids known_incomes=&known_incomes;
data _null_;
    length fname $200 line $2000;
    rc = filename('x24d', "{out_dir}");
    did = dopen('x24d');
    n = dnum(did);
    put 'X24 A_FULL OUTPUT_FOLDER files=' n;
    do i = 1 to n;
        fname = dread(did, i);
        put 'X24 A_FULL OUTPUT_FILE ' fname;
    end;
    rc = dclose(did);
run;
%macro x24_dump(f);
    %if %sysfunc(fileexist({out_dir}/&f)) %then %do;
        data _null_;
            infile "{out_dir}/&f" lrecl=5000 length=n;
            input;
            put "X24 A_FULL &f [" _infile_ +(-1) "]";
        run;
    %end;
    %else %put X24 A_FULL &f DOES NOT EXIST;
%mend;
%x24_dump(income_medians.csv)
%x24_dump(model_features_train.csv)
%x24_dump(model_features_validation.csv)
"""
    return ["".join(setup),
            "/* ================= X24 SUBMISSION A_FULL_SCRIPT (feature_engineering.sas, paths redirected) ================= */\n" + src,
            after]


def main() -> int:
    parts = legacy_check()
    for case, lines in CASES.items():
        (HERE / f"{NAME}_{case}.csv").write_text("\n".join(lines) + "\n")
    progs, prev = [], None
    for case, lines in CASES.items():
        progs.append(program(case, lines, prev, parts))
        prev = case
    progs.append("/* ================= X24 SUBMISSION END ================= */\n"
                 f"%put X24 {prev} STEP_AFTER_STOP_RAN=%sysfunc(exist(work.x24_after_{prev}));\n")
    work = "<WORK>"
    if "--dry" not in sys.argv:
        import saspy
        sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
        first = sas.submit("%put X24 SYSVLONG=&sysvlong VALIDVARNAME=%sysfunc(getoption(validvarname));\n"
                           "%put X24WORK=%sysfunc(pathname(work));")["LOG"]
        work = next(l.split("=", 1)[1].strip() for l in first.splitlines() if l.startswith("X24WORK="))
    progs += full_script_run(CASES["A"], work)
    (HERE / f"{NAME}.sas").write_text(
        "/* x24: generated by x24_round4_q27_run.py; each SUBMISSION block is submitted on its own,\n"
        "   in order, in one session. The statements between 'verbatim from here' and 'end of the\n"
        "   script''s statements' are those of legacy/feature_engineering.sas, with the X24\n"
        "   observation blocks inserted. */\n" + "".join(progs))
    if "--dry" in sys.argv:
        return 0
    header = (f"X24 RUN saspy={saspy.__version__} (uv run --with saspy, not pinned to the judge's) "
              f"python={sys.version.split()[0]} profile=oda_eu sasver={sas.sasver}\n")
    log, lst = [header, first], []
    try:
        for p in progs:
            res = sas.submit(p)
            log.append(res["LOG"])
            lst.append(res["LST"])
    finally:
        sas.endsas()
    (HERE / f"{NAME}.log").write_text("\n".join(log))
    (HERE / f"{NAME}.lst").write_text("\n".join(lst))
    for ln in "\n".join(log).splitlines():
        if ln.startswith(("X24", "ERROR", "WARNING")) and " ROW " not in ln:
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
