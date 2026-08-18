# Public IBD PGS compatibility check

Checked against the PGS Catalog on 2026-08-18.

FamilyPRS Lab uses three IBD score definitions as correlated genetic summaries:

| Score | Construction | Variants | Original build | Weight | Source GWAS |
|---|---|---:|---|---|---|
| PGS004105 | P+T / clumping | 139 | GRCh38 | beta | GCST004131 |
| PGS003997 | lassosum | 8,406 | GRCh38 | beta | GCST004131 |
| PGS004038 | LDpred2.CV | 1,018,068 | GRCh38 | beta | GCST004131 |

## Compatibility conclusion

The three scores can be calculated in the same target genotype dataset after ordinary genotype QC and allele harmonisation because:

1. they target the same reported trait, inflammatory bowel disease;
2. all three report GRCh38 as the original genome build;
3. all three use beta effect weights;
4. the PGS Catalog scoring-file schema uses `effect_allele` and `effect_weight` as the required scoring fields;
5. they were evaluated within the same methodological benchmark and use the same source GWAS.

They are **not statistically independent scores**. Their source evidence overlaps heavily. The relevant difference is the score-construction method, so the analysis treats the three values as correlated predictors and learns a regularised combination.

## File-level validation hook

`scripts/download_public_pgs.py` points to the official scoring-file locations. In an internet-enabled analysis environment it downloads each gzip file and checks:

- table header is present;
- `effect_allele` exists;
- `effect_weight` exists;
- genome build is GRCh38;
- weight type is beta.

The original development sandbox allowed the official score metadata and scoring-file specification to be inspected but did not reliably stream the large FTP gzip files. The project therefore does not claim a byte-level score-file validation run in that sandbox. The validator is included so that the check can be rerun immediately in the genotype-level stage.

## Practical scoring requirement

Schema/build compatibility does not remove the need for target-data harmonisation. Before applying the scores to real genotypes, the analysis still needs to check effect-allele orientation, strand-ambiguous variants, missing variants, genotype build, ancestry/QC and the treatment of overlapping variants across scores. A harmonised PGS Catalog scoring file or `pgsc_calc` workflow would be appropriate for this stage.
