/*****************************************************************************
 * Credit Risk Scoring Model - Model Validation
 *
 * Purpose: Comprehensive validation of credit risk model performance
 * Author: Risk Analytics Team
 * Date: 2025
 *
 * Data Source: Kaggle "Give Me Some Credit" competition
 *
 * Validation includes:
 * - ROC curve and AUC calculation
 * - Gini coefficient
 * - KS statistic
 * - Confusion matrix and accuracy metrics
 * - Decile analysis and lift charts
 * - Population Stability Index (PSI)
 * - Calibration plots
 *****************************************************************************/

/* Define output path */
%let output_path = /home/u64352077/output;

/* Remove the results of an earlier run first: a run that stops leaves no result */
data _null_;
    length fref $8 fname $64;
    do fname = 'validation_summary.csv', 'decile_analysis.csv', 'threshold_analysis.csv',
               'ks_statistic.csv', 'calibration_plot.csv', 'model_performance_metrics.csv';
        fref = ' ';
        if filename(fref, cats("&output_path/", fname)) = 0 then do;
            if fexist(fref) then rc = fdelete(fref);
            rc = filename(fref);
        end;
    end;
run;

/* Stop when the step before did not produce its result */
data _null_;
    if not fileexist("&output_path/risk_scores_train.csv")
       or not fileexist("&output_path/risk_scores_validation.csv") then do;
        put "ERROR: The score files are not in the output folder: model training did not complete.";
        put "ERROR: Model validation stopped. Nothing is exported.";
        abort cancel;
    end;
run;

/*****************************************************************************
 * 1. Load Scored Data
 *****************************************************************************/

/* Read scored validation data */
proc import datafile="&output_path/risk_scores_validation.csv"
    out=work.logit_scored_valid
    dbms=csv
    replace;
    getnames=yes;
run;

/* Read scored training data (needed for PSI) */
proc import datafile="&output_path/risk_scores_train.csv"
    out=work.logit_scored_train
    dbms=csv
    replace;
    getnames=yes;
run;

/*****************************************************************************
 * 2. ROC Curve and AUC Analysis
 *****************************************************************************/

/* ROC analysis for validation set */
proc logistic data=work.logit_scored_valid;
    model default_flag(event='1') = pd_logistic / nofit;
    roc 'Logistic Model' pred=pd_logistic;
    roccontrast;
    ods output ROCAssociation=work.roc_stats;
    title "ROC Curve Analysis - Validation Set";
run;

/* Calculate and display AUC: the exact pairwise AUC of the validation probabilities.
   A defaulter/non-defaulter pair is concordant when the defaulter's probability is
   higher, and tied only when the two probabilities are equal */
proc sql;
    create table work.auc_pairs as
    select pd_logistic,
           sum(default_flag = 1) as n_bad,
           sum(default_flag = 0) as n_good
    from work.logit_scored_valid
    where not missing(pd_logistic)
    group by pd_logistic
    order by pd_logistic;
quit;

data work.auc_summary;
    length ROCModel $14;
    set work.auc_pairs end=eof;
    retain concordant tied cum_good cum_bad 0;

    concordant + n_bad * cum_good;
    tied + n_bad * n_good;
    cum_good + n_good;
    cum_bad + n_bad;

    if eof then do;
        ROCModel = 'Logistic Model';
        if cum_bad * cum_good > 0 then do;
            AUC = (concordant + tied / 2) / (cum_bad * cum_good);
            Gini = 2 * AUC - 1;
        end;
        output;
    end;
    keep ROCModel AUC Gini;
    format AUC Gini 8.4;
run;

proc print data=work.auc_summary noobs;
    title "Model Performance Metrics - AUC and Gini";
run;

/*****************************************************************************
 * 3. Kolmogorov-Smirnov (KS) Statistic
 *****************************************************************************/

/* Sort by predicted probability */
proc sort data=work.logit_scored_valid;
    by pd_logistic;
run;

/* Calculate total good and bad counts */
proc sql noprint;
    select sum(default_flag = 0), sum(default_flag = 1)
    into :total_good_count, :total_bad_count
    from work.logit_scored_valid;
quit;

