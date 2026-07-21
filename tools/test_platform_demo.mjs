import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { mkdir } from 'node:fs/promises';
import { chromium } from '/Users/etdadmin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';

const url = pathToFileURL(resolve('computer/platform-demo.html')).href;
const output = resolve('tmp/platform-demo-qa');
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
      const deliberate = node.closest('.night-table-wrap');
      return !deliberate && rect.right > document.documentElement.clientWidth + 1 && getComputedStyle(node).position !== 'absolute';
    }).slice(0,8).map(node => `${node.tagName}.${node.className}`),
  }));
  if (layout.scrollWidth !== layout.clientWidth || layout.overflow.length) throw new Error(`${width}x${height}: ${JSON.stringify(layout)}`);
  if (errors.length) throw new Error(`${width}x${height} console errors: ${errors.join('; ')}`);

  await page.locator('#roomTime').fill('1365');
  if (await page.locator('#roomState').textContent() !== 'Lights out') throw new Error('Room plan did not reach lights out');
  if (await page.locator('#roomLight').textContent() !== '0%') throw new Error('Light did not reach 0%');
  await page.locator('#roomSoundSelect').selectOption('brown');
  if (!(await page.locator('#commandText').textContent()).includes('Brown')) throw new Error('Sound command did not update');
  await page.locator('.details summary').click();
  if (await page.locator('#nightRows tr').count() !== 30) throw new Error('Monthly table does not contain 30 nights');
  if (width === 375 || width === 1440) await page.screenshot({ path: `${output}/platform-${width}.png`, fullPage: true });
  await page.close();
}

const interaction = await browser.newPage({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
await interaction.goto(url, { waitUntil: 'load' });
await interaction.locator('#replay').click();
await interaction.waitForTimeout(3700);
if (!(await interaction.locator('#logState').textContent()).includes('PLAN READY')) throw new Error('Automation replay did not finish');
await interaction.close();
await browser.close();
console.log('Platform demo passed automation, room controls, 30-night data, console, overflow, and five-viewport checks.');
