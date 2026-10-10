const { chromium } = require('C:/Users/pauli/Projects/solveki/frontend/node_modules/playwright');
const fs = require('fs');
const LIMIT = +(process.env.LIMIT || 0);         // max courses (0 = all), for testing
const VLIMIT = +(process.env.VLIMIT || 0);       // max videos (0 = all), for testing
const CONC = 6;
const load = (f, d) => fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : d;
const courses = load('cache_courses.json', {});  // path -> {title, videos:[...]}
const yt = load('cache_yt.json', {});            // video path -> youtubeId|null
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  let pcv = null;
  page.on('request', r => { const m = r.url().match(/pcv=([0-9a-f]+)/); if (m) pcv = m[1]; });
  await page.goto('https://www.khanacademy.org/math/algebra', { waitUntil: 'domcontentloaded', timeout: 60000 });
  for (let i = 0; i < 30 && !pcv; i++) await page.waitForTimeout(1000);
  await page.waitForTimeout(3000);
  console.log('pcv', pcv);
  const gql = (name, hash, vars) => page.evaluate(async ([name, hash, vars, pcv]) => {
    const q = new URLSearchParams({ hash, fastly_cacheable: 'persist_until_publish', pcv, variables: JSON.stringify(vars), lang: 'en', app: 'khanacademy' });
    for (let a = 0; a < 3; a++) {
      const r = await fetch(`/api/internal/graphql/${name}?${q}`);
      if (r.ok) return await r.json();
      await new Promise(s => setTimeout(s, 2000 * (a + 1)));
    }
    return { error: 'failed' };
  }, [name, hash, vars, pcv]);

  // 1. Course list from the learn menu.
  const menu = await gql('learnMenuTopicsQuery', '365090232', { region: 'US' });
  let list = [];
  if (menu.data) for (const cat of menu.data.learnMenuTopics) {
    if (!/Pre-K - 8th|High school|Multiple grades/.test(cat.translatedTitle || '')) continue;
    for (const ch of cat.children) if (ch.courseId && !list.some(c => c.href === ch.href)) list.push({ href: ch.href, title: ch.translatedTitle });
  }
  if (!list.length) { console.log('menu failed', JSON.stringify(menu).slice(0, 300)); list = JSON.parse(fs.readFileSync('courses_fallback.json')); }
  list = list.filter(c => !/mappers/.test(c.href));
  if (LIMIT) list = list.slice(0, LIMIT);
  console.log('courses:', list.map(c => c.title).join(', '));

  // 2. Course trees.
  for (const c of list) {
    if (courses[c.href]) continue;
    const d = await gql('ContentRouteCourseData', '2276677658', { path: c.href.slice(1), countryCode: 'US' });
    const course = d?.data?.contentRoute?.listedPathData?.course;
    if (!course) { console.log('FAILED course', c.href, JSON.stringify(d).slice(0, 200)); continue; }
    const videos = [];
    for (const unit of course.unitChildren || []) for (const lesson of unit.allOrderedChildren || []) for (const item of lesson.curatedChildren || []) {
      if (item.contentKind !== 'Video') continue;
      videos.push({ unit: unit.translatedTitle, lesson: lesson.translatedTitle, title: item.translatedTitle, summary: item.translatedDescription, url: item.canonicalUrl || item.urlWithinCurationNode, id: item.id });
    }
    courses[c.href] = { title: course.translatedTitle, order: list.indexOf(c), videos };
    fs.writeFileSync('cache_courses.json', JSON.stringify(courses));
    console.log(`${course.translatedTitle}: ${videos.length} videos`);
  }

  // 3. YouTube IDs, one lookup per unique canonical video URL.
  let todo = [...new Set(Object.values(courses).flatMap(c => c.videos.map(v => v.url)))].filter(u => !(u in yt));
  if (VLIMIT) todo = todo.slice(0, VLIMIT);
  console.log('youtube lookups needed:', todo.length);
  let done = 0;
  const worker = async () => {
    while (todo.length) {
      const u = todo.shift();
      const d = await gql('ContentRouteLessonAndContentData', '183983073', { path: u.slice(1), countryCode: 'US' });
      const s = JSON.stringify(d);
      const m = s.match(/"youtubeId":"([^"]+)"/);
      yt[u] = m ? m[1] : (d.error ? undefined : null);
      if (yt[u] === undefined) delete yt[u];
      if (++done % 100 === 0) { fs.writeFileSync('cache_yt.json', JSON.stringify(yt)); console.log('yt', done); }
    }
  };
  await Promise.all(Array.from({ length: CONC }, worker));
  fs.writeFileSync('cache_yt.json', JSON.stringify(yt));
  console.log('done; yt cached', Object.keys(yt).length, 'missing', Object.values(yt).filter(v => !v).length);
  await browser.close();
})().catch(e => { console.error('ERR', e); process.exit(1); });
