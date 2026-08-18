from familyprs_metrics import *

def model_candidates(name):
    if name == "pgs_stack":
        return [
            Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(penalty="l2", C=c, max_iter=3000))])
            for c in [0.005, 0.01, 0.05, 0.2]
        ]
    if name == "elastic_net":
        out = []
        for c, l1 in [(0.3, 0.1), (1.0, 0.1), (1.0, 0.6), (3.0, 0.6)]:
            out.append(
                Pipeline(
                    [
                        ("scale", StandardScaler()),
                        (
                            "model",
                            LogisticRegression(
                                penalty="elasticnet",
                                solver="saga",
                                C=c,
                                l1_ratio=l1,
                                max_iter=6000,
                                random_state=SEED,
                            ),
                        ),
                    ]
                )
            )
        return out
    if name == "xgboost":
        return [
            XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=SEED,
                n_jobs=4,
                tree_method="hist",
                verbosity=0,
                n_estimators=n,
                max_depth=d,
                learning_rate=lr,
                subsample=0.9,
                colsample_bytree=0.9,
                min_child_weight=8,
                reg_lambda=2.0,
            )
            for n, d, lr in [(160, 2, 0.05), (220, 3, 0.04)]
        ]
    if name == "lightgbm":
        return [
            LGBMClassifier(
                objective="binary",
                random_state=SEED,
                n_jobs=4,
                verbosity=-1,
                n_estimators=n,
                num_leaves=leaves,
                learning_rate=lr,
                min_child_samples=30,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_lambda=2.0,
            )
            for n, leaves, lr in [(180, 7, 0.05), (220, 15, 0.04)]
        ]
    if name == "catboost":
        return [
            CatBoostClassifier(
                verbose=False,
                random_seed=SEED,
                thread_count=4,
                loss_function="Logloss",
                iterations=it,
                depth=depth,
                learning_rate=lr,
                l2_leaf_reg=5,
                allow_writing_files=False,
            )
            for it, depth, lr in [(180, 3, 0.05), (220, 5, 0.04)]
        ]
    if name == "extra_trees":
        return [
            ExtraTreesClassifier(
                n_estimators=240,
                random_state=SEED,
                n_jobs=4,
                max_depth=depth,
                min_samples_leaf=leaf,
                max_features=mf,
            )
            for depth, leaf, mf in [(6, 8, "sqrt"), (10, 8, 0.7), (None, 15, 0.7)]
        ]
    if name == "hist_gradient_boosting":
        return [
            HistGradientBoostingClassifier(
                random_state=SEED,
                max_iter=it,
                learning_rate=lr,
                max_leaf_nodes=leaves,
                l2_regularization=2.0,
                min_samples_leaf=25,
            )
            for it, lr, leaves in [(180, 0.05, 7), (260, 0.035, 15), (180, 0.05, 15)]
        ]
    raise KeyError(name)


def model_features(name):
    return PGS_FEATURES if name == "pgs_stack" else FEATURES


def tune_model(name, dev):
    feats = model_features(name)
    cv = GroupKFold(n_splits=3, shuffle=True, random_state=SEED + 13)
    candidates = model_candidates(name)
    rows = []
    oofs = []
    for idx, est in enumerate(candidates):
        fold_losses, fold_auc = [], []
        oof = np.full(len(dev), np.nan)
        for tr, va in cv.split(dev, groups=dev.family_id):
            m = clone(est)
            m.fit(dev.iloc[tr][feats], dev.iloc[tr].incident_ibd_10y)
            p = m.predict_proba(dev.iloc[va][feats])[:, 1]
            oof[va] = p
            fold_losses.append(log_loss(dev.iloc[va].incident_ibd_10y, p, labels=[0, 1]))
            fold_auc.append(roc_auc_score(dev.iloc[va].incident_ibd_10y, p))
        rows.append({
            "candidate_index": idx,
            "mean_log_loss": float(np.mean(fold_losses)),
            "mean_auroc": float(np.mean(fold_auc)),
            "sd_auroc": float(np.std(fold_auc, ddof=1)),
            "min_auroc": float(np.min(fold_auc)),
            "max_auroc": float(np.max(fold_auc)),
            "fold_auroc": [float(x) for x in fold_auc],
        })
        oofs.append(oof)
    best = min(rows, key=lambda r: r["mean_log_loss"])
    return clone(candidates[best["candidate_index"]]), best, oofs[best["candidate_index"]]

