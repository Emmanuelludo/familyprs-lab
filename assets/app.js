(()=>{
  const parts=['app_01.js','app_02.js','app_03.js','app_04.js','app_05.js','app_06.js'];
  let i=0;
  function loadNext(){
    if(i>=parts.length)return;
    const s=document.createElement('script');
    s.src=new URL(parts[i++],document.currentScript.src).href;
    s.async=false;
    s.onload=loadNext;
    s.onerror=()=>console.error('Failed to load FamilyPRS application module:',s.src);
    document.head.appendChild(s);
  }
  loadNext();
})();
