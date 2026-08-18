# FamilyPRS Lab

FamilyPRS Lab is a family-aware statistical-genetics demonstrator for prospective inflammatory bowel disease (IBD) risk modelling. The project combines multiple correlated IBD polygenic scores, pedigree-derived family history, clinical covariates, family-aware statistical models, machine-learning comparators, calibration, grouped validation and sensitivity analysis.

**Live application:** https://emmanuelludo.github.io/familyprs-lab/

## Repository structure

```text
.
├── .github/workflows/
│   └── pages.yml             validate source/site and deploy GitHub Pages
├── analysis/R/               R statistical-genetics extensions
├── assets/                   tested browser application + deployed model payload
├── data/public/              PGS/evidence provenance metadata
├── docs/                     modelling, validation and interview documentation
├── presentation/             reproducible PowerPoint source modules
├── scripts/                  complete Python simulation/modelling pipeline
├── tests/                    source and family-structure integrity tests
├── index.html                deployed application entry point
├── requirements.txt          Python research dependencies
└── run_demo.sh               local static-site runner
```

`results/`, `models/`, `data/synthetic/` and the final presentation binaries are **generated outputs**, not hand-maintained source. The Python pipeline recreates those directories when it is run. The static site committed under `index.html` + `assets/` is the tested deployment artifact used by GitHub Pages.

## Reproducible analysis source

The main entry point is:

```bash
python scripts/build_demo.py
```

The implementation is split into readable modules instead of one large script:

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

`.github/workflows/pages.yml` runs on every push to `main`. It syntax-checks the browser JavaScript, compiles the Python source, checks key statistical-genetics files, stages only `index.html` + `assets/`, and deploys that artifact with GitHub Pages.

For this workflow to be the deployment authority, the repository's **Settings → Pages → Build and deployment → Source** must be set to **GitHub Actions**.

## Data note

Participant-level records in the demonstrator are synthetic. Public PGS metadata and published summary estimates are used where documented. No UKSH patient-level data are included in this repository.