def nested_repeated_group_cv(name, dev, repeats=2, outer_folds=4, inner_folds=3):
    """Nested grouped CV used for internal performance estimation.

    Hyperparameters are chosen only inside each outer-training partition.  The
    outer family fold therefore estimates performance without reusing the family
    that supplied the validation outcome for hyperparameter selection.
    """
    feats = model_features(name)
    candidates = model_candidates(name)
    records = []
    for rep in range(repeats):
        outer = GroupKFold(n_splits=outer_folds, shuffle=True, random_state=SEED + 7000 + rep)
        for fold, (tr, va) in enumerate(outer.split(dev, groups=dev.family_id)):
            outer_tr = dev.iloc[tr].reset_index(drop=True)
            outer_va = dev.iloc[va]
            inner = GroupKFold(n_splits=inner_folds, shuffle=True, random_state=SEED + 8000 + rep * 10 + fold)
            candidate_scores = []
            for idx, est in enumerate(candidates):
                losses, aucs = [], []
                for itr, iva in inner.split(outer_tr, groups=outer_tr.family_id):
                    m = clone(est)
                    m.fit(outer_tr.iloc[itr][feats], outer_tr.iloc[itr].incident_ibd_10y)
                    p = m.predict_proba(outer_tr.iloc[iva][feats])[:, 1]
                    losses.append(log_loss(outer_tr.iloc[iva].incident_ibd_10y, p, labels=[0, 1]))
                    aucs.append(roc_auc_score(outer_tr.iloc[iva].incident_ibd_10y, p))
                candidate_scores.append((float(np.mean(losses)), float(np.mean(aucs)), idx))
            _, inner_auc, best_idx = min(candidate_scores, key=lambda z: z[0])
            m = clone(candidates[best_idx])
            m.fit(outer_tr[feats], outer_tr.incident_ibd_10y)
            p = m.predict_proba(outer_va[feats])[:, 1]
            rec = metrics(outer_va.incident_ibd_10y.values, p)
            records.append({
                "repeat": rep, "fold": fold, "candidate_index": best_idx,
                "inner_mean_auroc": inner_auc, "auroc": rec["auroc"],
                "auprc": rec["auprc"], "brier": rec["brier"],
            })
    vals = np.array([r["auroc"] for r in records])
    summary = {
        "mean_auroc": float(vals.mean()),
        "sd_auroc": float(vals.std(ddof=1)),
        "min_auroc": float(vals.min()),
        "max_auroc": float(vals.max()),
        "mean_auprc": float(np.mean([r["auprc"] for r in records])),
        "mean_brier": float(np.mean([r["brier"] for r in records])),
        "n_outer_folds": len(records),
        "design": f"{repeats} repeats x {outer_folds} outer family folds with {inner_folds}-fold inner family tuning",
    }
    return records, summary

def pgs_single_oof(feature, dev, test):
    base = Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(C=1.0, max_iter=3000))])
    cv = GroupKFold(n_splits=5, shuffle=True, random_state=SEED + 500)
    oof = np.full(len(dev), np.nan)
    fold_auc = []
    for tr, va in cv.split(dev, groups=dev.family_id):
        m = clone(base).fit(dev.iloc[tr][[feature]], dev.iloc[tr].incident_ibd_10y)
        p = m.predict_proba(dev.iloc[va][[feature]])[:, 1]
        oof[va] = p
        fold_auc.append(roc_auc_score(dev.iloc[va].incident_ibd_10y, p))
    cal = calibrator_from_oof(oof, dev.incident_ibd_10y.values)
    final = clone(base).fit(dev[[feature]], dev.incident_ibd_10y)
    p = apply_calibrator(cal, final.predict_proba(test[[feature]])[:, 1])
    return {
        "feature": feature,
        "cv_mean_auroc": float(np.mean(fold_auc)),
        "cv_sd_auroc": float(np.std(fold_auc, ddof=1)),
        "test": metrics(test.incident_ibd_10y, p),
    }


def design_matrix_for_fixed(model, df):
    names = model.exog_names
    cols = [np.ones(len(df))]
    for n in names[1:]:
        cols.append(df[n].astype(float).values)
    return np.column_stack(cols)