/* Calculate cumulative distributions */
data work.ks_calculation;
    set work.logit_scored_valid;
    by pd_logistic;
    retain cum_good cum_bad;

    if _n_ = 1 then do;
        cum_good = 0;
        cum_bad = 0;
    end;

    if default_flag = 0 then cum_good + 1;
    else cum_bad + 1;

    cum_pct_good = cum_good / &total_good_count;
    cum_pct_bad = cum_bad / &total_bad_count;
    /* Compare the two distributions only after the last applicant of each probability */
    if last.pd_logistic then ks_value = abs(cum_pct_good - cum_pct_bad);
run;

/* Find maximum KS (one row: the lowest cutoff when several attain the maximum) */
proc sql;
    create table work.ks_statistic as
    select max(ks_value) as KS_Statistic format=8.4,
           min(pd_logistic) as KS_Cutoff format=8.4
    from work.ks_calculation
    where ks_value = (select max(ks_value) from work.ks_calculation);
quit;

proc print data=work.ks_statistic noobs;
    title "Kolmogorov-Smirnov Statistic";
run;

/*****************************************************************************
 * 4. Confusion Matrix and Accuracy Metrics
 *****************************************************************************/

/* Calculate metrics at different thresholds */
%macro confusion_metrics(threshold, suffix);
    data work.confusion_&suffix;
        set work.logit_scored_valid;
        predicted = (pd_logistic >= &threshold);
    run;

    proc freq data=work.confusion_&suffix noprint;
        tables default_flag * predicted / out=work.conf_matrix_&suffix;
    run;

    /* Calculate metrics */
    data work.metrics_&suffix;
        set work.conf_matrix_&suffix end=eof;
        retain TP TN FP FN 0;

        if default_flag = 1 and predicted = 1 then TP = count;
        else if default_flag = 0 and predicted = 0 then TN = count;
        else if default_flag = 0 and predicted = 1 then FP = count;
        else if default_flag = 1 and predicted = 0 then FN = count;

        if eof then do;
            threshold = &threshold;
            if (TP + TN + FP + FN) > 0 then accuracy = (TP + TN) / (TP + TN + FP + FN);
            else accuracy = .;
            if (TP + FP) > 0 then precision = TP / (TP + FP);
            else precision = .;
            if (TP + FN) > 0 then recall = TP / (TP + FN);
            else recall = .;
            if (precision + recall) > 0 then f1_score = 2 * (precision * recall) / (precision + recall);
            else f1_score = .;
            if (TN + FP) > 0 then specificity = TN / (TN + FP);
            else specificity = .;
            output;
        end;
        keep threshold accuracy precision recall f1_score specificity;
    run;
%mend;

/* Test multiple thresholds */
%confusion_metrics(0.3, 03);
%confusion_metrics(0.4, 04);
%confusion_metrics(0.5, 05);
%confusion_metrics(0.6, 06);
%confusion_metrics(0.7, 07);

/* Combine results */
data work.threshold_analysis;
    set work.metrics_03 work.metrics_04 work.metrics_05
        work.metrics_06 work.metrics_07;
run;

proc print data=work.threshold_analysis;
    title "Performance Metrics at Different Thresholds";
    format accuracy precision recall f1_score specificity 8.4;
run;

/*****************************************************************************
 * 5. Decile Analysis and Lift Chart
 *****************************************************************************/

/* Create deciles based on predicted probability */
proc rank data=work.logit_scored_valid
          out=work.decile_data
          groups=10 descending;
    var pd_logistic;
    ranks decile;
run;

/* Always ten rows, deciles 1 to 10 */
data work.decile_list;
    do decile = 1 to 10;
        output;
    end;
run;

/* Calculate lift by decile; a decile that receives no applicant has
   count 0, capture rate 0 and lift 0 */
proc sql;
    create table work.decile_analysis as
    select
        l.decile,
        coalesce(d.total_count, 0) as total_count,
        coalesce(d.defaults, 0) as defaults,
        d.default_rate format=percent8.2,
        d.avg_pd format=8.4,
        d.min_pd format=8.4,
        d.max_pd format=8.4,
        case when d.decile is null then 0 else d.capture_rate end as capture_rate format=percent8.2,
        case when d.decile is null then 0 else d.lift end as lift format=8.2
    from work.decile_list l
    left join
        (select
            decile + 1 as decile,
            count(*) as total_count,
            sum(default_flag) as defaults,
            mean(default_flag) as default_rate,
            mean(pd_logistic) as avg_pd,
            min(pd_logistic) as min_pd,
            max(pd_logistic) as max_pd,
            sum(default_flag) / (select sum(default_flag) from work.decile_data) as capture_rate,
            (calculated default_rate) / (select mean(default_flag) from work.decile_data) as lift
         from work.decile_data
         group by decile) d
    on l.decile = d.decile
    order by l.decile;
