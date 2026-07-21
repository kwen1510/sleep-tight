import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { mkdir } from 'node:fs/promises';
import { chromium } from '/Users/etdadmin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const url = pathToFileURL(resolve('research/dashboard.html')).href;
const screenshotDir = resolve('tmp/dashboard-qa');
await mkdir(screenshotDir, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
});

const sizes = [
  [320, 568], [375, 812], [768, 1024], [1024, 768], [1440, 900],
];

for (const [width, height] of sizes) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
  const errors = [];
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url, { waitUntil: 'load' });

  const layout = await page.evaluate(() => {
    const root = document.documentElement;
    const overflow = [...document.querySelectorAll('body *')].filter(element => {
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      const deliberateScrollRegion = element.closest('.signal-scroll');
      const visuallyHiddenHeader = element.closest('.ranking-table thead');
      return rect.right > root.clientWidth + 1 && style.position !== 'fixed' && !deliberateScrollRegion && !visuallyHiddenHeader;
    }).slice(0, 8).map(element => `${element.tagName}.${element.className}`);
    return { scrollWidth: root.scrollWidth, clientWidth: root.clientWidth, overflow };
  });
  if (layout.scrollWidth !== layout.clientWidth || layout.overflow.length) {
    throw new Error(`${width}x${height} overflow: ${JSON.stringify(layout)}`);
  }
  if (errors.length) throw new Error(`${width}x${height} console errors: ${errors.join('; ')}`);

  await page.selectOption('#verdictFilter', 'avoid');
  if (await page.locator('#rankingBody tr').count() !== 2) throw new Error('Avoid filter must show two techniques');
  await page.fill('#search', 'no matching technique');
  if (!(await page.locator('#emptyState').evaluate(node => node.classList.contains('visible')))) throw new Error('Empty state did not appear');
  await page.fill('#search', '');
  await page.selectOption('#verdictFilter', 'all');
  if (await page.locator('#rankingBody tr').count() !== 10) throw new Error('Reset filters must show ten techniques');

  await page.keyboard.press('Tab');
  const focused = await page.evaluate(() => document.activeElement?.tagName);
  if (!focused || focused === 'BODY') throw new Error('Keyboard focus did not enter the page');

  if (width === 375 || width === 1440) {
    await page.screenshot({ path: `${screenshotDir}/dashboard-${width}.png`, fullPage: true });
  }
  await page.close();
}

// A 384 CSS-pixel viewport is the reflow width of a 768-pixel window at 200% browser zoom.
const zoomPage = await browser.newPage({ viewport: { width: 384, height: 900 } });
await zoomPage.goto(url, { waitUntil: 'load' });
const zoomOverflow = await zoomPage.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
if (zoomOverflow) throw new Error('Page-level overflow at 200% zoom');
await zoomPage.close();

await browser.close();
console.log('Dashboard checks passed at 320, 375, 768, 1024, 1440 CSS px and 200% zoom.');
