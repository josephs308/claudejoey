#!/usr/bin/env node
/**
 * Lighthouse scores per page, plus the specific accessibility/SEO audits that
 * failed -- the score alone does not tell you what to fix.
 *
 *   node lighthouse.mjs http://localhost:4321/ http://localhost:4321/about
 */
import lighthouse from 'lighthouse';
import { launch } from 'chrome-launcher';

const urls = process.argv.slice(2);
if (!urls.length) {
  console.error('usage: node lighthouse.mjs <url> [url ...]');
  process.exit(2);
}

const chrome = await launch({
  chromePath: process.env.CHROMIUM_PATH || undefined,
  chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
});

console.log('page                  perf  a11y  best  seo');
let worst = 100;

for (const url of urls) {
  const r = await lighthouse(url, { port: chrome.port, output: 'json', logLevel: 'error' });
  const c = r.lhr.categories;
  const pct = (k) => Math.round((c[k]?.score ?? 0) * 100);
  worst = Math.min(worst, pct('accessibility'), pct('seo'));
  console.log(
    new URL(url).pathname.padEnd(20) +
    ['performance', 'accessibility', 'best-practices', 'seo']
      .map((k) => String(pct(k)).padStart(4)).join('')
  );
  for (const group of ['accessibility', 'seo', 'best-practices']) {
    for (const ref of c[group]?.auditRefs ?? []) {
      const a = r.lhr.audits[ref.id];
      if (a?.score !== null && a?.score < 1 && ref.weight > 0) {
        console.log(`     ! [${group}] ${a.title}`);
      }
    }
  }
}

await chrome.kill();
process.exit(worst < 100 ? 1 : 0);
