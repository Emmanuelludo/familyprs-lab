"""Download and validate the three public IBD PGS scoring files used by FamilyPRS Lab.

The web demonstrator does not bundle the scoring files because two are large.  This script
is the genotype-level extension point: download the official PGS Catalog files, confirm
that their schema/build/weight conventions are compatible, and then pass them to a
standard score-calculation workflow (for example pgsc_calc) after target-genotype QC.
"""
from __future__ import annotations
import argparse
import gzip
from pathlib import Path
from urllib.request import urlretrieve

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "data" / "public" / "scoring_files"
SCORES = {
    "PGS004105": "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/PGS004105/ScoringFiles/PGS004105.txt.gz",
    "PGS003997": "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/PGS003997/ScoringFiles/PGS003997.txt.gz",
    "PGS004038": "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/PGS004038/ScoringFiles/PGS004038.txt.gz",
}


def inspect(path: Path):
    meta = {}
    columns = None
    with gzip.open(path, "rt") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("#"):
                if "=" in line:
                    k, v = line.lstrip("#").split("=", 1)
                    meta[k.strip()] = v.strip()
                continue
            columns = line.split("\t")
            break
    if columns is None:
        raise ValueError(f"No table header found in {path}")
    required = {"effect_allele", "effect_weight"}
    if not required.issubset(columns):
        raise ValueError(f"{path.name}: missing required columns {required - set(columns)}")
    build = meta.get("genome_build") or meta.get("HmPOS_build")
    weight = meta.get("weight_type")
    return {"metadata": meta, "columns": columns, "genome_build": build, "weight_type": weight}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate-only", action="store_true", help="validate already-downloaded files")
    args = ap.parse_args()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    reports = {}
    for pgs, url in SCORES.items():
        path = OUTDIR / f"{pgs}.txt.gz"
        if not path.exists() and not args.validate_only:
            print(f"Downloading {pgs}\n  {url}\n  -> {path}")
            urlretrieve(url, path)
        if not path.exists():
            raise FileNotFoundError(path)
        reports[pgs] = inspect(path)
        print(pgs, reports[pgs]["genome_build"], reports[pgs]["weight_type"], len(reports[pgs]["columns"]), "columns")

    builds = {r["genome_build"] for r in reports.values()}
    weights = {r["weight_type"] for r in reports.values()}
    if builds != {"GRCh38"}:
        raise ValueError(f"Unexpected build set: {builds}")
    if weights != {"beta"}:
        raise ValueError(f"Unexpected weight type set: {weights}")
    print("Compatibility check passed: all three scoring files use GRCh38 and beta weights with the standard PGS Catalog scoring schema.")


if __name__ == "__main__":
    main()
