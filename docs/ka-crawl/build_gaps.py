"""Render docs/khan_academy_coverage_gaps.md from the crawl + coverage judgments."""
import json, re
from datetime import date
KA = 'https://www.khanacademy.org'
ka = json.load(open('cache_courses.json', encoding='utf-8'))
L = json.load(open('lessons.json', encoding='utf-8'))
cov = {}
for i in range(4): cov.update(json.load(open(f'coverage_{i}.json', encoding='utf-8')))
covered = {l['lesson'].strip().lower(): bool(cov[f'L{i}']) for i, l in enumerate(L)}
topics = {t['generator_name']: t for t in json.load(open('solveki_topics.json', encoding='utf-8'))}
extra = json.load(open('match_extra.json', encoding='utf-8'))
match = {}
for i in range(4): match.update(json.load(open(f'match_{i}.json', encoding='utf-8')))

def cell(s): return (s or '').replace('|', r'\|').strip()
def anchor(t): return re.sub(r'[^\w\- ]', '', t.lower()).replace(' ', '-')

seen = set()
sections, n_lessons, n_units_full = [], 0, 0
for c in sorted((c for c in ka.values() if c['videos']), key=lambda c: c['order']):
    units = {}
    for v in c['videos']:
        u = units.setdefault(v['unit'], {})
        l = u.setdefault(v['lesson'], {'videos': [], 'url': v['url'].rsplit('/v/', 1)[0]})
        if v['title'] not in l['videos']: l['videos'].append(v['title'])
    body = []
    for uname, lessons in units.items():
        missing = [(n, l) for n, l in lessons.items() if not covered[n.strip().lower()]]
        new = [(n, l) for n, l in missing if n.strip().lower() not in seen]
        for n, _ in missing: seen.add(n.strip().lower())
        for n in lessons: seen.add(n.strip().lower())
        if not new: continue
        whole = len(missing) == len(lessons)
        n_units_full += whole
        body.append(f"### {uname}" + (" — *entire unit not covered*" if whole else f" — {len(missing)} of {len(lessons)} lessons not covered"))
        body.append('')
        for n, l in new:
            ex = '; '.join(l['videos'][:3])
            body.append(f"- [{cell(n)}]({KA}{l['url']}) — e.g. {cell(ex)}")
            n_lessons += 1
        body.append('')
    if body:
        sections.append((c['title'], body))

ka_channel = {g: e for g, e in extra.items() if e['channel'].startswith('Khan Academy') and not match.get(g, {}).get('yt')}
other = {g: e for g, e in extra.items() if not e['channel'].startswith('Khan Academy') and not match.get(g, {}).get('yt')}

def topic_rows(d):
    rows = ['| Solveki topic | Course | Generator | "Learn more" video used |', '|---|---|---|---|']
    order = list(topics)
    for g in sorted(d, key=order.index):
        t, e = topics[g], d[g]
        rows.append(f"| {cell(t['topic_name'])} | {t['course']} | `{g}` | [{cell(e['title'])}](https://www.youtube.com/watch?v={e['yt']}) ({cell(e['channel'])}) |")
    return rows

out = [
 '# Khan Academy ↔ Solveki coverage gaps', '',
 f'Compared on {date.today().isoformat()}: the Khan Academy math catalog ([khan_academy_math_catalog.md](khan_academy_math_catalog.md), '
 '29 core courses) against Solveki\'s 324 practice topics (`seed_topics.py`).', '',
 'A Khan Academy lesson counts as covered when some Solveki topic drills the same core skill — not merely the same broad area. '
 'These calls were made by reading each lesson\'s videos and, for borderline cases, the Solveki generator source, so treat individual entries as judgment calls rather than exact.', '',
 '## Summary', '',
 f'- Khan Academy lessons compared (deduplicated by name across courses): **{len(L)}**',
 f'- Covered by a Solveki topic: **{sum(covered.values())}**',
 f'- Not covered (listed below): **{n_lessons}**, including **{n_units_full}** units with no coverage at all',
 f'- Solveki topics with no video in Khan Academy\'s current math courses: **{len(ka_channel) + len(other)}**', '',
 '## Contents', '',
 '- [Solveki topics that Khan Academy doesn\'t have](#solveki-topics-that-khan-academy-doesnt-have)',
 '- [Khan Academy topics that Solveki doesn\'t have](#khan-academy-topics-that-solveki-doesnt-have)',
]
out += [f"  - [{t}](#{anchor(t)})" for t, _ in sections]
out += ['', '## Solveki topics that Khan Academy doesn\'t have', '',
 'No video in Khan Academy\'s current math course pages teaches these Solveki topics. Each still has a "Learn more" video, found by searching YouTube.', '',
 f'### On Khan Academy\'s YouTube channels but not in its current courses ({len(ka_channel)})', '',
 'Khan Academy made a video for these, but it is no longer part of the current math courses. Some are older uploads; some are from the Khan Academy India channel.', '']
out += topic_rows(ka_channel)
out += ['', f'### No Khan Academy video found ({len(other)})', '',
 'Neither the Khan Academy catalog nor a YouTube search turned up a Khan Academy video for these, so the "Learn more" link uses another educational channel.', '']
out += topic_rows(other)
out += ['', '## Khan Academy topics that Solveki doesn\'t have', '',
 'Grouped by Khan Academy course and unit, in course order. A lesson that appears in several courses is listed once, under the first course that has it, '
 'so later courses only show what is new to them. Each lesson links to Khan Academy.', '']
for t, body in sections:
    out += [f'## {t}', ''] + body
open('C:/Users/pauli/Projects/solveki/docs/khan_academy_coverage_gaps.md', 'w', encoding='utf-8').write('\n'.join(out))
print('lessons listed', n_lessons, 'full units', n_units_full, 'ka-channel', len(ka_channel), 'other', len(other))
