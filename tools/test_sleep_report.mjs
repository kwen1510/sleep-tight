import { resolve } from 'node:path';
import { mkdir } from 'node:fs/promises';
import { chromium } from '/Users/etdadmin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const url = 'http://127.0.0.1:8766/sleep-report.html';
const output = resolve('tmp/sleep-report-qa');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });

for (const [width, height] of [[320,568],[375,812],[768,1024],[1024,768],[1440,900]]) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url, { waitUntil: 'load' });
  const layout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    overflow: [...document.querySelectorAll('body *')].filter(node => {
      const rect = node.getBoundingClientRect();
      return !node.closest('.tabs') && rect.right > document.documentElement.clientWidth + 1 && getComputedStyle(node).position !== 'absolute';
    }).slice(0,8).map(node => `${node.tagName}.${node.className}`),
  }));
  if (layout.scrollWidth !== layout.clientWidth || layout.overflow.length) throw new Error(`${width}x${height}: ${JSON.stringify(layout)}`);
  if (errors.length) throw new Error(`${width} console errors: ${errors.join('; ')}`);
  if (await page.locator('#headlineMetrics .card').count() !== 4) throw new Error('Missing headline metrics');
  if (await page.locator('#learningChart circle').count() !== 30) throw new Error('Learning chart does not contain 30 nights');

  for (const id of ['tab-overview','tab-replay','tab-similar','tab-forward']) {
    await page.locator(`#${id}`).click();
    if (await page.locator(`#${id}`).getAttribute('aria-selected') !== 'true') throw new Error(`${id} did not select`);
  }
  await page.locator('#tab-replay').click();
  await page.locator('#daySlider').fill('1');
  if (!(await page.locator('#knowledgeTitle').textContent()).startsWith('0 earlier')) throw new Error('Night 1 used personal history');
  await page.locator('#daySlider').fill('11');
  if (!(await page.locator('#knowledgeTitle').textContent()).startsWith('10 earlier')) throw new Error('Night 11 did not use exactly ten prior nights');
  if (!(await page.locator('#replaySubheading').textContent()).includes('Nights 1–10 only')) throw new Error('Night 11 boundary is not explicit');
  await page.locator('#daySlider').fill('30');
  if (!(await page.locator('#knowledgeTitle').textContent()).startsWith('29 earlier')) throw new Error('Night 30 boundary is incorrect');

  await page.locator('#tab-similar').click();
  if (await page.locator('.pair-button').count() < 6) throw new Error('Too few matched comparisons');
  await page.locator('.pair-button').nth(1).click();
  if (await page.locator('.pair-button').nth(1).getAttribute('aria-pressed') !== 'true') throw new Error('Matched pair did not select');
  await page.locator('#tab-forward').click();
  if (await page.locator('.plan-row').count() !== 10) throw new Error('Next-ten plan is incomplete');

  await page.locator('#tab-overview').click();
  await page.locator('#tab-overview').focus();
  await page.keyboard.press('ArrowRight');
  if (await page.locator('#tab-replay').getAttribute('aria-selected') !== 'true') throw new Error('Keyboard tab navigation failed');
  await page.locator('#tab-overview').click();
  if (width === 375 || width === 1440) await page.screenshot({ path: `${output}/report-${width}.png`, fullPage: true });
  if (width === 1440) {
    for (const [tab, name] of [['#tab-replay','replay'],['#tab-similar','similar'],['#tab-forward','forward']]) {
      await page.locator(tab).click();
      await page.screenshot({ path: `${output}/${name}-1440.png`, fullPage: true });
    }
  }
  await page.close();
}

const zoom = await browser.newPage({ viewport: { width: 384, height: 900 }, reducedMotion: 'reduce' });
await zoom.goto(url, { waitUntil: 'load' });
if (await zoom.evaluate(() => document.documentElement.scrollWidth !== document.documentElement.clientWidth)) throw new Error('200% reflow overflow');
await zoom.close();
await browser.close();
console.log('Sequential report passed daily replay, matched comparisons, next-ten plan, keyboard, console, five viewports, and 200% reflow checks.');