quit;

proc print data=work.decile_analysis;
    title "Decile Analysis - Model Lift and Capture Rate";
run;

/* Calculate totals for cumulative lift chart */
proc sql noprint;
    select sum(default_flag), mean(default_flag)
    into :total_defaults, :overall_default_rate
    from work.decile_data;
quit;

/* Create cumulative lift chart */
data work.cumulative_lift;
    set work.decile_analysis;
    retain cum_defaults cum_count;
    if _n_ = 1 then do;
        cum_defaults = defaults;
        cum_count = total_count;
    end;
    else do;
        cum_defaults + defaults;
        cum_count + total_count;
    end;

    cum_capture_rate = cum_defaults / &total_defaults;
    /* No cumulative lift while the deciles so far are empty */
    if cum_count > 0 then cum_lift = (cum_defaults / cum_count) / &overall_default_rate;
    format cum_capture_rate percent8.2 cum_lift 8.2;
run;

proc sgplot data=work.cumulative_lift;
    series x=decile y=cum_lift;
    refline 1 / axis=y;
    xaxis label="Decile";
    yaxis label="Cumulative Lift";
    title "Cumulative Lift Chart";
run;

/*****************************************************************************
 * 6. Population Stability Index (PSI)
 *****************************************************************************/

/* Compare score distributions between training and validation */

/* Ten bins cut from the training scores: the nine cuts are the nearest-rank
   deciles of the training scores (no interpolation) */
proc sort data=work.logit_scored_train(keep=credit_risk_score)
          out=work.train_scores_sorted;
    by credit_risk_score;
run;

data work.psi_cuts;
    set work.train_scores_sorted nobs=n_train end=eof;
    array cut{9};
    retain cut1-cut9;
    do k = 1 to 9;
        if _n_ = ceil(k * n_train / 10) then cut{k} = credit_risk_score;
    end;
    if eof then output;
    keep cut1-cut9;
run;

/* Place both sets in the same bins; a score equal to a cut belongs to the lower bin */
data work.train_bins;
    if _n_ = 1 then set work.psi_cuts;
    set work.logit_scored_train;
    array cut{9};
    score_bin = 0;
    do k = 1 to 9;
        if credit_risk_score > cut{k} then score_bin = score_bin + 1;
    end;
    drop k cut1-cut9;
run;

data work.valid_bins;
    if _n_ = 1 then set work.psi_cuts;
    set work.logit_scored_valid;
    array cut{9};
    score_bin = 0;
    do k = 1 to 9;
        if credit_risk_score > cut{k} then score_bin = score_bin + 1;
    end;
    drop k cut1-cut9;
run;

data work.psi_bins;
    do score_bin = 0 to 9;
        output;
    end;
run;

/* An empty bin is given a share below that of one applicant, the same on both
   sides, so that a bin filled on one side only adds a positive amount */
proc sql noprint;
    select 0.5 / max(t.n, v.n) into :psi_floor trimmed
    from (select count(*) as n from work.train_bins) t,
         (select count(*) as n from work.valid_bins) v;
quit;

/* Calculate PSI */
proc sql;
    create table work.psi_calculation as
    select
        s.score_bin,
        coalesce(a.train_pct, 0) as train_pct,
        coalesce(b.valid_pct, 0) as valid_pct,
        (max(calculated train_pct, &psi_floor) - max(calculated valid_pct, &psi_floor))
            * log(max(calculated train_pct, &psi_floor) / max(calculated valid_pct, &psi_floor)) as psi_component
    from work.psi_bins s
    left join
        (select score_bin, count(*) / (select count(*) from work.train_bins) as train_pct
         from work.train_bins group by score_bin) a
    on s.score_bin = a.score_bin
    left join
        (select score_bin, count(*) / (select count(*) from work.valid_bins) as valid_pct
         from work.valid_bins group by score_bin) b
    on s.score_bin = b.score_bin
    order by s.score_bin;

    create table work.psi_summary as
    select sum(psi_component) as PSI format=best12.,
           case
              when calculated PSI < 0.1 then 'No significant change'
              when calculated PSI < 0.25 then 'Some change'
              else 'Significant change'
           end as PSI_interpretation
    from work.psi_calculation;
