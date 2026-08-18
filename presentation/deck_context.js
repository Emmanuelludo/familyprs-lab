const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const R = JSON.parse(fs.readFileSync(path.join(ROOT, 'results/model_results.json'), 'utf8'));
const PGS = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/public/pgs_catalog_metadata.json'), 'utf8'));

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Emmanuel Oludowole';
pptx.subject = 'Family-aware 10-year IBD risk prediction';
pptx.title = 'Family-aware 10-year IBD risk prediction';
pptx.company = 'Interview preparation';
pptx.lang = 'en-US';
pptx.theme = { headFontFace: 'Aptos Display', bodyFontFace: 'Aptos', lang: 'en-US' };

const C = {
  navy: '123451', ink: '17283C', teal: '1F7A7A', tealSoft: 'EAF6F5',
  paper: 'FFFFFF', bg: 'F7F9FB', line: 'D8E1E8', muted: '64748B',
  sand: 'F6F0E4', amber: 'A86A16', rose: 'F9ECEC', green: '2C7A63'
};

pptx.defineSlideMaster({
  title: 'MASTER',
  background: { color: C.bg },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.12, fill: { color: C.navy }, line: { color: C.navy } } },
    { text: { text: 'FamilyPRS Lab', options: { x: 0.58, y: 0.24, w: 2.0, h: 0.28, fontSize: 9.5, bold: true, color: C.navy, margin: 0 } } },
    { line: { x: 0.58, y: 7.12, w: 12.15, h: 0, line: { color: C.line, width: 0.9 } } },
  ],
  slideNumber: { x: 12.72, y: 7.18, w: 0.25, h: 0.18, color: C.muted, fontSize: 7.5, margin: 0 }
});

function addTitle(slide, kicker, heading, sub='') {
  slide.addText(kicker.toUpperCase(), { x: 0.65, y: 0.72, w: 3.8, h: 0.25, fontSize: 9.2, bold: true, color: C.teal, charSpacing: 1.2, margin: 0 });
  slide.addText(heading, { x: 0.65, y: 1.02, w: 12.0, h: 0.58, fontSize: 25.5, bold: true, color: C.ink, margin: 0, fit: 'shrink' });
  if (sub) slide.addText(sub, { x: 0.65, y: 1.66, w: 11.95, h: 0.48, fontSize: 12.5, color: C.muted, margin: 0, fit: 'shrink' });
}
function card(slide, x, y, w, h, title, body, opt={}) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.05, fill: { color: opt.fill || C.paper }, line: { color: opt.line || C.line, width: 1 } });
  if (title) slide.addText(title, { x: x+0.18, y: y+0.15, w: w-0.36, h: 0.28, fontSize: opt.titleSize || 11.5, bold: true, color: opt.titleColor || C.ink, margin: 0, fit: 'shrink' });
  if (body) slide.addText(body, { x: x+0.18, y: y+0.50, w: w-0.36, h: h-0.62, fontSize: opt.fontSize || 10.5, color: opt.bodyColor || C.muted, margin: 0.01, breakLine: false, valign: 'top', fit: 'shrink' });
}
function source(slide, text) {
  slide.addText(text, { x: 0.66, y: 6.86, w: 11.7, h: 0.18, fontSize: 6.7, color: '8190A0', italic: true, margin: 0, fit: 'shrink' });
}
function arrow(slide, x1, y1, x2, y2) {
  slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2-x1, h: y2-y1, line: { color: C.teal, width: 1.8, endArrowType: 'triangle' } });
}
function metric(slide, x, y, w, label, value, note='') {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 1.0, rectRadius: 0.05, fill: { color: C.paper }, line: { color: C.line } });
  slide.addText(label, { x: x+0.14, y: y+0.13, w: w-0.28, h: 0.19, fontSize: 8.2, bold: true, color: C.muted, margin: 0 });
  slide.addText(value, { x: x+0.14, y: y+0.37, w: w-0.28, h: 0.30, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  if (note) slide.addText(note, { x: x+0.14, y: y+0.72, w: w-0.28, h: 0.16, fontSize: 7.5, color: C.muted, margin: 0, fit: 'shrink' });
}
function img(slide, file, x, y, w, h) {
  slide.addImage({ path: path.join(ROOT, 'results/plots', file), x, y, w, h });
}
function bulletText(items) {
  const runs=[];
  items.forEach((t)=>{ runs.push({ text:t, options:{ bullet:{indent:14}, breakLine:true } }); });
  return runs;
}

module.exports = { pptx, fs, path, ROOT, R, PGS, C, addTitle, card, source, arrow, metric, img, bulletText };
