# R extension sketch for a nonlinear benchmark with family-grouped resampling.
# The same observed predictor block used by Elastic Net should be supplied to
# XGBoost, LightGBM or CatBoost. Model comparison is based on grouped family CV,
# not a random individual split.

# library(xgboost)
# dtrain <- xgb.DMatrix(data = x_development, label = y_development)
# fit <- xgb.train(
#   params = list(
#     objective = "binary:logistic",
#     eval_metric = "logloss",
#     max_depth = 2,
#     eta = 0.05,
#     subsample = 0.8,
#     colsample_bytree = 0.85
#   ),
#   data = dtrain,
#   nrounds = 100,
#   verbose = 0
# )
#
# Hyperparameters should be selected with folds defined on family_id, after
# which the chosen learner is refitted on all development families and assessed
# once on the locked final families.
