#!/usr/bin/env node
/**
 * Load every page in a real browser and fail on anything a static grep misses:
 * CSP violations, JS errors, missing or duplicated h1, horizontal overflow.
 *
 *   node check-browser.mjs http://localhost:4321 / /about /contact
 *
 * Serve the built output with the production headers before running this --
 * a CSP violation only appears when the CSP is actually sent.
 */
import { chromium } from 'playwright';

const [base, ...paths] = process.argv.slice(2);
if (!base) {
  console.error('usage: node check-browser.mjs <base-url> [path ...]');
  process.exit(2);
}
const routes = paths.length ? paths : ['/'];

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
});
let failed = 0;

for (const path of routes) {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const problems = [];
  page.on('console', (m) => {
    if (m.type() === 'error') problems.push('console: ' + m.text().slice(0, 140));
  });
  page.on('pageerror', (e) => problems.push('pageerror: ' + String(e).slice(0, 140)));

  await page.goto(base + path, { waitUntil: 'networkidle' });

  const info = await page.evaluate(() => ({
    h1: document.querySelectorAll('h1').length,
    h1text: document.querySelector('h1')?.innerText.replace(/\s+/g, ' ').trim() ?? '',
    scrollW: document.documentElement.scrollWidth,
    clientW: document.documentElement.clientWidth,
  }));

  const overflow = info.scrollW > info.clientW + 1;
  const bad = problems.length || info.h1 !== 1 || overflow;
  if (bad) failed++;

  console.log(
    `${path.padEnd(22)} h1=${info.h1}${overflow ? ' H-OVERFLOW' : ''} ` +
    `${problems.length ? 'ERRORS(' + problems.length + ')' : 'clean'}  "${info.h1text.slice(0, 44)}"`
  );
  problems.slice(0, 4).forEach((p) => console.log('      ! ' + p));
  await ctx.close();
}

await browser.close();
console.log(failed ? `\n${failed} page(s) with problems` : '\nAll pages clean');
process.exit(failed ? 1 : 0);
