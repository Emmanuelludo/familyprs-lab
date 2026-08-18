# Course and prior-code alignment

This project treats the supplied **course material as the knowledge standard** and the supplied personal code as evidence of the prior implementation level, not as the course syllabus itself.

## Knowledge reused directly

### GWAS / PLINK lecture and implementation
The supplied material covers common/polygenic disease, GWAS, linkage disequilibrium, GWAS quality control, unexpected relatedness, population/family structure, population stratification and polygenic risk scores. The prior R/PLINK implementation includes MAF filtering, missingness, HWE filtering, LD pruning and KING-relatedness output.

**Project extension:** relatedness is no longer only a QC issue; it becomes a defining property of the prediction/validation design.

### High-dimensional modelling implementation
The prior code uses `glmnet`, cross-validation, XGBoost and SHAP-oriented tooling.

**Project extension:** both model classes are placed inside a family-grouped validation design with calibration and identical prediction targets.

### Risk-adapted screening lecture
The supplied breast-screening lecture presents genetic risk models, family history, BOADICEA/IBIS comparison, discrimination/calibration, CanRiskCE and the inclusion of a standardized PRS alongside other risk information.

**Project extension:** use the same *risk-communication logic*—family history + polygenic + non-genetic information + graphical output—but for a non-clinical synthetic IBD research demonstration.

### Cohort / meta-analysis material
The supplied material emphasizes well-characterized cohorts, genotyping, relatedness/population structure, phenotype definition, QC, replication and heterogeneity.

**Project extension:** separate population generation, family ascertainment, model development and external-family evaluation explicitly.

## Implementation style retained from personal work

- vectorized transforms and matrix-oriented thinking;
- reproducible scripts and deterministic seeds;
- modular pipeline structure;
- direct comparison of statistical and ML methods;
- interpretability/diagnostic thinking rather than accuracy-only reporting.

The project deliberately raises the level from “complete an exercise” to “defend an end-to-end methodological research design.”
