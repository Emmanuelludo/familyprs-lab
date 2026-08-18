module.exports = function buildSlides(ctx) {
  const { pptx, R, PGS, C, addTitle, card, source, arrow, metric, img, path, ROOT } = ctx;
// 7 validation
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Validation','Model development and final testing are separated by family','The resampling unit is the family throughout. Random individual splitting is not used in the reported analysis.');
  const y=2.45;
  card(s,.72,y,2.5,1.42,'1. Lock test families',`${R.split_counts.families_test} families held out before tuning\n${R.split_counts.events_test} incident events`,{fill:C.sand,line:'E7D8BC',fontSize:10.2});
  arrow(s,3.25,3.15,3.62,3.15);
  card(s,3.67,y,2.5,1.42,'2. Develop',`${R.split_counts.families_development} families\nGrouped CV for hyperparameters`,{fill:C.paper,fontSize:10.2});
  arrow(s,6.20,3.15,6.57,3.15);
  card(s,6.62,y,2.5,1.42,'3. Cross-fit',`Out-of-fold development predictions\nProbability recalibration`,{fill:C.tealSoft,line:'B7DEDA',fontSize:10.2});
  arrow(s,9.15,3.15,9.52,3.15);
  card(s,9.57,y,2.5,1.42,'4. Refit and test',`Fit on all development families\nEvaluate once on locked families`,{fill:C.paper,fontSize:10.2});
  const re=R.repeated_family_cv.elastic_net.summary;
  const rc=R.repeated_family_cv[R.best_ml_model].summary;
  card(s,.9,4.45,3.55,1.55,'Internal stability',`Elastic Net repeated family CV: ${re.mean_auroc.toFixed(3)} mean AUROC\nrange ${re.min_auroc.toFixed(3)} to ${re.max_auroc.toFixed(3)}`,{fontSize:10.8});
  card(s,4.9,4.45,3.55,1.55,'Selected ML stability',`CatBoost repeated family CV: ${rc.mean_auroc.toFixed(3)} mean AUROC\nrange ${rc.min_auroc.toFixed(3)} to ${rc.max_auroc.toFixed(3)}`,{fontSize:10.8});
  card(s,8.9,4.45,3.55,1.55,'Final-test role','Development CV estimates internal stability. The locked family test remains the final estimate of transport to unseen families.',{fill:C.tealSoft,line:'B7DEDA',fontSize:10.8});
}

// 8 development and automl
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Development results','AutoML does not displace the regularised statistical model','CatBoost is the strongest boosted learner during model development, but the margin over XGBoost is small and the absolute CV differences are modest.');
  img(s,'development_vs_test_auc.png',.72,2.30,7.05,4.15);
  const lead=R.auto_ml_leaderboard;
  const y0=2.48;
  s.addText('AutoML development leaderboard',{x:8.12,y:2.32,w:3.9,h:.28,fontSize:11.5,bold:true,color:C.ink,margin:0});
  lead.forEach((m,i)=>{
    const y=y0+.55+i*.70;
    s.addShape(pptx.ShapeType.roundRect,{x:8.12,y,w:4.1,h:.55,rectRadius:.03,fill:{color:i===0?C.tealSoft:C.paper},line:{color:i===0?'B7DEDA':C.line}});
    s.addText(`${i+1}. ${m.model==='catboost'?'CatBoost':m.model==='xgboost'?'XGBoost':'LightGBM'}`,{x:8.30,y:y+.13,w:1.5,h:.20,fontSize:10.2,bold:true,color:C.ink,margin:0});
    s.addText(`CV ${m.mean_auroc.toFixed(3)}`,{x:9.95,y:y+.13,w:.8,h:.20,fontSize:10,color:C.ink,margin:0});
    s.addText(`Test ${m.final_test_auroc.toFixed(3)}`,{x:10.95,y:y+.13,w:1.0,h:.20,fontSize:10,color:C.muted,margin:0});
  });
  card(s,8.12,5.08,4.10,1.16,'Model choice','The project does not select a learner by final-test AUROC. Final-test values are reported only after development decisions are fixed.',{fill:C.sand,line:'E7D8BC',fontSize:9.6});
}

//9 final discrimination
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Final discrimination','Family-aware statistical models are competitive on unseen families','The final test contains 140 families and 67 incident events. Confidence intervals reflect resampling by family rather than by individual.');
  img(s,'final_test_auc_ci.png',.68,2.26,6.2,4.0);
  img(s,'roc_locked_test.png',7.05,2.26,5.55,4.0);
  const ft=R.final_test;
  s.addText(`Elastic Net ${ft.elastic_net.auroc.toFixed(3)}   Mixed ${ft.mixed_random_intercept.auroc.toFixed(3)}   GEE ${ft.family_gee.auroc.toFixed(3)}   CatBoost ${ft.catboost.auroc.toFixed(3)}`,
    {x:.85,y:6.40,w:11.5,h:.26,fontSize:10.8,bold:true,color:C.ink,margin:0,align:'center',fit:'shrink'});
}

//10 calibration sensitivity
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Calibration and robustness','Discrimination is only one part of the evaluation','Calibration is assessed on unseen families, and the fitted models are then stressed without re-tuning them.');
  img(s,'calibration_locked_test.png',.70,2.24,5.85,3.95);
  img(s,'sensitivity_auc.png',6.72,2.24,5.88,3.95);
  s.addText('Largest perturbation effect', {x:.85,y:6.33,w:1.8,h:.22,fontSize:9,bold:true,color:C.teal,margin:0});
  s.addText('Five percent outcome misclassification produces the clearest loss of AUROC and Brier performance in the current sensitivity set.', {x:2.55,y:6.28,w:9.5,h:.34,fontSize:10.8,color:C.ink,margin:0,fit:'shrink'});
}

