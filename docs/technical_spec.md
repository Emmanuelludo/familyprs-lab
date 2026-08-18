# Technical specification: FamilyPRS Lab v6

## 1. Estimand

The primary estimand is the calibrated probability of incident IBD within 10 years among relatives who are unaffected at baseline in families ascertained through at least one baseline IBD case.

A secondary estimand is event-time ranking over the same follow-up period.

## 2. Public genetic inputs

Three IBD PGS Catalog scores are represented:

- `PGS004105`: P+T/clumping, 139 variants, GRCh38, beta weights.
- `PGS003997`: lassosum, 8,406 variants, GRCh38, beta weights.
- `PGS004038`: LDpred2.CV, 1,018,068 variants, GRCh38, beta weights.

They share the same source GWAS (`GCST004131`) and therefore cannot be interpreted as independent pieces of evidence. The project uses them as correlated measurements of an underlying polygenic component.

The download validator checks:

1. PGS Catalog file structure;
2. required `effect_allele` and `effect_weight` fields;
3. GRCh38 build consistency;
4. beta weight type;
5. score ID and declared method metadata.

## 3. Evidence-informed parameter layer

For each public PGS, available evaluation odds ratios per standard deviation are transformed to the log-OR scale and synthesised with a random-effects model. These summaries inform the association between the latent genetic liability and each observed PGS representation.

Selected published familial-IBD summary estimates inform distributions for:

- sex;
- recent antibiotic exposure;
- affected sibling;
- two or more affected first-degree relatives;
- three or more affected first-degree relatives.

Smoking, age, extreme BMI, the high-genetic/high-family-history interaction and the residual family component are weakly informed simulation parameters because the current evidence table does not contain a sufficiently compatible formal synthesis for those coefficients.

The simulation draws parameter values from these distributions rather than hard-coding one arbitrary coefficient vector.

## 4. Genetic family generation

Each founder receives a standardised latent additive genetic value `G`.

For each child:

```text
G_child = 0.5 * G_father + 0.5 * G_mother + e_G
```

with residual variance chosen to preserve approximately unit marginal variance.

Each public PGS is represented as a noisy heritable measurement of `G`:

```text
PGS_m = rho_m * G + sqrt(1 - rho_m^2) * H_m
```

where `H_m` is an independent heritable score component generated through the same pedigree and `rho_m` is derived from the relative strength of the published score evidence.

This creates realistic score correlation within relatives and between PGS methods without pretending that the present simulation contains exact haplotypes for 1,018,068 markers.

A genotype-level extension should replace this layer with reference-haplotype simulation, Mendelian transmission and direct vectorised scoring from the official PGS files.

## 5. Baseline disease and ascertainment

Clinical covariates are generated before disease status. Baseline IBD is then generated from genetic, clinical and shared-family components.

Only after the population has been generated are families selected if at least one member has baseline IBD.

Family-history predictors are derived from realised pedigree and disease status:

- number of affected genetic FDRs;
- affected parent;
- affected sibling;
- earliest FDR age at onset;
- indicators for two or more and three or more affected FDRs.

Spouses are not genetic FDRs.

## 6. Prospective event-time model

Only baseline-unaffected relatives enter the prospective analysis.

For individual `i` in family `f`:

```text
h_if(t) = Z_f * h0 * exp(X_if beta)
```

where:

- `Z_f` is a shared gamma frailty with mean one;
- `h0` is an exponential baseline hazard;
- `X beta` contains latent genetic liability, selected clinical covariates and family-history terms.

Event times are sampled from this hazard model and administratively censored at 10 years. The fixed-horizon binary outcome is `event_time <= 10 years`.

## 7. Predictors exposed to fitted models

The fitted models do not receive the latent genetic value or the simulated true frailty. They receive only observed-style variables:

- `pgs_pt_z`;
- `pgs_lassosum_z`;
- `pgs_ldpred2_z`;
- age;
- sex;
- smoking;
- BMI;
- recent antibiotic exposure;
- affected-FDR count;
- affected parent;
- affected sibling;
- earliest FDR onset age;
- multiplex-family indicators.

This separates the data-generating mechanism from the prediction model.

## 8. Prediction models

### Multi-PGS ridge stack

Strongly regularised logistic model using the three PGS summaries. It tests whether combining correlated PGS representations adds information without allowing unstable coefficients.

### Elastic Net

Penalised logistic model using genetic, clinical and family-history features. Penalty strength and L1/L2 mixture are selected only inside development-family CV.

### Random-intercept mixed model

```text
logit P(Y_if = 1) = X_if beta + u_f
u_f ~ Normal(0, sigma_family^2)
```

Family grouping enters the likelihood. For a completely unseen family, the random effect is not observed and prediction uses the fixed-effect population component.

### GEE

Logistic GEE with family as cluster and exchangeable working correlation. This provides a population-average family-clustered estimate complementary to the mixed model.

### Shared-frailty survival model

A parametric proportional-hazards model with gamma family frailty is fitted to the simulated event/censoring times. It produces 10-year risk and a survival C-index.

### AutoML benchmarks

- XGBoost
- LightGBM
- CatBoost

All receive the same observed predictor block. Their role is to test whether non-linear interactions materially improve transport to unseen families.

## 9. Validation design

Before any tuning, 20% of family IDs are locked as the final test set. The remaining 80% form the development set.

Within development:

1. hyperparameters are compared with grouped family CV;
2. out-of-fold predictions are retained;
3. logistic probability recalibration is estimated from development out-of-fold predictions;
4. the selected model is refitted on all development families;
5. the locked test families are evaluated once.

A nested repeated grouped-CV analysis is used for Elastic Net and the selected ML learner: inner family folds select hyperparameters and outer family folds estimate development performance. It is not substituted for the final test result.

Random individual splitting is not used in the reported analysis.

## 10. Performance outputs

- AUROC;
- AUPRC;
- Brier score;
- log loss;
- calibration intercept and slope;
- calibration curves;
- family-bootstrap AUROC intervals;
- survival C-index for the frailty model.

## 11. Multi-PGS analysis

The principal incremental check holds the non-genetic specification fixed and compares:

```text
LDpred2 PGS + covariates
versus
P+T + lassosum + LDpred2 PGS + the same covariates
```

In the current run, the mean five-fold family-CV AUROC changes from approximately 0.630 to 0.640. The modest increment is consistent with strong overlap in discovery evidence between the scores.

## 12. Sensitivity analyses

The current locked-model sensitivity set includes:

- PGS measurement noise;
- 20% family-history missingness;
- 15% antibiotic-exposure misclassification;
- 5% outcome misclassification.

Future simulation grids should add:

- ancestry transportability;
- missing relatives;
- family size;
- lower/higher familial frailty;
- genotype measurement error;
- varying recruitment rules;
- loss to follow-up;
- phenotype-specific CD versus UC risks;
- microbiome/proteomic measurement error.

## 13. Genotype-level kinship extension

The current random-intercept model represents shared family clustering, not marker-derived genetic covariance. A true statistical-genetics extension should fit:

```text
u ~ MVN(0, sigma_g^2 K)
```

where `K` is a pedigree- or genotype-derived kinship/GRM matrix.

The repository keeps an R scaffold for this stage, but the current results do not claim that a GRM model has been fitted without genotype-level marker data.
