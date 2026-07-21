import { chromium } from '/Users/etdadmin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const url = 'http://127.0.0.1:8766/dashboard.html';
const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });

for (const [width, height] of [[320,568],[375,812],[768,1024],[1024,768],[1440,900]]) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.querySelector('#phoneBadge')?.textContent !== 'Checking');
  const layout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    buttonHeight: document.querySelector('#run').getBoundingClientRect().height,
  }));
  if (layout.scrollWidth !== layout.clientWidth) throw new Error(`${width} overflow: ${JSON.stringify(layout)}`);
  if (layout.buttonHeight < 44) throw new Error(`${width}: primary touch target is too small`);
  await page.keyboard.press('Tab');
  if (!(await page.evaluate(() => document.activeElement?.matches('a,button')))) throw new Error(`${width}: keyboard focus did not reach a control`);
  if (errors.length) throw new Error(`${width}: ${errors.join('; ')}`);
  await page.close();
}

const interaction = await browser.newPage({ viewport: { width: 900, height: 760 } });
await interaction.route('**/api/v1/evening/run', route => route.fulfill({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ run_id: 'browser-test', scene_url: '/wind-down-demo.html?run_id=browser-test' }),
}));
await interaction.goto(url, { waitUntil: 'networkidle' });
await interaction.locator('#run').click();
await interaction.waitForURL('**/wind-down-demo.html?run_id=browser-test');
await interaction.close();
const zoomContext = await browser.newContext({ viewport: { width: 384, height: 450 }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
const zoomed = await zoomContext.newPage();
await zoomed.goto(url, { waitUntil: 'networkidle' });
const zoomLayout = await zoomed.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
if (zoomLayout.scrollWidth !== zoomLayout.clientWidth) throw new Error(`200% zoom overflow: ${JSON.stringify(zoomLayout)}`);
await zoomContext.close();
await browser.close();
console.log('Evening dashboard passed five responsive sizes, 200% zoom, keyboard focus, source states, touch sizing, and scene handoff.');
