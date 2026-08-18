from familyprs_simulation import *

def calibration_stats(y, p):
    z = logit(np.clip(np.asarray(p), 1e-6, 1 - 1e-6)).reshape(-1, 1)
    m = LogisticRegression(C=1e8, solver="lbfgs", max_iter=3000).fit(z, y)
    return float(m.intercept_[0]), float(m.coef_[0, 0])


def metrics(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    ci, cs = calibration_stats(y, p)
    return {
        "n": int(len(y)),
        "events": int(y.sum()),
        "event_rate": float(y.mean()),
        "auroc": float(roc_auc_score(y, p)),
        "auprc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "calibration_intercept": ci,
        "calibration_slope": cs,
    }


def family_bootstrap_auc(df, p, n_boot=250):
    y = np.asarray(df.incident_ibd_10y.values)
    pred = np.asarray(p)
    fam = np.asarray(df.family_id.values)
    fams = np.unique(fam)
    indices = [np.flatnonzero(fam == f) for f in fams]
    rr = np.random.default_rng(SEED + 99)
    vals = []
    for _ in range(n_boot):
        pick = rr.integers(0, len(indices), size=len(indices))
        ix = np.concatenate([indices[j] for j in pick])
        yy = y[ix]
        if np.unique(yy).size == 2:
            vals.append(roc_auc_score(yy, pred[ix]))
    return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))]


def calibrator_from_oof(oof_p, y):
    z = logit(np.clip(np.asarray(oof_p), 1e-6, 1 - 1e-6)).reshape(-1, 1)
    return LogisticRegression(C=1e8, solver="lbfgs", max_iter=3000).fit(z, y)


def apply_calibrator(cal, p):
    z = logit(np.clip(np.asarray(p), 1e-6, 1 - 1e-6)).reshape(-1, 1)
    return cal.predict_proba(z)[:, 1]
