from __future__ import annotations

import json
import math
import warnings
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, gammaln, logit
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Binomial

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260818
RNG = np.random.default_rng(SEED)
HORIZON = 10.0

PGS_FEATURES = ["pgs_pt_z", "pgs_lassosum_z", "pgs_ldpred2_z"]
CLINICAL_FEATURES = [
    "age",
    "sex_female",
    "current_smoker",
    "bmi",
    "antibiotics_12m",
    "n_affected_fdr",
    "affected_parent",
    "affected_sibling",
    "min_relative_onset_age",
    "multi_fdr_2plus",
    "multi_fdr_3plus",
]
FEATURES = PGS_FEATURES + CLINICAL_FEATURES

# All three scores target IBD, use beta weights, use GRCh38, and were benchmarked in the
# same Monti et al. framework using the same source GWAS (GCST004131). They differ in
# construction, which makes them useful as correlated genetic summaries for stacking.
PUBLIC_PGS = {
    "PGS004105": {
        "feature": "pgs_pt_z",
        "name": "pt_clump.auto.GCST004131.IBD",
        "method": "P+T / clumping",
        "genome_build": "GRCh38",
        "variant_count": 139,
        "effect_weight_type": "beta",
        "source_gwas": "GCST004131",
        "publication": "Monti R et al., American Journal of Human Genetics (2024)",
        "catalog_url": "https://www.pgscatalog.org/score/PGS004105/",
        "scoring_file": "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/PGS004105/ScoringFiles/PGS004105.txt.gz",
        "evaluations": [
            {"sample": "PSS011220", "ancestry": "European", "or": 1.24143, "lo": 1.1890805, "hi": 1.29609272, "auroc": 0.55940},
            {"sample": "PSS011231", "ancestry": "European", "or": 1.63002, "lo": 1.5935273, "hi": 1.66734777, "auroc": 0.63362},
            {"sample": "PSS011244", "ancestry": "South Asian", "or": 1.40101, "lo": 1.27954934, "hi": 1.53399308, "auroc": 0.59819},
            {"sample": "PSS011260", "ancestry": "European", "or": 1.35946, "lo": 1.29634357, "hi": 1.42565477, "auroc": 0.58383},
            {"sample": "PSS011288", "ancestry": "South Asian", "or": 1.34635, "lo": 1.1581509, "hi": 1.56512439, "auroc": 0.58604},
            {"sample": "PSS011273", "ancestry": "European", "or": 1.59062, "lo": 1.50586312, "hi": 1.68013891, "auroc": 0.63057},
        ],
    },
    "PGS003997": {
        "feature": "pgs_lassosum_z",
        "name": "lassosum.auto.GCST004131.IBD",
        "method": "lassosum",
        "genome_build": "GRCh38",
        "variant_count": 8406,
        "effect_weight_type": "beta",
        "source_gwas": "GCST004131",
        "publication": "Monti R et al., American Journal of Human Genetics (2024)",
        "catalog_url": "https://www.pgscatalog.org/score/PGS003997/",
        "scoring_file": "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/PGS003997/ScoringFiles/PGS003997.txt.gz",
        "evaluations": [
            {"sample": "PSS011220", "ancestry": "European", "or": 1.35075, "lo": 1.2938079, "hi": 1.41020626, "auroc": 0.57941},
            {"sample": "PSS011231", "ancestry": "European", "or": 1.94603, "lo": 1.90231852, "hi": 1.99073726, "auroc": 0.67873},
            {"sample": "PSS011244", "ancestry": "South Asian", "or": 1.83801, "lo": 1.67998664, "hi": 2.01090769, "auroc": 0.66965},
            {"sample": "PSS011260", "ancestry": "European", "or": 1.53922, "lo": 1.46791286, "hi": 1.61399308, "auroc": 0.61798},
            {"sample": "PSS011288", "ancestry": "South Asian", "or": 1.73594, "lo": 1.48902968, "hi": 2.02379137, "auroc": 0.64780},
            {"sample": "PSS011273", "ancestry": "European", "or": 1.84612, "lo": 1.74826591, "hi": 1.94945659, "auroc": 0.66875},
        ],
    },
    "PGS004038": {
        "feature": "pgs_ldpred2_z",
        "name": "ldpred2.CV.GCST004131.IBD",
        "method": "LDpred2",
        "genome_build": "GRCh38",
        "variant_count": 1018068,
        "effect_weight_type": "beta",
        "source_gwas": "GCST004131",
        "publication": "Monti R et al., American Journal of Human Genetics (2024)",
        "catalog_url": "https://www.pgscatalog.org/score/PGS004038/",
        "scoring_file": "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/PGS004038/ScoringFiles/PGS004038.txt.gz",
        "evaluations": [
            {"sample": "PSS011220", "ancestry": "European", "or": 1.36610, "lo": 1.30841773, "hi": 1.42633451, "auroc": 0.58410},
            {"sample": "PSS011231", "ancestry": "European", "or": 2.00709, "lo": 1.96176588, "hi": 2.05345818, "auroc": 0.68746},
            {"sample": "PSS011244", "ancestry": "South Asian", "or": 1.94600, "lo": 1.77718979, "hi": 2.13085165, "auroc": 0.68641},
            {"sample": "PSS011260", "ancestry": "European", "or": 1.55477, "lo": 1.48236145, "hi": 1.63071918, "auroc": 0.61939},
            {"sample": "PSS011288", "ancestry": "South Asian", "or": 1.71999, "lo": 1.47511022, "hi": 2.00551470, "auroc": 0.64250},
            {"sample": "PSS011273", "ancestry": "European", "or": 1.96885, "lo": 1.86342403, "hi": 2.08023967, "auroc": 0.68458},
        ],
    },
}

EVIDENCE = {
    "female": {"or": 1.40, "lo": 1.23, "hi": 1.59, "source": "family-history IBD study"},
    "antibiotics": {"or": 1.28, "lo": 1.02, "hi": 1.61, "source": "family-history IBD study"},
    "affected_sibling": {"or": 1.36, "lo": 1.18, "hi": 1.57, "source": "family-history IBD study"},
    "fdr_2plus": {"or": 2.47, "lo": 1.86, "hi": 3.28, "source": "family-history IBD study"},
    "fdr_3plus": {"or": 6.26, "lo": 1.34, "hi": 29.29, "source": "family-history IBD study"},
    "smoking": {"log_or_mean": math.log(1.10), "log_or_sd": 0.12, "source": "weakly informative prior"},
    "age_per_10y": {"log_or_mean": math.log(1.08), "log_or_sd": 0.07, "source": "weakly informative prior"},
    "extreme_bmi": {"log_or_mean": math.log(1.12), "log_or_sd": 0.08, "source": "weakly informative prior"},
    "high_genetic_multifdr_interaction": {"log_or_mean": math.log(1.20), "log_or_sd": 0.10, "source": "simulation stress-test prior"},
    "baseline_family_sd": {"mean": 0.18, "sd": 0.04, "source": "simulation heterogeneity prior"},
    "frailty_theta": {"mean": 0.22, "sd": 0.05, "source": "simulation heterogeneity prior"},
}
