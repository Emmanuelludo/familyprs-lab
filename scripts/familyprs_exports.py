from familyprs_dependence import *

def export_elastic(est, cal):
    scale = est.named_steps["scale"]
    lm = est.named_steps["model"]
    return {
        "features": FEATURES,
        "mean": scale.mean_.tolist(),
        "scale": scale.scale_.tolist(),
        "coef": lm.coef_[0].tolist(),
        "intercept": float(lm.intercept_[0]),
        "calibration_coef": 1.0 if cal is None else float(cal.coef_[0, 0]),
        "calibration_intercept": 0.0 if cal is None else float(cal.intercept_[0]),
    }


def export_xgb(est, cal):
    booster = est.get_booster()
    trees = [json.loads(s) for s in booster.get_dump(dump_format="json")]
    cfg = json.loads(booster.save_config())
    base = float(str(cfg["learner"]["learner_model_param"]["base_score"]).strip("[]"))
    return {
        "features": FEATURES,
        "trees": trees,
        "base_score": base,
        "calibration_coef": float(cal.coef_[0, 0]),
        "calibration_intercept": float(cal.intercept_[0]),
    }


def export_lgbm(est, cal):
    return {
        "features": FEATURES,
        "dump": est.booster_.dump_model(),
        "calibration_coef": float(cal.coef_[0, 0]),
        "calibration_intercept": float(cal.intercept_[0]),
    }


def export_mixed(mod, fit, cal):
    return {
        "features": mod.exog_names[1:],
        "coef": [float(x) for x in fit.fe_mean[1:]],
        "intercept": float(fit.fe_mean[0]),
        "calibration_coef": 1.0 if cal is None else float(cal.coef_[0, 0]),
        "calibration_intercept": 0.0 if cal is None else float(cal.intercept_[0]),
        "variance_component_log_sd": [float(x) for x in fit.vcp_mean],
        "prediction_note": "For a previously unseen family, the random intercept is integrated at its population mean for the displayed fixed-effect prediction.",
    }


def pred_elastic_art(art, row):
    x = np.array([row[f] for f in art["features"]], dtype=float)
    z = (x - np.asarray(art["mean"])) / np.asarray(art["scale"])
    raw = art["intercept"] + float(np.dot(z, np.asarray(art["coef"])))
    return float(sigmoid(art["calibration_intercept"] + art["calibration_coef"] * raw))


def xgb_eval_tree(tree, row):
    if "leaf" in tree:
        return float(tree["leaf"])
    val = row.get(tree["split"], np.nan)
    if val is None or (isinstance(val, float) and math.isnan(val)):
        nxt = int(tree["missing"])
    else:
        nxt = int(tree["yes"]) if float(val) < float(tree["split_condition"]) else int(tree["no"])
    child = next(c for c in tree["children"] if int(c["nodeid"]) == nxt)
    return xgb_eval_tree(child, row)


def pred_xgb_art(art, row):
    margin = float(logit(np.clip(art["base_score"], 1e-8, 1 - 1e-8)))
    margin += sum(xgb_eval_tree(t, row) for t in art["trees"])
    return float(sigmoid(art["calibration_intercept"] + art["calibration_coef"] * margin)), margin


def lgb_eval_tree(node, row, features):
    if "leaf_value" in node:
        return float(node["leaf_value"])
    fi = int(node["split_feature"])
    val = float(row[features[fi]])
    threshold = float(node["threshold"])
    go_left = val <= threshold
    child = node["left_child"] if go_left else node["right_child"]
    return lgb_eval_tree(child, row, features)


def pred_lgb_art(art, row):
    raw = 0.0
    for t in art["dump"]["tree_info"]:
        raw += lgb_eval_tree(t["tree_structure"], row, art["features"])
    return float(sigmoid(art["calibration_intercept"] + art["calibration_coef"] * raw)), raw


def pred_mixed_art(art, row):
    raw = art["intercept"] + sum(float(c) * float(row[f]) for f, c in zip(art["features"], art["coef"]))
    return float(sigmoid(art["calibration_intercept"] + art["calibration_coef"] * raw))


def model_predict(est, name, df):
    return est.predict_proba(df[model_features(name)])[:, 1]


