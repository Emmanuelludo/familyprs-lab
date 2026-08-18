# Genotype-level kinship/GRM extension.
# This becomes executable once `grm` is supplied as a valid relationship matrix
# aligned to the rows of `dat`.
fit_kinship_glmm <- function(dat, grm) {
  if (!requireNamespace("GMMAT", quietly = TRUE)) {
    stop("Install GMMAT for the genotype-level kinship GLMM stage.")
  }
  stopifnot(nrow(grm) == nrow(dat), ncol(grm) == nrow(dat))
  form <- incident_ibd_10y ~ pgs_pt_z + pgs_lassosum_z + pgs_ldpred2_z +
    age + sex_female + current_smoker + bmi + antibiotics_12m +
    n_affected_fdr + affected_parent + affected_sibling +
    multi_fdr_2plus + multi_fdr_3plus
  GMMAT::glmmkin(
    fixed = form,
    data = dat,
    kins = grm,
    family = binomial(link = "logit")
  )
}
