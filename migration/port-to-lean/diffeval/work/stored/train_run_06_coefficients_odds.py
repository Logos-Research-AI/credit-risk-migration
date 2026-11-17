    mc_variable: list[str] = ["Intercept"]
    mc_estimate: list[str] = [sas_compat.sas_d8(intercept)]
    mc_stderr: list[str] = []
    mc_wald: list[str] = []
    mc_prob: list[str] = []
    # odds ratios: final model only, no Intercept  # INV printed_odds_ratios.csv, R§2 Z975
    or_effect: list[str] = []
    or_est: list[str] = []
    or_lower: list[str] = []
    or_upper: list[str] = []
    for idx, name in [(0, "Intercept"), *zip(final_index, final_effects, strict=True)]:
        b = float(final.beta[idx])
        se = math.sqrt(float(final.cov[idx, idx]))
        wald_b = (b / se) ** 2
        if idx != 0:
            mc_variable.append(name[:20])
            mc_estimate.append(sas_compat.sas_d8(b))
            or_effect.append(name[:20])
            # R§2 ODS stored widths (S7)
            or_est.append(sas_compat.fmt_oddsr(math.exp(b), 8, 3))
            or_lower.append(sas_compat.fmt_oddsr(math.exp(b - sas_compat.Z975 * se), 8, 3))
            or_upper.append(sas_compat.fmt_oddsr(math.exp(b + sas_compat.Z975 * se), 8, 3))
        mc_stderr.append(sas_compat.sas_d8(se))
        mc_wald.append(sas_compat.fmt_wd(wald_b, 10, 4))
        mc_prob.append(sas_compat.sas_pvalue(sas_compat.chi2_sf(wald_b, 1)))
    model_coefficients = pl.DataFrame(
        {
            "Variable": mc_variable,
            "DF": ["1"] * len(mc_variable),
            "Estimate": mc_estimate,
            "StdErr": mc_stderr,
            "WaldChiSq": mc_wald,
            "ProbChiSq": mc_prob,
            "_ESTTYPE_": ["MLE"] * len(mc_variable),
        }
    )
    printed_odds_ratios = pl.DataFrame(
        {"Effect": or_effect, "OddsRatioEst": or_est, "LowerCL": or_lower, "UpperCL": or_upper}
    )
    # stored formats: Effect $20., OddsRatioEst/LowerCL/UpperCL oddsr8.3 (S7)
    if final_effects:
        sas_compat.write_sas_csv(printed_odds_ratios, output_dir / "printed_odds_ratios.csv", formats={})
