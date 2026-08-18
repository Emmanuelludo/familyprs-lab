# FamilyPRS Lab

FamilyPRS Lab is a family-aware statistical-genetics demonstrator for prospective inflammatory bowel disease (IBD) risk modelling. The project combines multiple correlated IBD polygenic scores, pedigree-derived family history, clinical covariates, family-aware statistical models, machine-learning comparators, calibration, grouped validation and sensitivity analysis.

**Live application:** https://emmanuelludo.github.io/familyprs-lab/

## Repository structure

```text
.
├── .github/workflows/       automatic GitHub Pages deployment
├── analysis/R/              R/statistical-genetics analysis examples
├── assets/                  deployed browser data, styles and model evaluators
├── data/                    data provenance and schema documentation
├── docs/                    methods and validation documentation
├── models/                  model-artifact documentation
├── presentation/            interview-presentation notes/source documentation
├── results/                 model-result documentation
├── scripts/                 simulation, training and public-PGS utilities
├── tests/                   repository/model integrity tests
└── index.html               application entry point
```

## Scientific design

The current demonstrator predicts **10-year incident IBD among initially unaffected members of ascertained IBD families**. Family membership is kept intact during development and final evaluation.

The genetic block uses three IBD PGS as correlated predictors:

- PGS004105: P+T / clumping
- PGS003997: lassosum
- PGS004038: LDpred2.CV

The modelling comparison includes penalized logistic regression, a family random-intercept model, family-clustered GEE and boosted-tree learners. A shared-frailty survival model is used as a prospective time-to-event benchmark.

A planned genotype-level extension replaces score-level familial genetic liability with variant/haplotype transmission, constructs a pedigree- or genotype-derived relationship matrix `K`, and fits a kinship-aware GLMM with

`u ~ MVN(0, sigma_g^2 K)`.

## Validation

The final test families are locked before model development. Hyperparameter selection and internal performance estimation use family-grouped resampling. Probability calibration is learned from development out-of-fold predictions. The final fitted specification is then evaluated once on completely unseen families.

Random individual splitting is deliberately not part of the scientific validation analysis.

## Automatic deployment

`.github/workflows/pages.yml` deploys the application after every relevant push to `main`. The workflow stages only `index.html` and `assets/`, so research code and analysis files remain in the public repository without being copied into the Pages artifact.

## Data note

Participant-level records in the demonstrator are synthetic. Public PGS metadata and published summary estimates are used where documented. No UKSH patient-level data are included in this repository.
