# Reproducibility and repository boundaries

## Source versus generated output

The repository keeps the research and presentation **source code** under `scripts/`, `analysis/R/`, `presentation/` and `tests/`. Public score/evidence metadata are under `data/public/`.

The following are generated and are intentionally not required for understanding the implementation:

- `data/synthetic/`: simulated participant-level tables;
- `models/`: fitted/exported model artifacts;
- `results/`: model metrics and plots;
- PowerPoint/PDF binaries.

Running `python scripts/build_demo.py` recreates the synthetic cohort, fitted model artifacts and model-result JSON. The deployed web application is separately committed as the tested static artifact under root `index.html` and `assets/`.

## Website deployment

`.github/workflows/pages.yml` is the only deployment workflow. On each push to `main` it:

1. validates required browser assets and JavaScript syntax;
2. syntax-compiles the Python source and checks key statistical-genetics files;
3. stages only `index.html` and `assets/` into the Pages artifact;
4. deploys through GitHub Pages.

This keeps research code public and reviewable without exposing it through the application URL.

## Data safety

No UKSH participant-level data are present. Demonstration pedigrees, clinical variables and outcomes are synthetic. The PGS files referenced by `scripts/download_public_pgs.py` are public PGS Catalog resources and are downloaded only when a genotype-level scoring analysis is explicitly run.