def sensitivity_analysis(test, fitted, calibrators, best_ml_name):
    rr = np.random.default_rng(SEED + 9000)
    scenarios = []

    def evaluate(label, d, y=None):
        yy = test.incident_ibd_10y.values if y is None else y
        out = {"scenario": label, "n": int(len(d)), "events": int(np.sum(yy))}
        for name in ["elastic_net", best_ml_name]:
            raw = model_predict(fitted[name], name, d)
            pp = apply_calibrator(calibrators[name], raw)
            out[name] = {"auroc": float(roc_auc_score(yy, pp)), "brier": float(brier_score_loss(yy, pp))}
        scenarios.append(out)

    evaluate("Reference", test.copy())

    d = test.copy()
    for f in PGS_FEATURES:
        d[f] += rr.normal(0, 0.35, len(d))
    evaluate("PGS measurement noise", d)

    d = test.copy()
    mask = rr.random(len(d)) < 0.20
    for f in ["n_affected_fdr", "affected_parent", "affected_sibling", "multi_fdr_2plus", "multi_fdr_3plus"]:
        d.loc[mask, f] = 0
    d.loc[mask, "min_relative_onset_age"] = 60
    evaluate("20% family history missing", d)

    d = test.copy()
    flip = rr.random(len(d)) < 0.15
    d.loc[flip, "antibiotics_12m"] = 1 - d.loc[flip, "antibiotics_12m"]
    evaluate("15% antibiotic misclassification", d)

    y = test.incident_ibd_10y.values.copy()
    flip_y = rr.random(len(y)) < 0.05
    y[flip_y] = 1 - y[flip_y]
    evaluate("5% outcome misclassification", test.copy(), y)

    high = test[test.n_affected_fdr >= 2].copy()
    if len(high) > 40 and high.incident_ibd_10y.nunique() == 2:
        out = {"scenario": "Multiplex-family subgroup", "n": int(len(high)), "events": int(high.incident_ibd_10y.sum())}
        for name in ["elastic_net", best_ml_name]:
            raw = model_predict(fitted[name], name, high)
            pp = apply_calibrator(calibrators[name], raw)
            out[name] = {"auroc": float(roc_auc_score(high.incident_ibd_10y, pp)), "brier": float(brier_score_loss(high.incident_ibd_10y, pp))}
        scenarios.append(out)
    return scenarios


def make_demo_families(cohort, risk, arts, interactive_ml_name, n=12):
    counts = risk.groupby("family_id").size()
    fids = counts[counts >= 2].index
    fs = risk[risk.family_id.isin(fids)].groupby("family_id").pgs_ldpred2_z.max().sort_values()
    picks = []
    for q in np.linspace(0.05, 0.95, n):
        picks.append(fs.index[min(len(fs) - 1, int(q * (len(fs) - 1)))])
    demos = []
    for fid in list(dict.fromkeys(picks)):
        members = cohort[cohort.family_id.eq(fid)].sort_values("role")
        at = risk[risk.family_id.eq(fid)]
        sel = at.sort_values("pgs_ldpred2_z", ascending=False).iloc[0]
        payload = []
        for _, m in members.iterrows():
            pgs_payload = {}
            for pgs_id, meta in PUBLIC_PGS.items():
                z = float(m[meta["feature"]])
                pgs_payload[pgs_id] = {
                    "z": round(z, 4),
                    "percentile": round(float(100 * 0.5 * (1 + math.erf(z / math.sqrt(2)))), 1),
                }
            payload.append(
                {
                    "member_id": m.member_id,
                    "role": m.role,
                    "sex": m.sex,
                    "age": round(float(m.age), 1),
                    "pgs": pgs_payload,
                    "baseline_ibd": int(m.baseline_ibd),
                    "ibd_subtype": m.ibd_subtype,
                    "age_at_onset": None if pd.isna(m.age_at_onset) else round(float(m.age_at_onset), 1),
                    "current_smoker": int(m.current_smoker),
                    "bmi": round(float(m.bmi), 1),
                    "antibiotics_12m": int(m.antibiotics_12m),
                }
            )
        row = {f: float(sel[f]) for f in FEATURES}
        e = pred_elastic_art(arts["elastic"], row)
        mm = pred_mixed_art(arts["mixed"], row)
        if interactive_ml_name == "xgboost":
            ml, _ = pred_xgb_art(arts["xgb"], row)
        else:
            ml, _ = pred_lgb_art(arts["lgbm"], row)
        demos.append(
            {
                "family_id": fid,
                "selected_member_id": sel.member_id,
                "members": payload,
                "initial_predictions": {"elastic_net": e, "mixed": mm, "ml": ml},
            }
        )
    return demos
