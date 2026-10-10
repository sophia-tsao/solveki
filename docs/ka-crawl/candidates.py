import json, math, re
from collections import Counter
topics = json.load(open('solveki_topics.json', encoding='utf-8'))
ka = json.load(open('cache_courses.json', encoding='utf-8'))
yt = json.load(open('cache_yt.json', encoding='utf-8'))
ALIGN = {
  'Grade 1': ['Early math review', '2nd grade math'], 'Grade 2': ['2nd grade math', 'Early math review'],
  'Grade 3': ['3rd grade math', 'Arithmetic'], 'Grade 4': ['4th grade math', 'Arithmetic'],
  'Grade 5': ['5th grade math', 'Arithmetic'], 'Grade 6': ['6th grade math', 'Pre-algebra'],
  'Grade 7': ['7th grade math', 'Pre-algebra'], 'Grade 8': ['8th grade math', 'Pre-algebra', 'Algebra basics'],
  'Algebra I': ['Algebra 1', 'Algebra basics', 'Integrated math 1'],
  'Geometry': ['High school geometry', 'Basic geometry and measurement', 'Integrated math 2'],
  'Algebra II': ['Algebra 2', 'College Algebra', 'Integrated math 3'],
  'Statistical Reasoning': ['Statistics essentials', 'AP®︎/College Statistics'],
  'Pre-Calculus': ['Precalculus', 'AP®︎/College Precalculus', 'Trigonometry'],
  'AP Calculus': ['AP®︎/College Calculus AB', 'AP®︎/College Calculus BC'],
}
STOP = set('a an the of and or to in on for with by is are from what how using two one number numbers find intro introduction example examples'.split())
def toks(s):
    out = []
    for w in re.findall(r'[a-z0-9]+', (s or '').lower()):
        if w in STOP: continue
        if len(w) > 3 and w.endswith('s'): w = w[:-1]
        out.append(w)
    return out
vids = {}
for c in ka.values():
    for v in c['videos']:
        y = yt.get(v['url'])
        if not y: continue
        e = vids.setdefault(y, {'yt': y, 'url': v['url'], 'title': v['title'], 'summary': v['summary'] or '', 'places': []})
        e['places'].append((c['title'], v['unit'], v['lesson']))
docs = {}
for y, e in vids.items():
    bag = Counter()
    for w in toks(e['title']): bag[w] += 3
    for _, u, l in e['places'][:3]:
        for w in toks(l): bag[w] += 2
        for w in toks(u): bag[w] += 1
    for w in toks(e['summary']): bag[w] += 0.5
    docs[y] = bag
df = Counter(w for b in docs.values() for w in b)
N = len(docs)
idf = {w: math.log(N / (1 + n)) + 1 for w, n in df.items()}
def vec(b): return {w: c * idf.get(w, 1) for w, c in b.items()}
dv = {y: vec(b) for y, b in docs.items()}
norm = {y: math.sqrt(sum(x*x for x in v.values())) for y, v in dv.items()}
out = []
for t in topics:
    q = Counter(toks(t['topic_name']) * 2 + toks(t['generator_name'].replace('_', ' ')))
    qv = vec(q); qn = math.sqrt(sum(x*x for x in qv.values())) or 1
    pref = ALIGN.get(t['course'], [])
    scored = []
    for y, v in dv.items():
        s = sum(qv[w] * v.get(w, 0) for w in qv) / (qn * (norm[y] or 1))
        if s <= 0: continue
        if any(p[0] in pref for p in vids[y]['places']): s *= 1.35
        scored.append((s, y))
    scored.sort(reverse=True)
    lines = [f"### {t['generator_name']} | {t['topic_name']} | {t['course']}"]
    for i, (s, y) in enumerate(scored[:10], 1):
        e = vids[y]; c, u, l = e['places'][0]
        lines.append(f"{i}. {y} | {c} > {u} > {l} > {e['title']} — {e['summary'][:110]}")
    out.append('\n'.join(lines))
json.dump(vids, open('videos_by_yt.json', 'w', encoding='utf-8'))
for i in range(4):
    chunk = out[i*81:(i+1)*81]
    open(f'cand_{i}.md', 'w', encoding='utf-8').write('\n\n'.join(chunk) + '\n')
print(len(vids), 'unique videos;', len(out), 'topics')
