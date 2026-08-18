module.exports = function buildSlides(ctx) {
  const { pptx, R, PGS, C, addTitle, card, source, arrow, metric, img, path, ROOT } = ctx;
// 1 Title
{
  const s = pptx.addSlide('MASTER');
  s.background = { color: 'F2F7F8' };
  s.addShape(pptx.ShapeType.roundRect, { x: 0.72, y: 0.92, w: 0.66, h: 0.66, rectRadius: 0.08, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText('FP', { x: 0.72, y: 1.10, w: 0.66, h: 0.22, fontSize: 16, bold: true, align: 'center', color: 'FFFFFF', margin: 0 });
  s.addText('Family-aware 10-year IBD risk prediction', { x: 0.75, y: 1.95, w: 7.5, h: 1.05, fontSize: 34, bold: true, color: C.ink, margin: 0, fit: 'shrink' });
  s.addText('Polygenic scores, pedigree information and clinical covariates in an IBD-enriched family cohort', { x: 0.77, y: 3.23, w: 7.3, h: 0.62, fontSize: 17, color: C.teal, margin: 0, fit: 'shrink' });
  card(s, 8.65, 1.65, 3.75, 3.25, 'Question', 'Can a population-derived polygenic signal be transported into families already enriched for IBD, and what changes when relatedness, ascertainment and time-to-event risk are modelled explicitly?', { fill: C.paper, fontSize: 13 });
  s.addText('Emmanuel Oludowole', { x: 0.77, y: 5.65, w: 3.1, h: 0.30, fontSize: 12, bold: true, color: C.ink, margin: 0 });
  s.addText('Interview research project', { x: 0.77, y: 6.02, w: 3.1, h: 0.24, fontSize: 10.2, color: C.muted, margin: 0 });
}

// 2 problem
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Scientific question','The prediction problem changes inside high-risk families','The model has to separate genetic burden, observed family history and residual familial dependence, then transport the result to an unseen family.');
  card(s,.72,2.45,3.55,3.20,'Population-derived PGS','Published PGS estimate common-variant burden from large discovery samples. Their relative ranking may transport better than their absolute risk calibration.',{fill:C.paper,fontSize:11.3});
  card(s,4.88,2.45,3.55,3.20,'Family ascertainment','Recruitment through an affected proband enriches the cohort for genetic and shared environmental risk. Relatives are correlated observations, not exchangeable individuals.',{fill:C.sand,line:'E7D8BC',fontSize:11.3});
  card(s,9.04,2.45,3.55,3.20,'Prospective target','The target is incident IBD over 10 years among relatives without IBD at baseline. This preserves the temporal order between family history and the outcome.',{fill:C.tealSoft,line:'B7DEDA',fontSize:11.3});
  arrow(s,4.28,4.05,4.78,4.05); arrow(s,8.44,4.05,8.94,4.05);
  s.addText('Primary estimand', {x:.82,y:5.95,w:1.3,h:.22,fontSize:9,bold:true,color:C.teal,margin:0});
  s.addText('P(incident IBD within 10 years | baseline-unaffected relative, family history, PGS, clinical covariates)', {x:2.05,y:5.9,w:10.1,h:.34,fontSize:12.1,bold:true,color:C.ink,margin:0,fit:'shrink'});
}

// 3 data basis and one provenance acknowledgement
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Data basis','Three public IBD polygenic scores with different construction methods','The scores are technically compatible but share discovery evidence, so they are treated as correlated predictors rather than independent evidence.');
  const rows=[
    ['PGS004105','P+T / clumping','139','GRCh38'],
    ['PGS003997','lassosum','8,406','GRCh38'],
    ['PGS004038','LDpred2.CV','1,018,068','GRCh38']
  ];
  s.addShape(pptx.ShapeType.roundRect,{x:.75,y:2.4,w:7.1,h:2.75,rectRadius:.04,fill:{color:C.paper},line:{color:C.line}});
  s.addText('Score',{x:1.0,y:2.67,w:1.35,h:.22,fontSize:9,bold:true,color:C.muted,margin:0});
  s.addText('Method',{x:2.55,y:2.67,w:1.8,h:.22,fontSize:9,bold:true,color:C.muted,margin:0});
  s.addText('Variants',{x:4.9,y:2.67,w:1.1,h:.22,fontSize:9,bold:true,color:C.muted,margin:0});
  s.addText('Build',{x:6.35,y:2.67,w:1.0,h:.22,fontSize:9,bold:true,color:C.muted,margin:0});
  rows.forEach((r,i)=>{
    const y=3.12+i*.61;
    s.addText(r[0],{x:1.0,y,w:1.35,h:.22,fontSize:11,bold:true,color:C.ink,margin:0});
    s.addText(r[1],{x:2.55,y,w:1.9,h:.22,fontSize:10.5,color:C.ink,margin:0});
    s.addText(r[2],{x:4.9,y,w:1.1,h:.22,fontSize:10.5,color:C.ink,margin:0});
    s.addText(r[3],{x:6.35,y,w:1.0,h:.22,fontSize:10.5,color:C.ink,margin:0});
  });
  card(s,8.25,2.4,4.35,1.30,'Compatibility check','All three scores use beta weights on GRCh38 and target IBD. The repository includes a downloader that validates PGS Catalog scoring-file columns and metadata before genotype-level use.',{fill:C.tealSoft,line:'B7DEDA',fontSize:9.6});
  card(s,8.25,3.95,4.35,1.55,'Provenance','Public PGS definitions and published performance metadata are real. Participant-level pedigrees, clinical covariates and outcomes in this project are simulated; no UKSH participant-level data are used.',{fill:C.sand,line:'E7D8BC',fontSize:9.6});
  s.addText('Why use more than one score?',{x:.85,y:5.60,w:2.2,h:.25,fontSize:10,bold:true,color:C.teal,margin:0});
  s.addText('Different regularisation and LD assumptions can capture partly different projections of the same underlying polygenic signal. Regularised stacking decides whether the extra summaries add information.',{x:3.05,y:5.53,w:9.2,h:.56,fontSize:11.2,color:C.ink,margin:0,fit:'shrink'});
  source(s,'PGS Catalog: PGS004105, PGS003997 and PGS004038; Monti et al., American Journal of Human Genetics, 2024.');
}

// 4 DGM
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Data-generating model','A hierarchical family process, followed by study ascertainment','The fitted models never see the latent genetic value or the true family frailty. Those remain part of the simulation truth.');
  const xs=[.75,3.0,5.25,7.5,9.75];
  const labels=['Founders','Offspring','Baseline IBD','Ascertainment','Prospective follow-up'];
  const bodies=[
    'Latent additive genetic value G and three method-specific heritable PGS components.',
    '0.5 father + 0.5 mother + segregation residual for genetic components.',
    'Genetic, clinical and shared-family terms generate baseline disease before recruitment.',
    'Retain families with at least one baseline IBD case; derive observed family history.',
    'Baseline-unaffected relatives receive event times and are censored at 10 years.'
  ];
  for(let i=0;i<xs.length;i++){
    card(s,xs[i],2.35,1.9,1.72,labels[i],bodies[i],{fill:i===3?C.sand:C.paper,fontSize:8.8,titleSize:10.4});
    if(i<xs.length-1) arrow(s,xs[i]+1.9,3.2,xs[i+1]-.08,3.2);
  }
  s.addShape(pptx.ShapeType.roundRect,{x:.8,y:4.52,w:5.75,h:1.55,rectRadius:.04,fill:{color:C.tealSoft},line:{color:'B7DEDA'}});
  s.addText('Polygenic measurement model',{x:1.0,y:4.72,w:2.6,h:.24,fontSize:11.2,bold:true,color:C.ink,margin:0});
  img(s,'eq_pgs.png',1.03,4.98,4.75,.42);
  s.addText('Each public score is a correlated, heritable measurement of the same latent polygenic component. Score-specific loadings are informed by published PGS evidence.',{x:1.0,y:5.45,w:5.15,h:.43,fontSize:9.2,color:C.muted,margin:0,fit:'shrink'});
  s.addShape(pptx.ShapeType.roundRect,{x:6.85,y:4.52,w:5.65,h:1.55,rectRadius:.04,fill:{color:C.paper},line:{color:C.line}});
  s.addText('Prospective family hazard',{x:7.05,y:4.72,w:2.6,h:.24,fontSize:11.2,bold:true,color:C.ink,margin:0});
  img(s,'eq_hazard.png',7.08,4.98,4.65,.42);
  s.addText('A shared gamma frailty induces residual dependence within families. Genetic, clinical and family-history effects enter the hazard through Xβ.',{x:7.05,y:5.45,w:5.05,h:.43,fontSize:9.2,color:C.muted,margin:0,fit:'shrink'});
}

