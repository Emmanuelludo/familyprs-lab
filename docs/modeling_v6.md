# Modelling notes: FamilyPRS Lab v6

## Why the target is 10-year incident IBD

The demonstration uses a 10-year horizon. This suits a long-running family cohort and makes time-to-event modelling a natural companion to fixed-horizon classification. Baseline disease status remains family-history information; only relatives without IBD at baseline enter the incident-risk model.

## Multiple PGS

The project represents three IBD PGS from the same published benchmark but constructed with markedly different methods: P+T, lassosum and LDpred2. They are deliberately not described as independent genetic instruments because their discovery evidence overlaps.

The working interpretation is that each score is a noisy, correlated measurement of a common polygenic burden. Regularisation decides whether a score contributes incremental predictive information.

The current development-family CV comparison shows only a modest gain from all three PGS over LDpred2 plus the same covariates. That is a useful result: combining scores is possible, but overlap in source evidence limits the amount of genuinely new information.

## Data-generating model

The generator has two hierarchical components.

### Evidence hierarchy

Compatible external summary estimates define distributions for selected genetic, clinical and family-history coefficients. The simulation draws a plausible parameter set for each generated dataset rather than treating one arbitrary coefficient vector as truth.

### Family hierarchy

Founders receive latent additive genetic values. Offspring inherit half of each parental value plus residual segregation variance. The PGS features are correlated measurements of the latent genetic component. A shared gamma frailty introduces residual family risk that is not directly observed by the prediction models.

The prospective event process is:

```text
h_if(t) = Z_f h0 exp(X_if beta)
```

and event times are censored at 10 years.

This distinction matters because the fitted models see only the observed-style PGS, clinical covariates and derived family history, not the latent genetic value or the true family frailty.

## Development and final testing

The analysis starts by locking away 20% of families. These families are not used for feature selection, tuning or probability recalibration.

The remaining 80% of families are the development set. Grouped CV within development is used for hyperparameter selection. Out-of-fold development predictions supply the recalibration layer. The selected model is refitted on all development families, then evaluated once on the untouched test families.

Repeated grouped CV for Elastic Net and the leading ML method is reported as an internal stability measure. The repeated-CV mean should be described as development performance, while the final test remains the external-like estimate within the simulation.

## Current modelling picture

The current run does not support a simple claim that boosting is superior. CatBoost is the leading boosted learner in development CV, but the family-aware statistical models remain competitive or slightly stronger on the final unseen families.

That result is scientifically useful because the problem contains relatively structured predictors and a modest number of events. The analysis therefore favours transparency over algorithmic novelty.

## Family-aware models

### Random-intercept GLMM

The family-specific random intercept handles residual within-family dependence during estimation. For a new family there is no estimated family random effect, so new-family prediction uses the fixed-effect component.

### GEE

GEE estimates the population-average association while accounting for clustered observations. It is a useful complement to the subject/family-specific mixed model.

### Shared gamma frailty

The survival model treats residual familial propensity as a multiplicative hazard term and makes direct use of event times. Its C-index should not be compared numerically with a fixed-horizon AUROC as though they were the same quantity.

## Sensitivity analysis

Sensitivity scenarios are run with the fitted models locked. This avoids re-tuning a model separately under every perturbation and asks a clearer deployment-style question: how brittle is the fitted predictor if measurement quality deteriorates?

Outcome misclassification currently causes the largest performance drop. PGS noise and antibiotic misclassification produce smaller losses, while the selected family-history missingness perturbation has little effect in this particular run.

## Interpretation of AUC

The purpose is not to tune the synthetic generator until AUROC becomes visually impressive. IBD PGS discrimination is itself moderate in external evaluations, and a family-enriched target population restricts the risk range. The useful questions are therefore:

- how stable is discrimination across families;
- whether calibration is adequate;
- whether family structure adds information beyond PGS;
- whether multiple PGS add more than one strong score;
- whether a nonlinear learner improves transport;
- how performance changes under plausible data problems.
