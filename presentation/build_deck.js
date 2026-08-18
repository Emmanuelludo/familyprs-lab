const ctx = require('./deck_context');
require('./slides_01_06')(ctx);
require('./slides_07_13')(ctx);

const out = ctx.path.join(ctx.ROOT, 'presentation/FamilyPRS_Lab_v6_QR_Interview_Presentation.pptx');
ctx.pptx.writeFile({ fileName: out });