quit;

proc print data=work.psi_summary noobs;
    title "Population Stability Index";
run;

/*****************************************************************************
 * 7. Calibration Plot
 *****************************************************************************/

/* Bin predictions and compare to actual */
proc rank data=work.logit_scored_valid
          out=work.calibration_data
          groups=20;
    var pd_logistic;
    ranks pred_bin;
run;

proc sql;
    create table work.calibration_plot as
    select
        pred_bin,
        mean(pd_logistic) as mean_predicted format=8.4,
        mean(default_flag) as mean_actual format=8.4,
        count(*) as bin_count
    from work.calibration_data
    group by pred_bin
    order by pred_bin;
quit;

proc sgplot data=work.calibration_plot;
    scatter x=mean_predicted y=mean_actual / markerattrs=(size=10);
    lineparm x=0 y=0 slope=1 / lineattrs=(pattern=dash);
    xaxis label="Mean Predicted Probability";
    yaxis label="Mean Actual Default Rate";
    title "Calibration Plot - Predicted vs Actual";
run;

/*****************************************************************************
 * 8. Generate Validation Report
 *****************************************************************************/

/* Compile validation metrics */
data work.validation_summary;
    merge work.auc_summary
          work.ks_statistic
          work.psi_summary;
    length model $20 status $20;
    model = "Logistic Regression";

    /* Determine model status based on metrics */
    if AUC >= 0.7 and KS_Statistic >= 0.3 and PSI < 0.25 then
        status = "Production Ready";
    else if AUC >= 0.65 then
        status = "Requires Review";
    else
        status = "Needs Improvement";
run;

proc print data=work.validation_summary noobs;
    title "Model Validation Summary";
run;

/*****************************************************************************
 * 9. Export Validation Results
 *****************************************************************************/

/* Export validation summary */
proc export data=work.validation_summary
    outfile="&output_path/validation_summary.csv"
    dbms=csv
    replace;
run;

/* Export decile analysis */
proc export data=work.decile_analysis
    outfile="&output_path/decile_analysis.csv"
    dbms=csv
    replace;
run;

/* Export threshold analysis */
proc export data=work.threshold_analysis
    outfile="&output_path/threshold_analysis.csv"
    dbms=csv
    replace;
run;

/* Export KS statistics */
proc export data=work.ks_statistic
    outfile="&output_path/ks_statistic.csv"
    dbms=csv
    replace;
run;

/* Export calibration plot data */
proc export data=work.calibration_plot
    outfile="&output_path/calibration_plot.csv"
    dbms=csv
    replace;
run;

/* Create comprehensive model performance metrics dataset */
data work.model_performance_metrics;
    merge work.auc_summary
          work.ks_statistic
          work.psi_summary
          work.threshold_analysis(where=(threshold=0.5) rename=(accuracy=acc_50 precision=prec_50 recall=rec_50 f1_score=f1_50 specificity=spec_50));

    /* Add metadata */
    model_name = "Logistic Regression";
    validation_date = today();
    dataset = "Kaggle Give Me Some Credit";

    /* Rename for clarity */
    rename acc_50 = accuracy_at_50
           prec_50 = precision_at_50
           rec_50 = recall_at_50
           f1_50 = f1_score_at_50
           spec_50 = specificity_at_50;

    format validation_date date9.;

    /* Keep relevant variables */
    drop threshold ROCModel;
run;

/* Export comprehensive metrics */
proc export data=work.model_performance_metrics
    outfile="&output_path/model_performance_metrics.csv"
    dbms=csv
    replace;
run;

/* Print summary of saved metrics */
proc print data=work.model_performance_metrics noobs;
    title "Model Performance Metrics - Saved to Output Folder";
run;

%put NOTE: Model validation completed successfully;
%put NOTE: Validation metrics calculated and exported;
%put NOTE: Results saved to: &output_path;
%put NOTE: Check validation_summary.csv for overall performance;
