# Future genotype-level extension: vectorized polygenic scoring.
# G: individuals x variants dosage matrix; beta: matching vector of effect weights.
# After allele/build harmonisation:
score_prs <- function(G, beta) {
  stopifnot(ncol(G) == length(beta))
  drop(G %*% beta)
}

standardize_prs <- function(prs, ref_mean, ref_sd) {
  (prs - ref_mean) / ref_sd
}
