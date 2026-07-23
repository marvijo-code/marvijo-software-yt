// node grade_r4.mjs <url>  - functional checks for the departures board
import { createRequire } from 'module';
const require = createRequire('C:/dev/ai-tools/agent-skills/web-screenshot/shot.mjs');
const { chromium } = require('playwright-core');

const url = process.argv[2];
const checks = [];
const check = (name, ok, detail = '') =>
  checks.push({ name, ok }) && console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ' - ' + detail : ''}`);

const browser = await chromium.launch({ channel: 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
const errors = [];
page.on('pageerror', e => errors.push(String(e)));
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

const rows = () => page.$$eval('#board tbody tr', trs => trs.map(t => t.getAttribute('data-flight')));
const countText = () => page.$eval('#count', el => el.textContent.trim());

try {
  const ths = await page.$$eval('th[data-key]', els => els.map(e => e.getAttribute('data-key')));
  check('5 data-key headers', ths.length === 5, ths.join(','));

  const r0 = await rows();
  check('initial 12 rows time-asc', r0.length === 12 && r0[0] === 'CS101' && r0[11] === 'CS309', r0.join(','));
  check('initial count "12 flights"', (await countText()) === '12 flights', await countText());

  await page.click('th[data-key="flight"]');
  await page.waitForTimeout(300);
  let r = await rows();
  const ariaAsc = await page.$eval('th[data-key="flight"]', el => el.getAttribute('aria-sort'));
  const others = await page.$$eval('th[data-key]:not([data-key="flight"])', els => els.map(e => e.getAttribute('aria-sort')).filter(Boolean));
  check('sort flight asc + aria-sort', r[0] === 'CS101' && r[11] === 'ZA915' && ariaAsc === 'ascending' && others.length === 0, `first=${r[0]} last=${r[11]} aria=${ariaAsc} others=${others}`);

  await page.click('th[data-key="flight"]');
  await page.waitForTimeout(300);
  r = await rows();
  const ariaDesc = await page.$eval('th[data-key="flight"]', el => el.getAttribute('aria-sort'));
  check('re-click reverses + aria descending', r[0] === 'ZA915' && ariaDesc === 'descending', `first=${r[0]} aria=${ariaDesc}`);

  await page.fill('#filter', 'cape');
  await page.waitForTimeout(300);
  r = await rows();
  check('filter "cape" -> 2 rows, "2 flights"', r.length === 2 && (await countText()) === '2 flights', `${r.join(',')} / ${await countText()}`);

  await page.fill('#filter', 'mn0');
  await page.waitForTimeout(300);
  r = await rows();
  check('filter "mn0" -> 1 row, singular "1 flight"', r.length === 1 && r[0] === 'MN088' && (await countText()) === '1 flight', `${r.join(',')} / ${await countText()}`);

  await page.fill('#filter', '');
  await page.waitForTimeout(300);
  check('clear filter -> 12 rows', (await rows()).length === 12);

  const chipColors = await page.$$eval('#board tbody .chip', els => {
    const m = {};
    for (const el of els) m[el.getAttribute('data-status')] = getComputedStyle(el).backgroundColor + '|' + getComputedStyle(el).color;
    return m;
  });
  const statuses = Object.keys(chipColors);
  const distinct = new Set(Object.values(chipColors));
  check('4 status chips, distinct colors', statuses.length === 4 && distinct.size === 4, JSON.stringify(chipColors));

  const scrollW = await page.evaluate(() => document.documentElement.scrollWidth <= 1200);
  check('no horizontal scroll @1200px', scrollW);
} catch (e) {
  console.log('GRADER EXC: ' + e.message);
}
check('no page JS errors', errors.length === 0, errors.join('; '));
const passed = checks.filter(c => c.ok).length;
console.log(`SCORE ${passed}/${checks.length}`);
await browser.close();
