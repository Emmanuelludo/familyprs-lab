# Interview talking points

## 45-second project summary

> I built a family-aware IBD risk modelling project around a prospective question: among relatives who are unaffected at baseline in an IBD-enriched family cohort, how well can polygenic, clinical and family-history information predict disease over ten years? I used three public IBD PGS as correlated genetic summaries, generated pedigrees with Mendelian-style score inheritance and shared family frailty, and compared regularised prediction with mixed models, GEE, shared-frailty survival modelling and boosted-tree alternatives. All model selection and evaluation is grouped by family.

## Why multiple PGS?

> I did not treat the scores as independent discoveries because they use the same source GWAS. They differ in construction, so I asked whether a regularised combination adds incremental information. In the current development-family CV, the gain over LDpred2 plus the same covariates is modest, about one percentage point of AUROC.

## Why a mixed model?

> Explicit family-history variables capture measured information such as affected siblings or multiple affected first-degree relatives. A family random effect addresses residual dependence that remains after those variables are included. For a completely new family, its random effect is unknown, so prediction uses the population fixed-effect component. A genotype-level version would replace this coarse family intercept with a kinship-structured random effect based on a relationship matrix.

## Why GEE as well?

> GEE gives a population-average estimate while accounting for clustering. I would not present it as interchangeable with a mixed model; it answers a related but different inferential question and is useful as a robustness benchmark.

## Why a frailty survival model?

> The cohort is longitudinal, so time to IBD onset contains more information than a binary ten-year label. A shared frailty model allows members of a family to share residual hazard while retaining the actual event times and censoring structure.

## Validation design

> I lock away 20 percent of families before model development. Within the remaining development families, inner grouped folds select hyperparameters and outer grouped folds estimate internal performance for the principal model comparison. After the specification is fixed, I fit on all development families and evaluate once on the untouched families. This aligns the validation unit with the intended target: transport to a new family.

## Machine learning

> I compared XGBoost, LightGBM and CatBoost using the same observed predictor block. CatBoost was the strongest boosted learner internally, but it did not surpass the statistical models on the final family holdout. I therefore keep boosting as a nonlinear benchmark rather than assuming it should be the principal model.

## Current performance

The current locked family test contains 140 families and 67 incident events. AUROC is approximately 0.69 for Elastic Net, the random-intercept model and GEE; CatBoost is approximately 0.67. Nested repeated family CV is approximately 0.64 for both Elastic Net and CatBoost. The intervals are wide enough that minor ranking differences should not be overinterpreted.

## Sensitivity analysis

> I keep the fitted model fixed and perturb the test data. That asks how robust the deployed predictor would be to realistic measurement problems. In the current set, outcome misclassification has the clearest adverse effect; added PGS noise and antibiotic-exposure misclassification have smaller effects.

## What I would change with real cohort data

> The first upgrade would be genotype-level scoring and a pedigree- or genotype-derived kinship matrix. I would then separate Crohn's disease and ulcerative colitis where the data support it, incorporate longitudinal covariates, and evaluate external or temporal recalibration. Microbiome and other omic layers would be added only after the genetic-family benchmark is stable.