//11 interactive tool
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Interactive family tool','The interface makes family structure and model choice tangible','A user can start from an example family or construct a new nuclear family, select a relative, edit baseline family history and vary the three PGS and clinical covariates.');
  s.addShape(pptx.ShapeType.roundRect,{x:.66,y:2.18,w:8.55,h:4.50,rectRadius:.04,fill:{color:C.paper},line:{color:C.line}});
  s.addImage({path:path.join(ROOT,'results/plots/website_tool.png'),x:.78,y:2.30,w:8.30,h:4.25});
  card(s,9.43,2.30,3.18,1.20,'1. Pedigree editing','Parents and children are linked explicitly. Children can be added or removed, and sex, age and baseline IBD status can be changed.',{fill:C.paper,fontSize:9.4});
  card(s,9.43,3.72,3.18,1.20,'2. Individual inputs','Selecting a relative loads that person’s PGS and clinical covariates. Family-history predictors are recalculated from the current pedigree.',{fill:C.tealSoft,line:'B7DEDA',fontSize:9.4});
  card(s,9.43,5.14,3.18,1.20,'3. Live model comparison','Elastic Net, the family mixed model and the boosted benchmark recompute immediately from the same edited inputs.',{fill:C.sand,line:'E7D8BC',fontSize:9.4});
}

//12 interpretation
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Interpretation','What the current experiment says, and what it does not','The strongest conclusion is methodological: family structure changes how the prediction problem should be formulated and validated.');
  card(s,.75,2.35,3.70,3.55,'1. Multiple PGS','Using three correlated IBD scores gives a small development-CV gain over one strong LDpred2 score. This supports shrinkage and incremental testing rather than naive score aggregation.',{fill:C.paper,fontSize:11});
  card(s,4.82,2.35,3.70,3.55,'2. Family-aware estimation','The mixed model, GEE and shared-frailty model perform similarly to Elastic Net on unseen families. Family structure matters for estimation even when the final AUROC is not dramatically higher.',{fill:C.tealSoft,line:'B7DEDA',fontSize:11});
  card(s,8.89,2.35,3.70,3.55,'3. ML remains a benchmark','CatBoost is the strongest boosted learner in development, but it does not surpass the statistical models on the locked family test. Non-linearity is therefore useful to test, not assume.',{fill:C.sand,line:'E7D8BC',fontSize:11});
  s.addText('The next scientific question is not simply how to raise AUROC. It is which sources of familial information improve calibrated risk prediction and remain transportable across families.',{x:1.0,y:6.20,w:11.15,h:.42,fontSize:12.1,bold:true,color:C.ink,align:'center',margin:0,fit:'shrink'});
}

//13 next steps
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Next steps','Move from a score-level demonstrator to cohort-grade statistical genetics','The present pipeline is designed so each extension answers a specific methodological question rather than merely adding features.');
  const items=[
    ['Genotype-level scoring','Download and harmonise the official PGS scoring files, simulate or use marker-level genotypes, and calculate PGS by vectorised genotype-weight multiplication.'],
    ['Kinship-aware GLMM','Construct a pedigree- or genotype-derived relationship matrix K and use it to model the random genetic covariance rather than a single family intercept.'],
    ['CD and UC subtypes','Separate disease-specific genetic effects and family-history structures instead of treating all IBD as one endpoint.'],
    ['Longitudinal covariates','Allow microbiome, proteomic and clinical measurements to vary over follow-up and examine time-dependent prediction.'],
    ['External calibration','Estimate transport and recalibration in an independent family cohort or a temporally separated cohort segment.']
  ];
  items.forEach((it,i)=>{
    const y=2.12+i*.78;
    s.addShape(pptx.ShapeType.ellipse,{x:.86,y:y+.07,w:.34,h:.34,fill:{color:C.teal},line:{color:C.teal}});
    s.addText(String(i+1),{x:.86,y:y+.13,w:.34,h:.16,fontSize:8.5,bold:true,color:'FFFFFF',align:'center',margin:0});
    s.addText(it[0],{x:1.36,y,w:2.15,h:.28,fontSize:11.2,bold:true,color:C.ink,margin:0});
    s.addText(it[1],{x:3.55,y,w:8.75,h:.48,fontSize:10.5,color:C.muted,margin:0,fit:'shrink'});
  });
  s.addText('Kinship-aware GLMM', {x:.88,y:6.02,w:1.5,h:.22,fontSize:9,bold:true,color:C.teal,margin:0});
  s.addImage({path:path.join(ROOT,'results/plots/eq_kinship.png'),x:2.22,y:5.84,w:3.20,h:.55});
  s.addText('K encodes pairwise genetic relatedness; the variance term scales the random genetic component. This is the planned replacement for a simple family random intercept.', {x:5.55,y:5.90,w:6.60,h:.42,fontSize:9.5,color:C.muted,margin:0,fit:'shrink'});
  s.addText('Working principle', {x:.88,y:6.48,w:1.3,h:.22,fontSize:9,bold:true,color:C.teal,margin:0});
  s.addText('Use family structure in the model and validation design, not merely as another binary covariate.', {x:2.15,y:6.42,w:8.35,h:.30,fontSize:11.2,bold:true,color:C.ink,margin:0,fit:'shrink'});
  s.addText('Live tool', {x:10.72,y:6.02,w:.75,h:.20,fontSize:8.5,bold:true,color:C.teal,margin:0,align:'center'});
  s.addImage({path:path.join(ROOT,'results/plots/live_qr.png'),x:10.72,y:6.20,w:.78,h:.78});
  s.addText('emmanuelludo.github.io/familyprs-lab', {x:11.58,y:6.39,w:1.05,h:.32,fontSize:6.8,color:C.muted,margin:0,fit:'shrink'});
}

};
