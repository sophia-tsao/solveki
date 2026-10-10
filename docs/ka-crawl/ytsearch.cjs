// Usage: node ytsearch.cjs queries.json out.json
// queries.json: {"key": "search text", ...}. Writes top results per query.
const { chromium } = require('C:/Users/pauli/Projects/solveki/frontend/node_modules/playwright');
const fs = require('fs');
const [, , qfile, ofile] = process.argv;
const queries = JSON.parse(fs.readFileSync(qfile, 'utf8'));
const out = fs.existsSync(ofile) ? JSON.parse(fs.readFileSync(ofile, 'utf8')) : {};
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ locale: 'en-US' });
  for (const [key, q] of Object.entries(queries)) {
    if (out[key]) continue;
    await page.goto('https://www.youtube.com/results?search_query=' + encodeURIComponent(q), { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const html = await page.content();
    const m = html.match(/var ytInitialData = (\{.*?\});<\/script>/s);
    const results = [];
    if (m) {
      const walk = o => {
        if (!o || typeof o !== 'object') return;
        if (o.videoRenderer) {
          const v = o.videoRenderer;
          results.push({ yt: v.videoId, title: v.title?.runs?.[0]?.text, channel: v.ownerText?.runs?.[0]?.text, length: v.lengthText?.simpleText });
          return;
        }
        for (const k in o) walk(o[k]);
      };
      walk(JSON.parse(m[1]));
    }
    out[key] = { query: q, results: results.slice(0, 8) };
    fs.writeFileSync(ofile, JSON.stringify(out, null, 1));
    console.log(key, results.length, results[0] && `${results[0].channel}: ${results[0].title}`);
  }
  await browser.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
