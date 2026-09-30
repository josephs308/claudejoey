// Load every .html page of a built site in headless Chromium at phone and desktop
// widths and report runtime problems.
//
// Usage: NODE_PATH=$(npm root -g) node browser_check.js SITE_DIR [--contrast] [--widths 390,1440] [--block regex]
//
// Reports per page: JS errors, console errors, failed requests, HTTP >= 400,
// horizontal overflow (sideways scrolling), web fonts that failed to load.
// --contrast also lists text below WCAG AA contrast (4.5:1, or 3:1 for large text)
// against a solid background (text over background images is skipped: check it by eye).
// --block skips requests whose URL matches the regex (e.g. flaky external image CDNs).
// Exit code 1 if any page has a problem.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');

const args = process.argv.slice(2);
const flagValues = new Set(['--widths', '--block'].map(f => args.indexOf(f)).filter(i => i >= 0).map(i => i + 1));
const root = path.resolve(args.find((a, i) => !a.startsWith('--') && !flagValues.has(i)) || '.');
const contrast = args.includes('--contrast');
const wi = args.indexOf('--widths');
const widths = wi >= 0 ? args[wi + 1].split(',').map(Number) : [390, 1440];
const bi = args.indexOf('--block');
const block = bi >= 0 ? new RegExp(args[bi + 1]) : null;

const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif',
  '.gif': 'image/gif', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.woff': 'font/woff', '.json': 'application/json',
  '.xml': 'application/xml', '.txt': 'text/plain', '.webm': 'video/webm', '.mp4': 'video/mp4' };

function serve() {
  const srv = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0].split('#')[0]);
    let fp = path.join(root, p);
    if (fs.existsSync(fp) && fs.statSync(fp).isDirectory()) fp = path.join(fp, 'index.html');
    if (!fs.existsSync(fp) && fs.existsSync(fp + '.html')) fp += '.html';
    if (!fs.existsSync(fp)) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(fp).toLowerCase()] || 'application/octet-stream' });
    fs.createReadStream(fp).pipe(res);
  });
  return new Promise(r => srv.listen(0, '127.0.0.1', () => r(srv)));
}

const urls = [];
(function walk(d) {
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    if (fs.statSync(p).isDirectory()) { if (f !== 'node_modules' && !f.startsWith('.')) walk(p); }
    else if (f.endsWith('.html')) urls.push('/' + path.relative(root, p).split(path.sep).join('/').replace(/(^|\/)index\.html$/, '$1'));
  }
})(root);

function contrastProblems() {
  const rgb = s => { const m = s.match(/[\d.]+/g) || [0, 0, 0]; return [+m[0], +m[1], +m[2], m[3] === undefined ? 1 : +m[3]]; };
  const lum = c => { const a = c.slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * a[0] + .7152 * a[1] + .0722 * a[2]; };
  function bgOf(e) {
    const layers = [];
    while (e) {
      const c = getComputedStyle(e);
      if (c.backgroundImage && c.backgroundImage !== 'none') return null;
      const b = rgb(c.backgroundColor);
      if (b[3] > 0) { layers.push(b); if (b[3] >= 1) break; }
      e = e.parentElement;
    }
    let base = [255, 255, 255];
    for (const l of layers.reverse()) base = base.map((v, i) => v * (1 - l[3]) + l[i] * l[3]);
    return base;
  }
  const out = [];
  document.querySelectorAll('body *').forEach(e => {
    if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
    const c = getComputedStyle(e);
    if (c.visibility === 'hidden' || c.display === 'none' || +c.opacity < .99) return;
    if (!e.getBoundingClientRect().width) return;
    if (e.closest('[disabled],[aria-disabled="true"]')) return; // WCAG exempts disabled controls
    const bg = bgOf(e); if (!bg) return;
    const f = rgb(c.color);
    const fg = bg.map((v, i) => v * (1 - f[3]) + f[i] * f[3]);
    const L1 = lum(fg), L2 = lum(bg);
    const cr = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
    const size = parseFloat(c.fontSize), big = size >= 24 || (size >= 18.66 && +c.fontWeight >= 700);
    if (cr < (big ? 3 : 4.5)) out.push(`contrast ${cr.toFixed(2)} ${e.tagName.toLowerCase()}${e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).join('.') : ''} "${e.textContent.trim().slice(0, 40)}"`);
  });
  return out;
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}`;
  const launchOpts = {};
  if (process.env.CHROMIUM_PATH) launchOpts.executablePath = process.env.CHROMIUM_PATH;
  const browser = await chromium.launch(launchOpts);
  let bad = 0;
  for (const w of widths) {
    for (const u of urls) {
      const page = await browser.newPage({ viewport: { width: w, height: 900 } });
      const errs = [];
      page.on('pageerror', e => errs.push('JS ' + e.message));
      page.on('console', m => { if (m.type() === 'error' && !/net::|Failed to load resource/.test(m.text())) errs.push('console ' + m.text().slice(0, 140)); });
      page.on('requestfailed', r => { if (!(block && block.test(r.url()))) errs.push('request failed ' + r.url()); });
      page.on('response', r => { if (r.status() >= 400 && !(block && block.test(r.url())) && !(u.endsWith('404.html') && r.url() === base + u)) errs.push(r.status() + ' ' + r.url()); });
      if (block) await page.route(block, r => r.abort());
      try { await page.goto(base + u, { waitUntil: 'networkidle', timeout: 30000 }); }
      catch (e) { errs.push('load ' + e.message.split('\n')[0]); }
      const ov = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth).catch(() => 0);
      if (ov > 1) errs.push(`horizontal overflow ${ov}px`);
      const fonts = await page.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.status === 'error').map(f => f.family); }).catch(() => []);
      if (fonts.length) errs.push('font failed ' + fonts.join(', '));
      if (contrast) {
        await page.evaluate(() => document.querySelectorAll('*').forEach(e => { e.style.transition = 'none'; e.style.animation = 'none'; }));
        errs.push(...(await page.evaluate(contrastProblems)).slice(0, 15));
      }
      if (errs.length) { bad++; console.log(`${w}px ${u}`); for (const e of [...new Set(errs)].slice(0, 20)) console.log('   ' + e); }
      await page.close();
    }
  }
  console.log(`pages ${urls.length} x widths ${widths.join(',')}  problems ${bad}`);
  await browser.close(); srv.close();
  process.exit(bad ? 1 : 0);
})();
