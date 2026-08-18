from familyprs_candidates import *


def fit_predict_standard(name, estimator, dev, test, oof_predictions):
    """Refit a selected classifier on all development families and recalibrate.

    The probability recalibrator is learned only from grouped out-of-fold
    predictions in the development set. The locked test families are used once.
    """
    features = model_features(name)
    calibrator = calibrator_from_oof(oof_predictions, dev.incident_ibd_10y.values)
    final = clone(estimator).fit(dev[features], dev.incident_ibd_10y)
    raw_test = final.predict_proba(test[features])[:, 1]
    return final, calibrator, apply_calibrator(calibrator, raw_test)
