function drawChart(svgId,type){
  const svg=$(svgId),legend=$(type==='roc'?'rocLegend':'calLegend');
  svg.innerHTML=''; if(legend)legend.innerHTML='';
  const W=560,H=360,L=58,R=18,T=24,B=48;
  const defs=[
    {key:'elastic_net',label:'Elastic Net',color:'#0072B2'},
    {key:'mixed_random_intercept',label:'Mixed model',color:'#D55E00'},
    {key:'family_gee',label:'Family GEE',color:'#009E73'},
    {key:D.results.best_ml_model,label:prettyModel(D.results.best_ml_model),color:'#CC79A7'}
  ].filter((d,i,a)=>D.results.curves[d.key]&&a.findIndex(x=>x.key===d.key)===i);
  let axisMax=1;
  if(type!=='roc'){
    const vals=[];
    defs.forEach(d=>{const c=D.results.curves[d.key][type]; vals.push(...c.pred,...c.obs);});
    const observed=Math.max(...vals.filter(Number.isFinite),0.2);
    axisMax=Math.min(1,Math.max(0.25,Math.ceil((observed+0.025)*20)/20));
  }
  const x=v=>L+(v/axisMax)*(W-L-R), y=v=>H-B-(v/axisMax)*(H-T-B);
  for(let i=0;i<=5;i++){
    const q=axisMax*i/5;
    svg.appendChild(svgEl('line',{x1:x(q),y1:y(0),x2:x(q),y2:y(axisMax),class:'chart-grid'}));
    svg.appendChild(svgEl('line',{x1:x(0),y1:y(q),x2:x(axisMax),y2:y(q),class:'chart-grid'}));
    const digits=axisMax<=.5?2:1;
    let tx=svgEl('text',{x:x(q),y:H-18,'text-anchor':'middle',class:'chart-text'});tx.textContent=q.toFixed(digits);svg.appendChild(tx);
    let ty=svgEl('text',{x:46,y:y(q)+4,'text-anchor':'end',class:'chart-text'});ty.textContent=q.toFixed(digits);svg.appendChild(ty);
  }
  svg.appendChild(svgEl('line',{x1:x(0),y1:y(0),x2:x(axisMax),y2:y(axisMax),class:'chart-ref'}));
  const lineEls=new Map(), hitEls=new Map(), buttons=new Map();
  function applyHighlight(key){
    const pinned=chartState[type];
    const active=key||pinned;
    defs.forEach(d=>{
      const line=lineEls.get(d.key),btn=buttons.get(d.key);
      line.classList.toggle('chart-curve-active',!!active&&d.key===active);
      line.classList.toggle('chart-curve-muted',!!active&&d.key!==active);
      if(btn){btn.classList.toggle('active',!!active&&d.key===active);btn.classList.toggle('muted',!!active&&d.key!==active);btn.setAttribute('aria-pressed',pinned===d.key?'true':'false');}
      const hit=hitEls.get(d.key); if(hit)hit.style.pointerEvents='stroke';
    });
  }
  function pin(key){chartState[type]=chartState[type]===key?null:key;applyHighlight(chartState[type]);}
  defs.forEach(d=>{
    const c=D.results.curves[d.key][type],xs=type==='roc'?c.fpr:c.pred,ys=type==='roc'?c.tpr:c.obs;
    const pts=xs.map((v,i)=>`${x(Math.min(axisMax,Math.max(0,v)))},${y(Math.min(axisMax,Math.max(0,ys[i])))}`).join(' ');
    const line=svgEl('polyline',{points:pts,fill:'none',stroke:d.color,'stroke-width':'2.8',class:'chart-curve','data-model':d.key,'stroke-linejoin':'round','stroke-linecap':'round'});
    const title=svgEl('title'); title.textContent=`${d.label}${type==='roc'?` · AUROC ${D.results.final_test[d.key].auroc.toFixed(3)}`:''}`; line.appendChild(title); svg.appendChild(line); lineEls.set(d.key,line);
    const hit=svgEl('polyline',{points:pts,fill:'none',stroke:'transparent','stroke-width':'16',class:'chart-hit','data-model':d.key});
    hit.addEventListener('mouseenter',()=>{if(!chartState[type])applyHighlight(d.key);});
    hit.addEventListener('mouseleave',()=>{if(!chartState[type])applyHighlight(null);});
    hit.addEventListener('click',e=>{e.preventDefault();pin(d.key);});
    svg.appendChild(hit); hitEls.set(d.key,hit);
    if(legend){
      const btn=document.createElement('button');btn.type='button';btn.className='chart-legend-item';btn.setAttribute('aria-pressed','false');btn.dataset.model=d.key;
      const auc=type==='roc'?`<span class="legend-metric">AUROC ${D.results.final_test[d.key].auroc.toFixed(3)}</span>`:'';
      btn.innerHTML=`<span class="legend-swatch" style="background:${d.color}"></span><span>${d.label}</span>${auc}`;
      btn.addEventListener('mouseenter',()=>{if(!chartState[type])applyHighlight(d.key);});
      btn.addEventListener('mouseleave',()=>{if(!chartState[type])applyHighlight(null);});
      btn.addEventListener('click',()=>pin(d.key));
      legend.appendChild(btn);buttons.set(d.key,btn);
    }
  });
  const xl=svgEl('text',{x:(L+W-R)/2,y:H-3,'text-anchor':'middle',class:'chart-text'});xl.textContent=type==='roc'?'1 - specificity':'Predicted probability';svg.appendChild(xl);
  const yl=svgEl('text',{x:14,y:(T+H-B)/2,transform:`rotate(-90 14 ${(T+H-B)/2})`,'text-anchor':'middle',class:'chart-text'});yl.textContent=type==='roc'?'Sensitivity':'Observed proportion';svg.appendChild(yl);
  applyHighlight(chartState[type]);
}