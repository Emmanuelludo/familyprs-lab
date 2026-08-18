# R analogue of the regularised multi-PGS benchmark.
# Family ID is the resampling unit. The final test families must be locked before
# this code is run on the development data.

library(glmnet)

# x <- model.matrix(
#   ~ pgs_pt_z + pgs_lassosum_z + pgs_ldpred2_z +
#     age + sex_female + current_smoker + bmi + antibiotics_12m +
#     n_affected_fdr + affected_parent + affected_sibling +
#     min_relative_onset_age + multi_fdr_2plus + multi_fdr_3plus,
#   data = development
# )[,-1]
# y <- development$incident_ibd_10y
#
# family_fold <- ...  # exactly one grouped fold per unique family_id
# foldid <- family_fold[match(development$family_id, names(family_fold))]
#
# fit <- cv.glmnet(
#   x, y,
#   family = "binomial",
#   alpha = 0.5,
#   foldid = foldid,
#   type.measure = "deviance"
# )
#
# Refit the selected specification on all development families, estimate any
# recalibration from development out-of-fold predictions, and evaluate once on
# the locked family test set.