//5 multi PGS
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Polygenic signal','Multiple PGS add a small amount of internal discrimination','The gain is deliberately interpreted as incremental signal, not as three independent replications of the same genetic association.');
  img(s,'multi_pgs_increment.png',.72,2.35,6.25,3.75);
  const inc=R.multi_pgs_incremental;
  metric(s,7.45,2.55,2.25,'LDpred2 + covariates',inc.ldpred2_plus_covariates_5fold_family_cv.mean_auroc.toFixed(3),'5-fold family CV AUROC');
  metric(s,9.95,2.55,2.25,'Three PGS + covariates',inc.three_pgs_plus_covariates_5fold_family_cv.mean_auroc.toFixed(3),'same covariate specification');
  card(s,7.45,3.90,4.75,1.60,'Interpretation',`Incremental AUROC: +${inc.delta_auroc.toFixed(3)}. The three scores were built from the same source GWAS, so a modest gain is more plausible than a large jump. Strong shrinkage controls collinearity.`,{fill:C.tealSoft,line:'B7DEDA',fontSize:10.8});
  s.addText('Practical implication',{x:7.6,y:5.78,w:1.5,h:.22,fontSize:9,bold:true,color:C.teal,margin:0});
  s.addText('Keep the multi-PGS block if it improves grouped development CV and calibration; otherwise prefer the most stable single score.',{x:9.05,y:5.73,w:3.2,h:.44,fontSize:10.8,color:C.ink,margin:0,fit:'shrink'});
}

