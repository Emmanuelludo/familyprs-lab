from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from familyprs_evidence import evidence_prior_summary, validate_pgs_compatibility
from familyprs_simulation import simulate_population, add_family_history
from familyprs_candidates import model_candidates, model_features


def test_pgs_metadata_are_compatible_but_not_treated_as_independent():
    meta = validate_pgs_compatibility()
    assert meta["same_genome_build"] == "GRCh38"
    assert meta["same_effect_weight_type"] == "beta"
    assert meta["same_source_gwas"] == "GCST004131"
    assert len(meta["score_ids"]) == 3
    assert "not statistically independent" in meta["interpretation"]


def test_evidence_layer_defines_score_specific_measurement_loadings():
    prior = evidence_prior_summary()
    assert set(prior["pgs_measurement_rho"]) == {"PGS004105", "PGS003997", "PGS004038"}
    assert all(0 < x <= 1 for x in prior["pgs_measurement_rho"].values())
    assert prior["latent_genetic_effect"]["predictive_sd"] > 0


def test_small_family_population_has_mendelian_style_structure():
    pop, _, _, _ = simulate_population(n_families=40, children=3)
    assert pop.family_id.nunique() == 40
    assert len(pop) == 40 * 5
    assert set(pop.role.unique()) == {"father", "mother", "child1", "child2", "child3"}
    assert {"pgs_pt_z", "pgs_lassosum_z", "pgs_ldpred2_z"}.issubset(pop.columns)


def test_family_history_is_derived_from_realised_pedigree():
    pop, _, _, _ = simulate_population(n_families=80, children=3, target_baseline_prevalence=0.10)
    hist = add_family_history(pop)
    required = {"n_affected_fdr", "affected_parent", "affected_sibling", "multi_fdr_2plus", "multi_fdr_3plus"}
    assert required.issubset(hist.columns)
    assert (hist["n_affected_fdr"] >= 0).all()


def test_model_candidate_blocks_exist():
    assert len(model_candidates("elastic_net")) >= 2
    assert len(model_candidates("xgboost")) >= 2
    assert len(model_candidates("lightgbm")) >= 2
    assert len(model_candidates("catboost")) >= 2
    assert model_features("pgs_stack") == ["pgs_pt_z", "pgs_lassosum_z", "pgs_ldpred2_z"]


def test_deployed_site_assets_exist():
    assert (ROOT / "index.html").exists()
    for name in ["app.js", "styles.css", "curves.js", "data_a.js", "data_b.js", "data_c.js", "xgb_trees.js"]:
        assert (ROOT / "assets" / name).exists()
