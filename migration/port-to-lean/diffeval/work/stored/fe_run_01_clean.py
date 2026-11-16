    def input_best32(v: str) -> pl.Expr:
        if credit_raw.schema[v] != pl.String:
            return sas_compat.input_best32(
                pl.col(v).map_elements(sas_compat.sas_best12, return_dtype=pl.String)
            )
        return sas_compat.input_best32(pl.col(v))

    credit_raw_clean = (
        credit_raw.with_columns(
            MonthlyIncome_num=input_best32("MonthlyIncome"),
            NumberOfDependents_num=input_best32("NumberOfDependents"),
        )
        .drop("MonthlyIncome", "NumberOfDependents")
        .rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"})
    )