// 6 models
{
  const s=pptx.addSlide('MASTER');
  addTitle(s,'Model set','Statistical models define the core analysis; boosting tests non-linearity','Every model is evaluated on the same prospective target and the same family-level holdout.');
  card(s,.72,2.35,2.75,3.65,'Elastic Net','Three PGS + clinical covariates + explicit family history. Shrinkage is useful because the genetic scores are correlated and the event count is modest.',{fill:C.paper,fontSize:10.8});
  card(s,3.65,2.35,2.75,3.65,'Mixed model / GEE','The GLMM adds a family random intercept; GEE gives a population-average clustered analysis. Both account for within-family dependence during estimation.',{fill:C.tealSoft,line:'B7DEDA',fontSize:10.8});
  card(s,6.58,2.35,2.75,3.65,'Shared frailty','A gamma family frailty enters the hazard multiplicatively. This uses event times rather than collapsing follow-up immediately to a binary label.',{fill:C.paper,fontSize:10.8});
  card(s,9.51,2.35,2.75,3.65,'AutoML benchmark','XGBoost, LightGBM and CatBoost are tuned with grouped family CV. CatBoost is strongest in development in the current run, but not dominant on final families.',{fill:C.sand,line:'E7D8BC',fontSize:10.8});
  s.addText('Genotype-level extension', {x:.85,y:6.25,w:1.8,h:.22,fontSize:9,bold:true,color:C.teal,margin:0});
  s.addText('Replace the family random intercept with a marker- or pedigree-derived kinship matrix K:  u ~ MVN(0, sigma_g^2 K).', {x:2.55,y:6.20,w:9.5,h:.30,fontSize:11.2,color:C.ink,margin:0,fit:'shrink'});
}

};
