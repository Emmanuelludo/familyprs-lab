# RBesT-style evidence synthesis example for one compatible predictor.
# The Python generator uses an analogous random-effects predictive distribution.
make_map_prior <- function(est, se, tau_prior = 0.5) {
  if (!requireNamespace("RBesT", quietly = TRUE)) {
    stop("Install RBesT to run the MAP-prior example.")
  }
  RBesT::gMAP(
    cbind(est, se) | study,
    data = data.frame(est = est, se = se, study = seq_along(est)),
    family = gaussian,
    tau.dist = "HalfNormal",
    tau.prior = tau_prior
  )
}
