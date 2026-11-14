# Model Card: Credit Default Risk Prediction

## Model Details

**Model Name:** Credit Risk Scoring - Logistic Regression
**Version:** 1.0
**Date:** 2025
**Model Type:** Binary Classification (Logistic Regression with Stepwise Selection)
**Framework:** SAS (PROC LOGISTIC)

### Model Description

This model predicts the probability of serious delinquency (90+ days past due or worse) within the next 2 years for credit applicants. It uses logistic regression with stepwise variable selection to identify the most predictive features from financial and demographic data.

## Training Data

**Source:** Kaggle "Give Me Some Credit" Competition
**Dataset:** cs-training.csv
**Records:** 150,000 credit applicants
**Split:** 70% training (105,000) / 30% validation (45,000)
**Time Period:** Historical credit data

### Features

The model uses the following feature categories:

#### Original Features
- `age`: Age of borrower
- `MonthlyIncome`: Monthly income
- `NumberOfDependents`: Number of dependents
- `RevolvingUtilizationOfUnsecuredLines`: Credit utilization ratio
- `DebtRatio`: Monthly debt payments / monthly income
- `NumberOfTime30-59DaysPastDueNotWorse`: Late payments (30-59 days)
- `NumberOfTime60-89DaysPastDueNotWorse`: Late payments (60-89 days)
- `NumberOfTimes90DaysLate`: Serious delinquencies (90+ days)
- `NumberOfOpenCreditLinesAndLoans`: Number of open credit lines
- `NumberRealEstateLoansOrLines`: Number of real estate loans

#### Engineered Features
- Total late payments across all categories
- Delinquency indicators (any delinquency, serious delinquency)
- Credit utilization and debt ratio categories
- Income per dependent
- Credit lines per household member
- Age categories for risk segmentation
- Risk flags (high utilization, high debt ratio, low income, etc.)
- Financial health score (0-100)
- Log transformations of skewed variables
- Interaction features (age × income, utilization × debt ratio)
- Missing value indicators

### Target Variable
**SeriousDlqin2yrs:** Binary indicator (1 = default, 0 = no default)
**Definition:** Person experienced 90+ days past due delinquency or worse in the next 2 years

### Data Preprocessing
- Missing value imputation:
  - MonthlyIncome: Median by age group
  - NumberOfDependents: Imputed with 0 (most common value)
- Outlier capping for extreme values in utilization and debt ratio
- Feature scaling and normalization where appropriate

## Model Performance

### Training Set Metrics

#### Discrimination Metrics
- **AUC-ROC:** 0.8592
- **Gini Coefficient:** 0.7184
- **Somers' D:** 0.7184

#### Classification Metrics (at 0.5 threshold)
- **Accuracy:** 0.9369
- **Precision:** 0.5781
- **Recall:** 0.2023
- **F1-Score:** 0.2998

### Validation Set Metrics

#### Discrimination Metrics
- **AUC-ROC:** 0.8564
- **Gini Coefficient:** 0.7128
- **Somers' D:** 0.7128

#### Classification Metrics (at 0.5 threshold)
- **Accuracy:** 0.9362
- **Precision:** 0.5690
- **Recall:** 0.2008
- **F1-Score:** 0.2968

#### Confusion Matrix (Validation Set)

|                    | Predicted: No Default | Predicted: Default |
|--------------------|----------------------|-------------------|
| **Actual: No Default** | 41,523 (TN)         | 459 (FP)          |
| **Actual: Default**    | 2,412 (FN)          | 606 (TP)          |

**Total Validation Records:** 45,000

#### Model Stability
- **Population Stability Index (PSI):** 0.0013 (No significant change - excellent stability)
- **PSI Interpretation:** No significant population shift between training and validation

### Performance Summary
- The model demonstrates excellent discrimination ability with AUC > 0.85 on both training and validation sets
- Very low overfitting: Training AUC (0.8592) and Validation AUC (0.8564) are nearly identical
- The dataset is highly imbalanced (default rate ~6.7%)
- At 0.5 threshold: High accuracy (93.6%) and precision (56.9%), but low recall (20.1%)
- The low recall indicates the model is conservative, predicting default only when very confident
- Model shows excellent stability (PSI = 0.0013)

## Risk Scoring System

The model outputs are transformed into an interpretable credit risk score system:

### Credit Risk Score (300-850)
Probability of default is converted to a FICO-like score scale:
- Score = 600 + 250 × (1 - predicted_probability)

### Risk Grades

| Grade | Score Range | Expected Default Probability | Interest Rate | Recommendation |
|-------|-------------|----------------------------|---------------|----------------|
| A     | 750+        | < 10%                      | 5.0%          | Approve        |
| B     | 700-749     | 10-15%                     | 7.0%          | Approve        |
| C     | 650-699     | 15-25%                     | 9.0%          | Review         |
| D     | 600-649     | 25-35%                     | 12.0%         | Decline        |
| E     | 550-599     | 35-50%                     | 15.0%         | Decline        |
| F     | < 550       | > 50%                      | 20.0%         | Decline        |

## Caveats and Recommendations

### Known Limitations
1. **Imbalanced Classes:** Default rate is low (~6-7%), requiring careful threshold selection
2. **Missing Data:** ~20% of records have missing income, using imputation strategy
3. **Outliers:** Extreme values in utilization ratio and debt ratio are capped
4. **Temporal Validation:** Model should be tested on out-of-time samples
5. **External Validity:** Performance on populations outside training distribution unknown

## Model Files and Outputs

### Scripts
1. `feature_engineering.sas` - Data loading and feature engineering
2. `train.sas` - Model training and scoring
3. `metrics_calculation.sas` - Comprehensive validation metrics
4. `predict.sas` - Scoring new applications

### Output Files
- `model_features_train.csv` - Training features
- `model_features_validation.csv` - Validation features
- `risk_scores_train.csv` - Scored training set with risk grades
- `risk_scores_validation.csv` - Scored validation set with risk grades
- `validation_summary.csv` - Overall validation metrics (AUC, KS, PSI)
- `decile_analysis.csv` - Lift analysis by decile
- `threshold_analysis.csv` - Performance at different thresholds
- `model_performance_metrics.csv` - Comprehensive metrics
- `test_predictions.csv` - Predictions on test set
- `kaggle_submission.csv` - Kaggle competition submission format

## Contact Information

**Model Developers:** Risk Analytics Team
**Organization:** [Your Organization]
**Last Updated:** 2025

## References

- Kaggle "Give Me Some Credit" Competition: https://www.kaggle.com/c/GiveMeSomeCredit
- Dataset Source: https://github.com/turintech/evoml-client-examples/tree/main/trials/credit-default-risk

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0     | 2025 | Initial model using Kaggle dataset, logistic regression with stepwise selection |

---

**Note:** Model card updated with actual performance metrics from production model run (06OCT2025).
