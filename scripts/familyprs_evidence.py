from familyprs_config import *

def sigmoid(x):
    return expit(x)


def logor_se(item):
    m = math.log(item["or"])
    se = (math.log(item["hi"]) - math.log(item["lo"])) / (2 * 1.96)
    return m, se


def random_effects_meta(items):
    theta = np.array([logor_se(x)[0] for x in items], dtype=float)
    se = np.array([logor_se(x)[1] for x in items], dtype=float)
    v = se**2
    w = 1 / v
    mu_fixed = np.sum(w * theta) / np.sum(w)
    q = np.sum(w * (theta - mu_fixed) ** 2)
    df = len(theta) - 1
    c = np.sum(w) - np.sum(w * w) / np.sum(w)
    tau2 = max(0.0, (q - df) / max(c, 1e-12))
    wr = 1 / (v + tau2)
    mu = np.sum(wr * theta) / np.sum(wr)
    se_mu = math.sqrt(1 / np.sum(wr))
    return {
        "mean": float(mu),
        "se_mean": float(se_mu),
        "tau": float(math.sqrt(tau2)),
        "predictive_sd": float(math.sqrt(tau2 + se_mu**2)),
    }


def validate_pgs_compatibility():
    vals = list(PUBLIC_PGS.values())
    assert len({x["genome_build"] for x in vals}) == 1
    assert len({x["effect_weight_type"] for x in vals}) == 1
    assert len({x["source_gwas"] for x in vals}) == 1
    compatibility = {
        "trait": "Inflammatory bowel disease",
        "same_genome_build": vals[0]["genome_build"],
        "same_effect_weight_type": vals[0]["effect_weight_type"],
        "same_source_gwas": vals[0]["source_gwas"],
        "score_ids": list(PUBLIC_PGS),
        "interpretation": (
            "The scores are schema-compatible and target the same trait, but they are not statistically independent. "
            "They use different construction methods on substantially overlapping source evidence, so the analysis treats them as correlated predictors and learns a regularized stacked combination."
        ),
        "download_validation": (
            "The repository download script validates PGS Catalog format metadata, build and required columns when the scoring files are downloaded in an internet-enabled environment."
        ),
    }
    return compatibility


def evidence_prior_summary():
    pgs = {k: random_effects_meta(v["evaluations"]) for k, v in PUBLIC_PGS.items()}
    # The three methods share discovery/evaluation data. Do not treat them as independent studies.
    # We use the strongest meta-analytic mean to define a latent genetic-liability coefficient,
    # then map each score to that latent liability via an attenuation/correlation parameter.
    pgs_means = np.array([x["mean"] for x in pgs.values()])
    latent_beta_mean = float(np.max(pgs_means) / 0.93)
    latent_beta_sd = float(np.median([x["predictive_sd"] for x in pgs.values()]) * 0.35)
    rhos = {k: float(np.clip(v["mean"] / latent_beta_mean, 0.55, 0.95)) for k, v in pgs.items()}
    out = {
        "pgs": pgs,
        "latent_genetic_effect": {"mean": latent_beta_mean, "predictive_sd": max(0.04, latent_beta_sd)},
        "pgs_measurement_rho": rhos,
    }
    for key in ["female", "antibiotics", "affected_sibling", "fdr_2plus", "fdr_3plus"]:
        m, se = logor_se(EVIDENCE[key])
        out[key] = {"mean": m, "predictive_sd": se, "source": EVIDENCE[key]["source"]}
    for key in ["smoking", "age_per_10y", "extreme_bmi", "high_genetic_multifdr_interaction"]:
        out[key] = {
            "mean": EVIDENCE[key]["log_or_mean"],
            "predictive_sd": EVIDENCE[key]["log_or_sd"],
            "source": EVIDENCE[key]["source"],
        }
    return out


def draw_dgm_parameters(rng):
    p = evidence_prior_summary()
    d = {}
    d["genetic"] = float(rng.normal(p["latent_genetic_effect"]["mean"], p["latent_genetic_effect"]["predictive_sd"]))
    for k in ["female", "antibiotics", "affected_sibling", "fdr_2plus", "fdr_3plus", "smoking", "age_per_10y", "extreme_bmi", "high_genetic_multifdr_interaction"]:
        d[k] = float(rng.normal(p[k]["mean"], max(1e-4, p[k]["predictive_sd"])))
    d["baseline_family_sd"] = float(max(0.05, rng.normal(EVIDENCE["baseline_family_sd"]["mean"], EVIDENCE["baseline_family_sd"]["sd"])))
    d["frailty_theta"] = float(max(0.03, rng.normal(EVIDENCE["frailty_theta"]["mean"], EVIDENCE["frailty_theta"]["sd"])))
    return d, p


def calibrate_logistic_intercept(lp, target):
    lo, hi = -12.0, 2.0
    for _ in range(90):
        mid = (lo + hi) / 2
        if sigmoid(mid + lp).mean() > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def calibrate_exponential_baseline(lp, frailty, horizon, target):
    lo, hi = 1e-7, 0.2
    for _ in range(90):
        mid = (lo + hi) / 2
        p = 1 - np.exp(-mid * horizon * frailty * np.exp(lp))
        if p.mean() > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def inherit(f, m, rng):
    return 0.5 * f + 0.5 * m + rng.normal(0, math.sqrt(0.5), len(f))
