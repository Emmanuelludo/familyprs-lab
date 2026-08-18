from familyprs_exports import *
from familyprs_fit import fit_predict_standard


def main():
    for p in ["data/public", "data/synthetic", "models", "results", "results/plots", "site/assets"]:
        (ROOT / p).mkdir(parents=True, exist_ok=True)

    compatibility = validate_pgs_compatibility()
    pop, pars, prior, b0base = simulate_population()
    cohort, risk, base_hazard = ascertain_and_simulate_incident(pop, pars)
    dev, test = split_development_test(risk)

    print(
        "population", len(pop), "families", pop.family_id.nunique(),
        "ascertained", cohort.family_id.nunique(), "risk", len(risk),
        "events10y", int(risk.incident_ibd_10y.sum()),
        "dev/test", len(dev), len(test),
    )

    # Single-score baselines.
    pgs_single = {}
    for pgs_id, meta in PUBLIC_PGS.items():
        pgs_single[pgs_id] = pgs_single_oof(meta["feature"], dev, test)

    # Tune on development families, then estimate development performance with repeated grouped CV.
    names = ["pgs_stack", "elastic_net", "xgboost", "lightgbm", "catboost"]
    fitted, calibrators, predictions, cv_summary, tuning, selected_estimators = {}, {}, {}, {}, {}, {}
    for name in names:
        print("tune", name, flush=True)
        est, tune, oof = tune_model(name, dev)
        final, cal, p = fit_predict_standard(name, est, dev, test, oof)
        fitted[name], calibrators[name], predictions[name] = final, cal, p
        selected_estimators[name] = est
        cv_summary[name], tuning[name] = tune, tune
        print(name, "CV", round(tune["mean_auroc"], 3), "test", round(roc_auc_score(test.incident_ibd_10y, p), 3), flush=True)

    # Family-aware estimation.
    print("fit mixed", flush=True)
    mm_mod, mm_fit, mm_cal, mm_p, mm_cv, _ = mixed_oof_and_final(dev, test)
    print("fit GEE", flush=True)
    gee_mod, gee_fit, gee_cal, gee_p, gee_cv, _ = gee_oof_and_final(dev, test)
    print("fit frailty", flush=True)
    frailty = fit_shared_gamma_frailty(dev, test)

    # AutoML ranking uses development family CV; final test remains untouched confirmation.
    ml_names = ["xgboost", "lightgbm", "catboost"]
    best_ml_name = max(ml_names, key=lambda k: cv_summary[k]["mean_auroc"])
    interactive_ml_name = max(["xgboost", "lightgbm"], key=lambda k: cv_summary[k]["mean_auroc"])
    repeated_family_cv = {}
    for nm in ["elastic_net", best_ml_name]:
        rec, summ = nested_repeated_group_cv(nm, dev, repeats=2, outer_folds=4, inner_folds=3)
        repeated_family_cv[nm] = {"summary": summ, "records": rec}

    group = {}
    curves_out = {}
    for name in names:
        group[name] = metrics(test.incident_ibd_10y.values, predictions[name])
        group[name]["auroc_ci95"] = family_bootstrap_auc(test, predictions[name])
        curves_out[name] = curves(test.incident_ibd_10y.values, predictions[name])
    group["mixed_random_intercept"] = metrics(test.incident_ibd_10y.values, mm_p)
    group["mixed_random_intercept"]["auroc_ci95"] = family_bootstrap_auc(test, mm_p)
    group["family_gee"] = metrics(test.incident_ibd_10y.values, gee_p)
    group["family_gee"]["auroc_ci95"] = family_bootstrap_auc(test, gee_p)
    curves_out["mixed_random_intercept"] = curves(test.incident_ibd_10y.values, mm_p)
    curves_out["family_gee"] = curves(test.incident_ibd_10y.values, gee_p)
    group["oracle_true_risk"] = {
        "auroc": float(roc_auc_score(test.incident_ibd_10y, test.true_incident_risk_10y)),
        "note": "Latent generating risk, included only to quantify the information ceiling in the simulated data-generating mechanism.",
    }

    auto_leaderboard = []
    for name in ml_names:
        auto_leaderboard.append(
            {
                "model": name,
                **cv_summary[name],
                "final_test_auroc": group[name]["auroc"],
                "final_test_brier": group[name]["brier"],
                "tuning": tuning[name],
            }
        )
    auto_leaderboard.sort(key=lambda x: x["mean_auroc"], reverse=True)

    sensitivity = sensitivity_analysis(test, fitted, calibrators, best_ml_name)

    result = {
        "target": "10-year incident IBD among baseline-unaffected relatives from IBD-ascertained families",
        "validation_design": {
            "final_holdout": "20% of families held out before model development",
            "development": "80% of families",
            "hyperparameter_selection": "3-fold grouped CV within development families for the locked final fit",
            "development_performance": "nested repeated family CV for Elastic Net and the selected ML model: 2 x 4 outer folds with 3-fold inner family tuning",
            "calibration": "logistic recalibration trained on out-of-fold development predictions from the selected grouped-CV specification",
            "final_test": "one locked evaluation on completely unseen families",
            "random_individual_split": "not used",
        },
        "split_counts": {
            "development": int(len(dev)),
            "test": int(len(test)),
            "families_development": int(dev.family_id.nunique()),
            "families_test": int(test.family_id.nunique()),
            "events_development": int(dev.incident_ibd_10y.sum()),
            "events_test": int(test.incident_ibd_10y.sum()),
        },
        "pgs_single": pgs_single,
        "development_cv": cv_summary,
        "repeated_family_cv": repeated_family_cv,
        "auto_ml_leaderboard": auto_leaderboard,
        "best_ml_model": best_ml_name,
        "interactive_ml_model": interactive_ml_name,
        "final_test": group,
        "curves": curves_out,
        "mixed_model_cv": mm_cv,
        "gee_cv": gee_cv,
        "frailty_model": frailty,
        "sensitivity": sensitivity,
        "dgm": {
            "horizon_years": HORIZON,
            "parameters_drawn": pars,
            "baseline_logistic_intercept": b0base,
            "incident_exponential_baseline_hazard": base_hazard,
            "prior_summary": prior,
            "population_families": int(pop.family_id.nunique()),
            "ascertained_families": int(cohort.family_id.nunique()),
            "at_risk_individuals": int(len(risk)),
            "incident_events": int(risk.incident_ibd_10y.sum()),
        },
        "pgs_compatibility": compatibility,
    }

    # Export interactive models.
    elastic_art = export_elastic(fitted["elastic_net"], calibrators["elastic_net"])
    xgb_art = export_xgb(fitted["xgboost"], calibrators["xgboost"])
    lgbm_art = export_lgbm(fitted["lightgbm"], calibrators["lightgbm"])
    mixed_art = export_mixed(mm_mod, mm_fit, mm_cal)
    arts = {"elastic": elastic_art, "xgb": xgb_art, "lgbm": lgbm_art, "mixed": mixed_art}

    # Verify exported tree evaluators against native raw margins on a small sample.
    chk = test.iloc[:30]
    x_native = fitted["xgboost"].predict(chk[FEATURES], output_margin=True)
    x_manual = []
    for _, r in chk.iterrows():
        _, margin = pred_xgb_art(xgb_art, {f: float(r[f]) for f in FEATURES})
        x_manual.append(margin)
    if np.max(np.abs(np.asarray(x_native) - np.asarray(x_manual))) > 5e-2:
        raise RuntimeError("XGBoost export evaluator mismatch")
    l_native = fitted["lightgbm"].predict(chk[FEATURES], raw_score=True)
    l_manual = []
    for _, r in chk.iterrows():
        _, raw = pred_lgb_art(lgbm_art, {f: float(r[f]) for f in FEATURES})
        l_manual.append(raw)
    if np.max(np.abs(np.asarray(l_native) - np.asarray(l_manual))) > 1e-4:
        raise RuntimeError("LightGBM export evaluator mismatch")

    demos = make_demo_families(cohort, risk, arts, interactive_ml_name)

    drop_private = ["g_true", "family_env", "frailty_true"]
    cohort[cohort.family_id.isin([d["family_id"] for d in demos])].drop(columns=[c for c in drop_private if c in cohort.columns]).to_csv(
        ROOT / "data/synthetic/demo_family_members.csv", index=False
    )
    risk.sample(min(16000, len(risk)), random_state=SEED).drop(columns=[c for c in drop_private if c in risk.columns]).to_csv(
        ROOT / "data/synthetic/modeling_sample.csv", index=False
    )

    (ROOT / "data/public/pgs_catalog_metadata.json").write_text(json.dumps(PUBLIC_PGS, indent=2))
    (ROOT / "data/public/pgs_compatibility.json").write_text(json.dumps(compatibility, indent=2))
    (ROOT / "data/public/evidence_summary.json").write_text(json.dumps(prior, indent=2))
    (ROOT / "results/model_results.json").write_text(json.dumps(result, indent=2))
    (ROOT / "site/assets/model_results.json").write_text(json.dumps(result, indent=2))
    (ROOT / "site/assets/demo_families.json").write_text(json.dumps(demos, indent=2))

    for name, obj in [("elastic_net", elastic_art), ("xgboost", xgb_art), ("lightgbm", lgbm_art), ("mixed_random_intercept", mixed_art)]:
        (ROOT / f"models/{name}.json").write_text(json.dumps(obj, separators=(",", ":")))

    js_payload = {
        "families": demos,
        "results": result,
        "elastic": elastic_art,
        "xgb": xgb_art,
        "lgbm": lgbm_art,
        "mixed": mixed_art,
        "pgs": PUBLIC_PGS,
        "evidence": prior,
        "interactive_ml_model": interactive_ml_name,
    }
    (ROOT / "site/assets/data.js").write_text("window.FAMILYPRS_DATA=" + json.dumps(js_payload, separators=(",", ":")) + ";\n")

    print("best ML", best_ml_name, "interactive", interactive_ml_name)
    print("CV elastic", cv_summary["elastic_net"])
    print("CV best ML", cv_summary[best_ml_name])
    print("test elastic", group["elastic_net"])
    print("test best ML", group[best_ml_name])
    print("frailty", frailty)
