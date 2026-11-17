    fs_step: list[str] = ["0"]
    fs_rowid: list[str] = ["M2LOGL0"]
    fs_criterion: list[str] = ["-2 Log L"]
    fs_equals: list[str] = ["="]
    fs_only: list[str] = [sas_compat.sas_d12_3(m2ll0)]  # R§2 S6: the one D12.3 helper
    fs_cov: list[str] = [sas_compat.fmt_wd(m2ll0, 9, 3)]
    # ODS GlobalTests -> printed_global_tests.csv  # INV printed_global_tests.csv
    # (complete cases only: the global tests come from the fit on fit_frame)
    # stored formats: Test $16., ChiSq 10.4, DF 4., ProbChiSq pvalue6.4 (S7)
    gt_step: list[str] = []
    gt_test: list[str] = []
    gt_chisq: list[str] = []
    gt_df: list[str] = []
    gt_prob: list[str] = []
    # ODS RSquare -> printed_rsquare.csv  # INV printed_rsquare.csv
    # stored formats: cValue $6., nValue d12.3 (S7)
    rs_step: list[str] = []
    rs_label1: list[str] = []
    rs_cvalue1: list[str] = []
    rs_nvalue1: list[str] = []
    rs_label2: list[str] = []
    rs_cvalue2: list[str] = []
    rs_nvalue2: list[str] = []
    for st in stepwise.steps:
        names_k = st.fit.names
        q = len(names_k) - 1  # effects in the model, intercept not counted
        if q == 0:
            # a step that removes the last variable: SAS prints for it what it prints for step 0, the
            # one -2 Log L line, and no global tests or R-square row (small-inputs.md (e))
            fs_step.append(str(st.step))
            fs_rowid.append("M2LOGL0")
            fs_criterion.append("-2 Log L")
            fs_equals.append("=")
            fs_only.append(sas_compat.sas_d12_3(m2ll0))
            fs_cov.append(sas_compat.fmt_wd(m2ll0, 9, 3))
            continue
        m2ll = -2.0 * st.fit.loglik
        x_k = np.column_stack(
            [
                np.ones(n_obs),
                *[np.asarray(fit_frame.get_column(c).to_numpy(), dtype=np.float64) for c in names_k[1:]],
            ]
        )
        # fit statistics: AIC, SC, -2 Log L for each step
        fs_step.extend([str(st.step)] * 3)
        fs_rowid.extend(["AIC", "SBC", "M2LOGL"])
        fs_criterion.extend(["AIC", "SC", "-2 Log L"])
        fs_equals.extend(["", "", ""])
        fs_only.extend(
            [
                sas_compat.sas_d12_3(m2ll0 + 2.0),
                sas_compat.sas_d12_3(m2ll0 + math.log(n_obs)),
                sas_compat.sas_d12_3(m2ll0),
            ]
        )
        fs_cov.extend(
            [
                sas_compat.fmt_wd(m2ll + 2.0 * (q + 1), 9, 3),
                sas_compat.fmt_wd(m2ll + (q + 1) * math.log(n_obs), 9, 3),
                sas_compat.fmt_wd(m2ll, 9, 3),
            ]
        )
        # global tests: likelihood ratio, score (at the intercept-only fit), Wald
        lr = m2ll0 - m2ll
        u0 = x_k.T @ (y_train - ybar)
        i0 = ybar * (1.0 - ybar) * (x_k.T @ x_k)
        score = float(u0 @ np.linalg.solve(i0, u0))
        b_slope = st.fit.beta[1:]
        wald = float(b_slope @ np.linalg.solve(st.fit.cov[1:, 1:], b_slope))
        for test, stat in (("Likelihood Ratio", lr), ("Score", score), ("Wald", wald)):
            gt_step.append(str(st.step))
            gt_test.append(test)
            gt_chisq.append(sas_compat.fmt_wd(stat, 10, 4))
            gt_df.append(str(q))
            gt_prob.append(sas_compat.sas_pvalue(sas_compat.chi2_sf(stat, q)))
        # R-square: Cox-Snell and Nagelkerke (max-rescaled)
        cox_snell = 1.0 - math.exp(-lr / n_obs)
        nagelkerke = cox_snell / (1.0 - math.exp(-m2ll0 / n_obs))
        rs_step.append(str(st.step))
        rs_label1.append("R-Square")
        rs_cvalue1.append(sas_compat.fmt_wd(cox_snell, 6, 4))
        rs_nvalue1.append(sas_compat.sas_d12_3(cox_snell))
        rs_label2.append("Max-rescaled R-Square")
        rs_cvalue2.append(sas_compat.fmt_wd(nagelkerke, 6, 4))
        rs_nvalue2.append(sas_compat.sas_d12_3(nagelkerke))
    printed_fit_statistics = pl.DataFrame(
        {
            "Step": fs_step,
            "RowId": fs_rowid,
            "Criterion": fs_criterion,
            "Equals": fs_equals,
            "InterceptOnly": fs_only,
            "InterceptAndCovariates": fs_cov,
        }
    )
    sas_compat.write_sas_csv(printed_fit_statistics, output_dir / "printed_fit_statistics.csv", formats={})
    printed_global_tests = pl.DataFrame(
        {"Step": gt_step, "Test": gt_test, "ChiSq": gt_chisq, "DF": gt_df, "ProbChiSq": gt_prob}
    )
    # SAS makes no Global Tests and no R-Square table when no variable ever entered (small-inputs.md (d))
    if stepwise.steps:
        sas_compat.write_sas_csv(printed_global_tests, output_dir / "printed_global_tests.csv", formats={})
    printed_rsquare = pl.DataFrame(
        {
            "Step": rs_step,
            "Label1": rs_label1,
            "cValue1": rs_cvalue1,
            "nValue1": rs_nvalue1,
            "Label2": rs_label2,
            "cValue2": rs_cvalue2,
            "nValue2": rs_nvalue2,
        }
    )
    if stepwise.steps:
        sas_compat.write_sas_csv(printed_rsquare, output_dir / "printed_rsquare.csv", formats={})

