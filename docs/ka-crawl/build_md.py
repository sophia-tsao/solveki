"""Render the crawled Khan Academy caches into a markdown catalog."""
import json
import re
from datetime import date

courses = json.load(open('cache_courses.json', encoding='utf-8'))
yt = json.load(open('cache_yt.json', encoding='utf-8'))
KA = 'https://www.khanacademy.org'

def cell(s):
    return (s or '').replace('|', r'\|').replace('\n', ' ').strip()

out = [
    '# Khan Academy Math Video Catalog', '',
    f'Crawled from {KA}/math on {date.today().isoformat()}. One row per video, grouped by course, unit, and lesson.',
    'A video that appears in several courses is listed under each one.', '',
]
total = 0
ordered = sorted((c for c in courses.values() if c['videos']), key=lambda c: c['order'])

def anchor(t):
    return re.sub(r'[^\w\- ]', '', t.lower()).replace(' ', '-')
out += ['## Courses', '']
out += [f"- [{c['title']}](#{anchor(c['title'])}) ({len(c['videos'])} videos)" for c in ordered]
out.append('')
for c in ordered:
    out += [f"## {c['title']}", '']
    unit = lesson = None
    for v in c['videos']:
        if v['unit'] != unit:
            unit, lesson = v['unit'], None
            out += [f'### {unit}', '']
        if v['lesson'] != lesson:
            lesson = v['lesson']
            out += [f'#### {lesson}', '', '| Title | Khan Academy | YouTube | Summary |', '|---|---|---|---|']
        yid = yt.get(v['url'])
        ytcell = f'[{yid}](https://www.youtube.com/watch?v={yid})' if yid else '—'
        out.append(f"| {cell(v['title'])} | [link]({KA}{v['url']}) | {ytcell} | {cell(v['summary'])} |")
        total += 1
    out.append('')
out.insert(4, f'**{total} video entries across {len(ordered)} courses.**')
open('khan_academy_math_catalog.md', 'w', encoding='utf-8').write('\n'.join(out))
print(total, 'entries')
