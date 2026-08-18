from familyprs_evidence import *

def simulate_population(n_families=18000, children=3, target_baseline_prevalence=0.018):
    pars, prior = draw_dgm_parameters(RNG)
    rhos = prior["pgs_measurement_rho"]
    fam = pd.DataFrame({"family_id": [f"F{j:05d}" for j in range(n_families)]})
    fam["family_env"] = RNG.normal(0, pars["baseline_family_sd"], n_families)
    fam["father_g"] = RNG.normal(0, 1, n_families)
    fam["mother_g"] = RNG.normal(0, 1, n_families)
    for pgs_id in PUBLIC_PGS:
        fam[f"father_h_{pgs_id}"] = RNG.normal(0, 1, n_families)
        fam[f"mother_h_{pgs_id}"] = RNG.normal(0, 1, n_families)
    fam["father_age"] = np.clip(RNG.normal(59, 9, n_families), 38, 82)
    fam["mother_age"] = np.clip(fam.father_age - RNG.normal(2, 4, n_families), 36, 80)

    rows = []

    def founder_frame(role, sex, gcol, agecol, prefix):
        out = pd.DataFrame(
            {
                "family_id": fam.family_id,
                "member_id": fam.family_id + "_" + role,
                "role": role,
                "sex": sex,
                "g_true": fam[gcol].values,
                "age": fam[agecol].values,
                "family_env": fam.family_env.values,
            }
        )
        for pgs_id, meta in PUBLIC_PGS.items():
            rho = rhos[pgs_id]
            h = fam[f"{prefix}_h_{pgs_id}"].values
            out[meta["feature"]] = rho * out.g_true.values + math.sqrt(1 - rho**2) * h
        return out

    rows.append(founder_frame("father", "M", "father_g", "father_age", "father"))
    rows.append(founder_frame("mother", "F", "mother_g", "mother_age", "mother"))

    for k in range(children):
        cg = inherit(fam.father_g.values, fam.mother_g.values, RNG)
        c_age = np.clip(
            np.minimum(fam.father_age.values, fam.mother_age.values)
            - RNG.normal(27, 4, n_families)
            - k * RNG.normal(1.5, 0.6, n_families),
            18,
            58,
        )
        c_sex = RNG.choice(["F", "M"], n_families)
        out = pd.DataFrame(
            {
                "family_id": fam.family_id,
                "member_id": fam.family_id + f"_child{k+1}",
                "role": f"child{k+1}",
                "sex": c_sex,
                "g_true": cg,
                "age": c_age,
                "family_env": fam.family_env.values,
            }
        )
        for pgs_id, meta in PUBLIC_PGS.items():
            rho = rhos[pgs_id]
            ch = inherit(fam[f"father_h_{pgs_id}"].values, fam[f"mother_h_{pgs_id}"].values, RNG)
            out[meta["feature"]] = rho * cg + math.sqrt(1 - rho**2) * ch
        rows.append(out)

    d = pd.concat(rows, ignore_index=True)
    agec = (d.age.values - 40) / 10
    d["sex_female"] = (d.sex == "F").astype(int)
    d["current_smoker"] = RNG.binomial(1, sigmoid(-1.6 + 0.25 * agec + 0.15 * (d.sex.values == "M")))
    d["bmi"] = np.clip(RNG.normal(25.5 + 0.25 * agec, 4.2, len(d)), 16, 43)
    d["antibiotics_12m"] = RNG.binomial(1, sigmoid(-1.45 + 0.10 * agec + 0.15 * d.current_smoker.values))

    lp = (
        pars["genetic"] * d.g_true.values
        + pars["female"] * d.sex_female.values
        + pars["antibiotics"] * d.antibiotics_12m.values
        + 0.35 * pars["smoking"] * d.current_smoker.values
        + 0.35 * pars["age_per_10y"] * agec
        + d.family_env.values
    )
    b0 = calibrate_logistic_intercept(lp, target_baseline_prevalence)
    d["baseline_ibd"] = RNG.binomial(1, sigmoid(b0 + lp))
    subtype = RNG.choice(["Crohn disease", "Ulcerative colitis"], p=[0.56, 0.44], size=len(d))
    d["ibd_subtype"] = np.where(d.baseline_ibd.eq(1), subtype, "Unaffected")
    d["age_at_onset"] = np.where(
        d.baseline_ibd.eq(1),
        np.round(np.maximum(12, d.age.values - RNG.gamma(2, 6, len(d))), 1),
        np.nan,
    )
    return d, pars, prior, b0


