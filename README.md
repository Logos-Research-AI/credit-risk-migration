# Credit Default Risk Prediction Model

A production-ready SAS credit risk scoring system using real-world data from the Kaggle "Give Me Some Credit" competition. This model predicts the probability of serious delinquency (90+ days past due) within the next 2 years.

## Overview

This repository contains a complete SAS-based credit risk modeling pipeline that:
- Loads and preprocesses real credit data from Kaggle
- Engineers predictive features from financial and demographic data
- Trains a logistic regression model with stepwise variable selection
- Validates model performance with comprehensive metrics
- Scores new applications with risk grades and recommendations
- Provides a baseline for SAS-to-Python migration efforts

## Data Source

**Kaggle Competition:** [Give Me Some Credit](https://www.kaggle.com/c/GiveMeSomeCredit)
**Dataset Location:** `data/cs-training.csv` (150,000 records), `data/cs-test.csv` (101,503 records)
**Target Variable:** `SeriousDlqin2yrs` - Binary indicator of serious delinquency in next 2 years

### Dataset Features

| Feature | Description |
|---------|-------------|
| RevolvingUtilizationOfUnsecuredLines | Credit utilization ratio |
| age | Age of borrower |
| NumberOfTime30-59DaysPastDueNotWorse | Number of 30-59 day late payments |
| DebtRatio | Monthly debt payments / monthly income |
| MonthlyIncome | Monthly income |
| NumberOfOpenCreditLinesAndLoans | Number of open credit lines |
| NumberOfTimes90DaysLate | Number of serious delinquencies (90+ days) |
| NumberRealEstateLoansOrLines | Number of real estate loans |
| NumberOfTime60-89DaysPastDueNotWorse | Number of 60-89 day late payments |
| NumberOfDependents | Number of dependents |

## Project Structure

```
├── data/
│   ├── cs-training.csv              # Kaggle training data (150K records)
│   └── cs-test.csv                  # Kaggle test data (101K records)
├── feature_engineering.sas          # Data loading, cleaning, and feature engineering
├── train.sas                        # Model training and validation scoring
├── metrics_calculation.sas          # Comprehensive model validation
├── predict.sas                      # Score test set predictions
├── MODEL_CARD.md                    # Detailed model documentation
└── README.md                        # This file
```

## Prerequisites

- **SAS 9.4 or later**
- **Write access to:** `/home/u64352077/output/`
- **Data files:** cs-training.csv and cs-test.csv in `data/` directory

## Quick Start

### Complete Pipeline Execution

Run the scripts in order:

```sas
/* Step 1: Feature Engineering */
%include "feature_engineering.sas";

/* Step 2: Train Model */
%include "train.sas";

/* Step 3: Calculate Validation Metrics */
%include "metrics_calculation.sas";

/* Step 4: Score Test Set (optional) */
%include "predict.sas";
```

## Detailed Script Descriptions

### 1. feature_engineering.sas

**Purpose:** Loads raw Kaggle data, handles missing values, and creates predictive features

**Key Operations:**
- Imports cs-training.csv from `data/` directory
- Handles missing values:
  - MonthlyIncome: Imputed with median by age group
  - NumberOfDependents: Imputed with 0
- Creates 40+ engineered features:
  - Late payment aggregations
  - Delinquency indicators
  - Risk flags (high utilization, high debt, etc.)
  - Financial health score
  - Log transformations
  - Interaction features
- Splits data: 70% training / 30% validation
- Exports to output directory

**Inputs:**
- `data/cs-training.csv`

**Outputs:**
- `output/model_features_train.csv` (105,000 records)
- `output/model_features_validation.csv` (45,000 records)


### 2. train.sas

**Purpose:** Trains logistic regression model and generates risk scores

**Key Operations:**
- Trains logistic regression with stepwise selection (p-value thresholds: 0.05)
- Scores both training and validation sets
- Generates confusion matrices
- Creates risk scores (300-850 scale, FICO-like)
- Assigns risk grades (A-F)
- Provides lending recommendations (Approve/Review/Decline)
- Calculates risk-based interest rates
- Computes ROC curves and AUC

**Inputs:**
- `output/model_features_train.csv`
- `output/model_features_validation.csv`

**Outputs:**
- `output/risk_scores_train.csv` - Scored training set with risk grades
- `output/risk_scores_validation.csv` - Scored validation set
- `output/final_model_output.csv` - Final predictions summary
- `output/model_summary.csv` - AUC and model metadata


### 3. metrics_calculation.sas

**Purpose:** Comprehensive model validation and performance analysis

**Key Metrics:**
- **ROC Curve and AUC:** Discrimination ability
- **Gini Coefficient:** Model power (2 × AUC - 1)
- **KS Statistic:** Maximum separation between good/bad distributions
- **Confusion Matrix:** At multiple thresholds (0.3, 0.4, 0.5, 0.6, 0.7)
- **Accuracy, Precision, Recall, F1-Score, Specificity**
- **Decile Analysis:** Lift and capture rates by risk decile
- **Population Stability Index (PSI):** Distribution stability (train vs validation)
- **Calibration Plot:** Predicted vs actual default rates

**Inputs:**
- `output/risk_scores_train.csv`
- `output/risk_scores_validation.csv`

**Outputs:**
- `output/validation_summary.csv` - Overall model performance
- `output/decile_analysis.csv` - Lift by decile
- `output/threshold_analysis.csv` - Metrics at different thresholds
- `output/ks_statistic.csv` - KS statistic
- `output/calibration_plot.csv` - Calibration data
- `output/model_performance_metrics.csv` - Comprehensive metrics


### 4. predict.sas

**Purpose:** Score Kaggle test set for competition submission

**Key Operations:**
- Loads cs-test.csv
- Applies same feature engineering as training
- Handles missing values consistently
- Scores using trained model
- Generates risk scores and grades
- Creates Kaggle submission file

**Inputs:**
- `data/cs-test.csv`
- `work.logit_model` (from train.sas)

**Outputs:**
- `output/kaggle_submission.csv` - Competition submission format (row_id, probability)
- `output/test_predictions.csv` - Full predictions with risk grades


## Risk Grading System

The model converts default probabilities to credit risk scores and grades:

| Risk Grade | Score Range | Default Probability | Interest Rate | Recommendation |
|-----------|-------------|---------------------|---------------|----------------|
| A | 750+ | < 10% | 5.0% | Approve |
| B | 700-749 | 10-15% | 7.0% | Approve |
| C | 650-699 | 15-25% | 9.0% | Review |
| D | 600-649 | 25-35% | 12.0% | Decline |
| E | 550-599 | 35-50% | 15.0% | Decline |
| F | < 550 | > 50% | 20.0% | Decline |

**Score Formula:** `600 + 250 × (1 - predicted_probability)`

## Key Features Used in Model

### Core Financial Metrics
- Credit utilization (capped at 200%)
- Debt-to-income ratio (capped at 500%)
- Monthly income (log-transformed)
- Age

### Late Payment Indicators
- 30-59 day late payments
- 60-89 day late payments
- 90+ day serious delinquencies
- Total late payments
- Delinquency flags

### Risk Flags
- High credit utilization (> 75%)
- Very high utilization (> 100%)
- High debt ratio (> 43%)
- Serious delinquency (90+ days late)
- Multiple delinquencies (≥ 3)
- Low income (< $2,500/month)
- Many dependents (≥ 3)
- Few credit lines (≤ 2)

### Composite Scores
- Financial health score (0-100)
- Total risk flags count

### Interaction Features
- Age × log(income)
- Credit utilization × debt ratio

## Output Files Reference

### Feature Engineering Outputs
- `model_features_train.csv` - Training features with all engineered variables
- `model_features_validation.csv` - Validation features

### Model Training Outputs
- `risk_scores_train.csv` - Training set with predictions, scores, grades
- `risk_scores_validation.csv` - Validation set with predictions, scores, grades
- `final_model_output.csv` - Summary of key predictions
- `model_summary.csv` - Model metadata and AUC

### Validation Metrics Outputs
- `validation_summary.csv` - AUC, Gini, KS, PSI, model status
- `decile_analysis.csv` - Performance by risk decile
- `threshold_analysis.csv` - Metrics at 0.3, 0.4, 0.5, 0.6, 0.7 thresholds
- `ks_statistic.csv` - KS statistic and cutoff
- `calibration_plot.csv` - Predicted vs actual by bin
- `model_performance_metrics.csv` - Comprehensive metrics file

### Test Set Outputs
- `kaggle_submission.csv` - Kaggle format (row_id, probability)
- `test_predictions.csv` - Full predictions with risk grades

## Configuration

All scripts use these path variables (update if needed):

```sas
%let data_path = /home/u64352077;
%let output_path = /home/u64352077/outputs;
```

## Troubleshooting

### Issue: Missing data directory
**Solution:** Create `data/` directory and place cs-training.csv and cs-test.csv files

### Issue: Output path doesn't exist
**Solution:** Update `%let output_path` in all scripts to a valid directory with write permissions

### Issue: Missing values not handled
**Solution:** The feature_engineering.sas script automatically imputes missing values using median (income) or 0 (dependents)

### Issue: Model stored in work library disappears
**Solution:** Run train.sas and predict.sas in the same SAS session, or use a permanent library for model storage

### Issue: Different results on re-run
**Solution:** Random seed is set (seed=42) for reproducibility. Same seed = same train/val split

## Model Card

See [MODEL_CARD.md](MODEL_CARD.md) for comprehensive model documentation including:
- Model architecture and training details
- Performance metrics and benchmarks
- Feature descriptions
- Risk scoring methodology


**Last Updated:** 2025
**Version:** 1.0
