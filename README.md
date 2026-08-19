# FamilyPRS Lab

FamilyPRS Lab is a family-aware statistical-genetics demonstrator for prospective inflammatory bowel disease (IBD) risk modelling. The project combines multiple correlated IBD polygenic scores, pedigree-derived family history, clinical covariates, family-aware statistical models, machine-learning comparators, calibration, grouped validation and sensitivity analysis.

**Live application:** https://emmanuelludo.github.io/familyprs-lab/

## Repository structure

```text
.
├── .github/workflows/       validation and GitHub Pages deployment
├── analysis/R/              R statistical-genetics extensions
├── assets/                  browser application and deployed model payload
├── data/public/             public PGS/evidence provenance metadata
├── docs/                    technical and reproducibility documentation
├── scripts/                 Python simulation/modelling pipeline
├── tests/                   source and browser-interaction tests
├── index.html               deployed application entry point
├── requirements.txt         Python research dependencies
└── run_demo.sh              local static-site runner
```

Generated outputs such as `results/`, fitted model objects and synthetic datasets are not hand-maintained source. They are recreated by the analysis pipeline. The static site committed under `index.html` + `assets/` is the deployment artifact used by GitHub Pages.

## Reproducible analysis source

The main entry point is:

```bash
python scripts/build_demo.py
```

The implementation is split into modules:

- `familyprs_config.py` — predictors, public PGS metadata and evidence table;
- `familyprs_evidence.py` — random-effects evidence synthesis and DGM parameter draws;
- `familyprs_simulation.py` — pedigrees, Mendelian-style inheritance, ascertainment and 10-year event generation;
- `familyprs_metrics.py` — calibration and family-bootstrap metrics;
- `familyprs_candidates.py` — grouped model tuning and nested repeated family CV;
- `familyprs_dependence.py` — mixed model, GEE and shared-gamma-frailty models;
- `familyprs_fit.py` — development-OOF recalibration and final refit;
- `familyprs_exports.py` — browser model export, sensitivity analysis and demo families;
- `familyprs_pipeline.py` — end-to-end orchestration.

The public-PGS download/schema check is separate:

```bash
python scripts/download_public_pgs.py
```

It downloads the official PGS Catalog scoring files and checks required scoring columns, genome build and weight type before genotype-level use.

## Scientific design

The demonstrator predicts **10-year incident IBD among initially unaffected members of ascertained IBD families**. Family membership is kept intact during development and final evaluation.

The genetic block uses three IBD PGS as correlated predictors:

- PGS004105: P+T / clumping
- PGS003997: lassosum
- PGS004038: LDpred2.CV

The modelling comparison includes penalized logistic regression, a family random-intercept model, family-clustered GEE, a shared-frailty survival model and boosted-tree learners.

A planned genotype-level extension replaces the coarse family random intercept with a pedigree- or genotype-derived relationship matrix `K` and a kinship-aware GLMM:

```text
u ~ MVN(0, sigma_g^2 K)
```

The R scaffold for that step is `analysis/R/04_kinship_glmm.R`. It is deliberately not presented as a fitted GRM model without marker-level genotypes or a valid relationship matrix.

## Validation

The final test families are locked before model development. Hyperparameter selection and internal performance estimation use family-grouped resampling. Probability calibration is learned from development out-of-fold predictions. The final fitted specification is then evaluated once on completely unseen families.

Random individual splitting is deliberately not part of the scientific validation analysis.

## Website

For a local copy of the deployed site:

```bash
./run_demo.sh
# open http://localhost:8000
```

The family editor supports example and custom nuclear families, live pedigree editing, three PGS inputs, clinical covariates and model switching. Validation ROC/calibration curves use explicit model labels, distinct colours, hover isolation and click/tap pinning.

## Automatic deployment

`.github/workflows/pages.yml` runs on every push to `main`. It checks the browser JavaScript, compiles the Python source, runs an interaction smoke test in Chromium, stages only `index.html` + `assets/`, and deploys that artifact with GitHub Pages.

## Data note

Participant-level records in the demonstrator are synthetic. Public PGS metadata and published summary estimates are used where documented. No real patient-level clinical or genotype data are included in this repository.