def add_family_history(d):
    out_parts = []
    for fid, g in d.groupby("family_id", sort=False):
        g = g.copy()
        by_role = {r.role: r for _, r in g.iterrows()}
        for idx, r in g.iterrows():
            if r.role.startswith("child"):
                fdr_roles = ["father", "mother"] + [x for x in by_role if x.startswith("child") and x != r.role]
            else:
                fdr_roles = [x for x in by_role if x.startswith("child")]
            fdrs = [by_role[x] for x in fdr_roles if x in by_role]
            aff = [x for x in fdrs if int(x.baseline_ibd) == 1]
            g.loc[idx, "n_affected_fdr"] = len(aff)
            g.loc[idx, "affected_parent"] = int(r.role.startswith("child") and any(x.role in ("father", "mother") and int(x.baseline_ibd) for x in fdrs))
            g.loc[idx, "affected_sibling"] = int(r.role.startswith("child") and any(x.role.startswith("child") and int(x.baseline_ibd) for x in fdrs))
            ages = [float(x.age_at_onset) for x in aff if not pd.isna(x.age_at_onset)]
            g.loc[idx, "min_relative_onset_age"] = min(ages) if ages else 60.0
            g.loc[idx, "multi_fdr_2plus"] = int(len(aff) >= 2)
            g.loc[idx, "multi_fdr_3plus"] = int(len(aff) >= 3)
        out_parts.append(g)
    out = pd.concat(out_parts, ignore_index=True)
    for c in ["n_affected_fdr", "affected_parent", "affected_sibling", "multi_fdr_2plus", "multi_fdr_3plus"]:
        out[c] = out[c].astype(int)
    return out


def ascertain_and_simulate_incident(pop, pars, max_families=700, target_10y_event_rate=0.13):
    fam_has_case = pop.groupby("family_id").baseline_ibd.max()
    eligible = fam_has_case[fam_has_case.eq(1)].index.to_numpy()
    if len(eligible) > max_families:
        eligible = RNG.choice(eligible, max_families, replace=False)
    cohort = pop[pop.family_id.isin(eligible)].copy()
    cohort = add_family_history(cohort)

    cases = cohort[cohort.baseline_ibd.eq(1)].sort_values(["family_id", "age_at_onset"])
    probands = cases.groupby("family_id").first()["member_id"].to_dict()
    cohort["is_proband"] = [int(probands.get(fid) == mid) for fid, mid in zip(cohort.family_id, cohort.member_id)]

    risk = cohort[cohort.baseline_ibd.eq(0)].copy()
    theta = pars["frailty_theta"]
    fams = risk.family_id.unique()
    frailty = pd.Series(RNG.gamma(shape=1 / theta, scale=theta, size=len(fams)), index=fams)
    risk["frailty_true"] = risk.family_id.map(frailty).astype(float)
    agec = (risk.age.values - 35) / 10
    lp = (
        pars["genetic"] * risk.g_true.values
        + pars["female"] * risk.sex_female.values
        + pars["antibiotics"] * risk.antibiotics_12m.values
        + pars["smoking"] * risk.current_smoker.values
        + pars["age_per_10y"] * agec
        + pars["affected_sibling"] * risk.affected_sibling.values
        + pars["fdr_2plus"] * risk.multi_fdr_2plus.values
        + max(0.0, pars["fdr_3plus"] - pars["fdr_2plus"]) * risk.multi_fdr_3plus.values
        + pars["extreme_bmi"] * ((risk.bmi.values < 20) | (risk.bmi.values > 32))
        + pars["high_genetic_multifdr_interaction"] * ((risk.g_true.values > 1.25) & (risk.n_affected_fdr.values >= 2))
    )
    base_hazard = calibrate_exponential_baseline(lp, risk.frailty_true.values, HORIZON, target_10y_event_rate)
    hazard = base_hazard * risk.frailty_true.values * np.exp(lp)
    p10 = 1 - np.exp(-hazard * HORIZON)
    t = RNG.exponential(1 / np.clip(hazard, 1e-10, None))
    risk["event_time_y"] = np.minimum(t, HORIZON)
    risk["event_observed"] = (t <= HORIZON).astype(int)
    risk["incident_ibd_10y"] = risk.event_observed.astype(int)
    risk["true_incident_risk_10y"] = p10
    return cohort, risk, base_hazard


def split_development_test(df, test_size=0.20):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=SEED)
    dev_idx, test_idx = next(gss.split(df, groups=df.family_id))
    return df.iloc[dev_idx].copy(), df.iloc[test_idx].copy()
