from familyprs_candidates import *

def mixed_oof_and_final(dev, test):
    formula = "incident_ibd_10y ~ " + " + ".join(FEATURES)
    mod = BinomialBayesMixedGLM.from_formula(formula, {"family": "0 + C(family_id)"}, dev)
    fit = mod.fit_vb()
    Xt = design_matrix_for_fixed(mod, test)
    p = sigmoid(Xt @ fit.fe_mean)
    cv_summary = {"mean_auroc": None, "note": "Final family-aware model fitted once on all development families; no repeated mixed-model CV."}
    return mod, fit, None, p, cv_summary, None

def gee_oof_and_final(dev, test):
    formula = "incident_ibd_10y ~ " + " + ".join(FEATURES)
    mod = GEE.from_formula(formula, "family_id", dev, cov_struct=Exchangeable(), family=Binomial())
    fit = mod.fit()
    p = np.asarray(fit.predict(test))
    cv_summary = {"mean_auroc": None, "note": "Final clustered estimating-equation model fitted once on all development families."}
    return mod, fit, None, p, cv_summary, None

def fit_shared_gamma_frailty(dev, test):
    cols = PGS_FEATURES + ["sex_female", "antibiotics_12m", "affected_sibling", "multi_fdr_2plus", "multi_fdr_3plus"]
    X = dev[cols].astype(float).values
    time = dev.event_time_y.values.astype(float)
    status = dev.event_observed.values.astype(int)
    families = dev.family_id.values
    groups = [np.flatnonzero(families == f) for f in np.unique(families)]

    def nll(par):
        beta = par[: len(cols)]
        lam = math.exp(par[-2])
        theta = math.exp(par[-1])
        eta = X @ beta
        ll = 0.0
        for ix in groups:
            d = int(status[ix].sum())
            H = float(np.sum(lam * time[ix] * np.exp(np.clip(eta[ix], -20, 20))))
            ll += d * math.log(lam) + float(np.sum(eta[ix][status[ix] == 1]))
            ll += gammaln(d + 1 / theta) - gammaln(1 / theta) + d * math.log(theta)
            ll -= (d + 1 / theta) * math.log1p(theta * H)
        return -ll

    init = np.zeros(len(cols) + 2)
    init[-2] = math.log(0.012)
    init[-1] = math.log(0.2)
    bounds = [(-2.5, 2.5)] * len(cols) + [(-8.5, -0.5), (-4.5, 1.5)]
    opt = minimize(nll, init, method="L-BFGS-B", bounds=bounds, options={"maxiter": 400})
    beta = opt.x[: len(cols)]
    lam = math.exp(opt.x[-2])
    theta = math.exp(opt.x[-1])
    eta_t = test[cols].astype(float).values @ beta
    # Marginal survival for a new family after integrating over gamma frailty.
    surv10 = (1 + theta * lam * HORIZON * np.exp(np.clip(eta_t, -20, 20))) ** (-1 / theta)
    p10 = 1 - surv10
    return {
        "columns": cols,
        "coef": {c: float(v) for c, v in zip(cols, beta)},
        "baseline_hazard": float(lam),
        "frailty_theta": float(theta),
        "converged": bool(opt.success),
        "objective": float(opt.fun),
        "test_metrics_10y": metrics(test.incident_ibd_10y, p10),
        "test_c_index": float(harrell_c_index(test.event_time_y.values, test.event_observed.values, eta_t)),
    }


def harrell_c_index(time, status, score):
    concord = ties = comp = 0
    n = len(time)
    for i in range(n):
        for j in range(i + 1, n):
            if time[i] == time[j]:
                continue
            if time[i] < time[j] and status[i] == 1:
                a, b = i, j
            elif time[j] < time[i] and status[j] == 1:
                a, b = j, i
            else:
                continue
            comp += 1
            if score[a] > score[b]:
                concord += 1
            elif score[a] == score[b]:
                ties += 1
    return (concord + 0.5 * ties) / comp if comp else float("nan")


def curves(y, p):
    pt, pp = calibration_curve(y, p, n_bins=8, strategy="quantile")
    fpr, tpr, _ = roc_curve(y, p)
    idx = np.linspace(0, len(fpr) - 1, min(120, len(fpr))).astype(int)
    return {
        "calibration": {"pred": pp.tolist(), "obs": pt.tolist()},
        "roc": {"fpr": fpr[idx].tolist(), "tpr": tpr[idx].tolist()},
    }
