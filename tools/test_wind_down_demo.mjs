import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from '/Users/etdadmin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const url = 'http://127.0.0.1:8766/wind-down-demo.html';
const output = resolve('tmp/wind-down-qa');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });

for (const [width, height] of [[320,568],[375,812],[768,1024],[1024,768],[1440,900]]) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url, { waitUntil: 'networkidle' });

  const command = JSON.parse(await page.locator('#jsonView').textContent());
  const initial = await page.locator('#demoClock').textContent();
  if (initial !== command.schedule.wind_down_start) throw new Error(`${width}: scene did not start at command time (received ${initial})`);
  if (await page.locator('#jsonView').textContent() === 'Loading…') throw new Error('JSON command did not load');
  if (command.type !== 'room_command') throw new Error('Persisted room command is not displayed');

  const overflow = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
  if (overflow.scrollWidth !== overflow.clientWidth) throw new Error(`${width} overflow: ${JSON.stringify(overflow)}`);
  if (errors.length) throw new Error(`${width} console errors: ${errors.join('; ')}`);
  if (width === 375 || width === 1440) await page.screenshot({ path: `${output}/wind-down-${width}.png`, fullPage: true });
  await page.close();
}

const audio = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await audio.goto(url, { waitUntil: 'networkidle' });
if (await audio.locator('#soundState').getAttribute('data-signal') !== 'present') {
  if (await audio.locator('#unlock').isVisible()) await audio.locator('#unlock').click();
  else await audio.locator('body').click({ position: { x: 20, y: 200 } });
}
await audio.waitForFunction(() => document.querySelector('#soundState')?.dataset.signal === 'present', null, { timeout: 5000 });
if (await audio.locator('#soundStatus').textContent() !== 'Sound playing') throw new Error('Audio status never confirmed playback');
for (const profile of ['pink','brown','ocean','instrumental']) {
  await audio.locator('#profile').selectOption(profile);
  await audio.waitForFunction(() => document.querySelector('#soundState')?.dataset.signal === 'present');
}
await audio.locator('#profile').selectOption('silence');
await audio.waitForFunction(() => document.querySelector('#soundState')?.dataset.signal === 'absent');
await audio.locator('#profile').selectOption('instrumental');
await audio.waitForFunction(() => document.querySelector('#soundState')?.dataset.signal === 'present');
await audio.locator('#toggleSound').click();
await audio.waitForFunction(() => document.querySelector('#soundState')?.dataset.signal === 'absent');
await audio.close();
const zoomContext = await browser.newContext({ viewport: { width: 384, height: 450 }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
const zoomed = await zoomContext.newPage();
await zoomed.goto(url, { waitUntil: 'networkidle' });
const zoomLayout = await zoomed.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
if (zoomLayout.scrollWidth !== zoomLayout.clientWidth) throw new Error(`200% zoom overflow: ${JSON.stringify(zoomLayout)}`);
await zoomContext.close();
await browser.close();
console.log('Lamp demo passed live room-command load, dynamic animation start, five viewports, 200% zoom, and measured instrumental/pink/brown/ocean/silence audio checks.');
