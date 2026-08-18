import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const pageErrors = [];
const consoleErrors = [];
page.on('pageerror', err => pageErrors.push(err.message));
page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

try {
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });

  await page.waitForFunction(() => {
    const select = document.querySelector('#familySelect');
    const risk = document.querySelector('#riskPct');
    return select && select.options.length > 0 && risk && risk.textContent.trim() !== '—';
  }, { timeout: 15000 });

  const initialFamilies = await page.locator('#familySelect option').count();
  if (initialFamilies < 1) throw new Error('Family selector was not populated');

  const initialRisk = (await page.textContent('#riskPct'))?.trim();
  if (!initialRisk || initialRisk === '—') throw new Error('Initial risk was not rendered');

  await page.click('[data-tab="compare"]');
  if (!(await page.locator('#compare').evaluate(el => el.classList.contains('active')))) {
    throw new Error('Models tab did not activate');
  }

  await page.click('[data-tab="tool"]');
  await page.click('#newFamilyBtn');
  const afterNewFamily = await page.locator('#familySelect option').count();
  if (afterNewFamily <= initialFamilies) throw new Error('New family action did not add a family');

  const slider = page.locator('#pgsLd');
  const beforeSliderRisk = (await page.textContent('#riskPct'))?.trim();
  await slider.evaluate(el => { el.value = '95'; el.dispatchEvent(new Event('input', { bubbles: true })); });
  await page.waitForTimeout(100);
  const afterSliderRisk = (await page.textContent('#riskPct'))?.trim();
  if (!afterSliderRisk || afterSliderRisk === '—') throw new Error('Risk disappeared after PGS input change');
  if (afterSliderRisk === beforeSliderRisk) throw new Error('PGS input change did not update risk');

  await page.click('[data-model="mixed"]');
  if (!(await page.locator('[data-model="mixed"]').evaluate(el => el.classList.contains('active')))) {
    throw new Error('Mixed-model switch did not activate');
  }

  await page.click('[data-tab="validation"]');
  if ((await page.locator('#rocLegend .chart-legend-item').count()) < 3) {
    throw new Error('ROC legend did not render');
  }
  if ((await page.locator('#calLegend .chart-legend-item').count()) < 3) {
    throw new Error('Calibration legend did not render');
  }

  if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);
  if (consoleErrors.length) throw new Error(`Console errors: ${consoleErrors.join(' | ')}`);

  console.log('FamilyPRS browser smoke test passed');
} finally {
  await browser.close();
}
