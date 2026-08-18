'use strict';
const D=window.FAMILYPRS_DATA;
const $=id=>document.getElementById(id);
const SVG='http://www.w3.org/2000/svg';
const XGB=D.xgb||D.xgboost;
const LGB=D.lgbm||D.lightgbm;
let familyIndex=0, selectedId=null, model='elastic', customCounter=1;
const chartState={roc:null,calibration:null};
const original=JSON.parse(JSON.stringify(D.families));
const sigmoid=x=>1/(1+Math.exp(-x));
const logit=p=>Math.log(p/(1-p));
function erfInv(x){const a=.147,s=x<0?-1:1,l=Math.log(1-x*x);return s*Math.sqrt(Math.sqrt((2/(Math.PI*a)+l/2)**2-l/a)-(2/(Math.PI*a)+l/2));}
function zFromPercentile(p){const q=Math.min(.999,Math.max(.001,p/100));return Math.SQRT2*erfInv(2*q-1);}
function percentileFromZ(z){return 100*(.5*(1+erf(z/Math.SQRT2)));}
function erf(x){const sign=x<0?-1:1; x=Math.abs(x); const a1=.254829592,a2=-.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=.3275911; const t=1/(1+p*x); const y=1-(((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*Math.exp(-x*x); return sign*y;}
function currentFamily(){return D.families[familyIndex];}
function member(){return currentFamily().members.find(m=>m.member_id===selectedId);}
function isChild(m){return /^child\d+$/.test(m.role);}
function roleLabel(role){if(role==='father')return 'Father'; if(role==='mother')return 'Mother'; const n=role.match(/child(\d+)/); return n?`Child ${n[1]}`:role;}
function ensurePgs(m){if(!m.pgs)m.pgs={}; const ids=['PGS004105','PGS003997','PGS004038']; ids.forEach(id=>{if(!m.pgs[id])m.pgs[id]={z:0,percentile:50};});}
function geneticFDRs(sel){const fam=currentFamily().members;if(isChild(sel))return fam.filter(m=>m.member_id!==sel.member_id&&(m.role==='father'||m.role==='mother'||isChild(m)));return fam.filter(m=>isChild(m));}
function derived(sel){const aff=geneticFDRs(sel).filter(m=>m.baseline_ibd===1);return{n_affected_fdr:aff.length,affected_parent:isChild(sel)&&aff.some(m=>m.role==='father'||m.role==='mother')?1:0,affected_sibling:isChild(sel)&&aff.some(m=>isChild(m))?1:0,min_relative_onset_age:aff.length?Math.min(...aff.map(m=>m.age_at_onset??60)):60,multi_fdr_2plus:aff.length>=2?1:0,multi_fdr_3plus:aff.length>=3?1:0};}
function featureRow(){const m=member(),fh=derived(m);return{pgs_pt_z:zFromPercentile(+$('pgsPt').value),pgs_lassosum_z:zFromPercentile(+$('pgsLasso').value),pgs_ldpred2_z:zFromPercentile(+$('pgsLd').value),age:+$('age').value,sex_female:$('sex').value==='F'?1:0,current_smoker:$('smoker').checked?1:0,bmi:+$('bmi').value,antibiotics_12m:$('antibiotics').checked?1:0,...fh};}
function predElastic(r){const a=D.elastic;let raw=a.intercept;for(let i=0;i<a.features.length;i++)raw+=((r[a.features[i]]-a.mean[i])/a.scale[i])*a.coef[i];return sigmoid(a.calibration_intercept+a.calibration_coef*raw);}
function evalXGB(node,r){if(Object.prototype.hasOwnProperty.call(node,'leaf'))return +node.leaf;const val=r[node.split];const next=(val===undefined||Number.isNaN(val))?node.missing:(val<node.split_condition?node.yes:node.no);return evalXGB(node.children.find(c=>c.nodeid===next),r);}
function predXGB(r){if(!XGB)throw new Error('XGBoost browser artifact is missing.');let margin=logit(XGB.base_score);for(const t of XGB.trees)margin+=evalXGB(t,r);return sigmoid(XGB.calibration_intercept+XGB.calibration_coef*margin);}
function evalLGB(node,r,features){if(Object.prototype.hasOwnProperty.call(node,'leaf_value'))return +node.leaf_value;const val=r[features[node.split_feature]];const left=(val===undefined||Number.isNaN(val))?!!node.default_left:(val<=+node.threshold);return evalLGB(left?node.left_child:node.right_child,r,features);}
function predLGB(r){if(!LGB)throw new Error('LightGBM browser artifact is missing.');let raw=0;for(const t of LGB.dump.tree_info)raw+=evalLGB(t.tree_structure,r,LGB.features);return sigmoid(LGB.calibration_intercept+LGB.calibration_coef*raw);}
function predML(r){return D.interactive_ml_model==='lightgbm'?predLGB(r):predXGB(r);}
function predMixed(r){const a=D.mixed;let raw=a.intercept;for(let i=0;i<a.features.length;i++)raw+=a.coef[i]*r[a.features[i]];return sigmoid(a.calibration_intercept+a.calibration_coef*raw);}
const labelMap={pgs_pt_z:'P+T PGS',pgs_lassosum_z:'lassosum PGS',pgs_ldpred2_z:'LDpred2 PGS',age:'Age',sex_female:'Sex',current_smoker:'Current smoking',bmi:'BMI',antibiotics_12m:'Recent antibiotics',n_affected_fdr:'Affected FDRs',affected_parent:'Affected parent',affected_sibling:'Affected sibling',min_relative_onset_age:'Youngest onset',multi_fdr_2plus:'≥2 affected FDRs',multi_fdr_3plus:'≥3 affected FDRs'};
function localLinearDrivers(art,r,scaled=false){return art.features.map((f,i)=>({f,val:(scaled?((r[f]-art.mean[i])/art.scale[i]):r[f])*art.coef[i]})).sort((a,b)=>Math.abs(b.val)-Math.abs(a.val)).slice(0,6);}
function splitCounts(){const counts={};if(D.interactive_ml_model==='xgboost'&&XGB){const walk=n=>{if(n.leaf!==undefined)return;counts[n.split]=(counts[n.split]||0)+1;n.children.forEach(walk);};XGB.trees.forEach(walk);}else if(LGB){const feats=LGB.features;const walk=n=>{if(n.leaf_value!==undefined)return;const f=feats[n.split_feature];counts[f]=(counts[f]||0)+1;walk(n.left_child);walk(n.right_child);};LGB.dump.tree_info.forEach(t=>walk(t.tree_structure));}return Object.entries(counts).map(([f,val])=>({f,val})).sort((a,b)=>b.val-a.val);}
function renderDrivers(){const r=featureRow(),box=$('drivers');box.innerHTML='';let rows;if(model==='elastic')rows=localLinearDrivers(D.elastic,r,true);else if(model==='mixed')rows=localLinearDrivers(D.mixed,r,false);else rows=splitCounts().slice(0,6);const max=Math.max(...rows.map(x=>Math.abs(x.val)),1e-8);for(const x of rows){const d=document.createElement('div');d.className='driver';d.innerHTML=`<span>${labelMap[x.f]||x.f}</span><div class="driver-bar"><i class="${x.val>=0?'pos':'neg'}" style="width:${Math.max(3,100*Math.abs(x.val)/max)}%"></i></div><b>${model==='ml'?Math.round(x.val):(x.val>=0?'+':'')+x.val.toFixed(2)}</b>`;box.appendChild(d);}}