"""Write backend/myapp/learn_more.py from the agents' topic -> video picks."""
import json
topics = json.load(open('C:/tmp/kacrawl/solveki_topics.json', encoding='utf-8'))
vids = json.load(open('C:/tmp/kacrawl/videos_by_yt.json', encoding='utf-8'))
match = {}
for i in range(4):
    match.update(json.load(open(f'C:/tmp/kacrawl/match_{i}.json', encoding='utf-8')))
extra = json.load(open('C:/tmp/kacrawl/match_extra.json', encoding='utf-8')) if __import__('os').path.exists('C:/tmp/kacrawl/match_extra.json') else {}
ORDER = ['Grade 1','Grade 2','Grade 3','Grade 4','Grade 5','Grade 6','Grade 7','Grade 8','Algebra I','Geometry','Algebra II','Statistical Reasoning','Pre-Calculus','AP Calculus']
topics.sort(key=lambda t: ORDER.index(t['course']))
lines, missing, bad = [], [], []
course = None
for t in topics:
    g = t['generator_name']
    m = extra.get(g) or match.get(g) or {}
    y = m.get('yt')
    if t['course'] != course:
        course = t['course']
        lines.append(f'    # {course}')
    if not y:
        missing.append(g); continue
    title = ((vids.get(y) or {}).get('title') or m.get('title') or '').strip()
    if not title: bad.append((g, y))
    ch = m.get('channel')
    src = '' if y in vids or ch == 'Khan Academy' else f' ({ch})'
    lines.append(f'    "{g}": "{y}",  # {title}{src}')
body = '\n'.join(lines)
code = f'''"""Curated "Learn more" video links for each topic.

Every practice card offers a "Learn more" link to a video that teaches its
topic. Links are keyed by the topic's stable ``generator_name`` (not the display
name, which can be renamed): ``LEARN_MORE_VIDEOS`` maps a generator to the
YouTube ID of a video that teaches it — a Khan Academy video wherever one exists
(matched from the Khan Academy catalog in docs/khan_academy_math_catalog.md).

A topic with no curated video gets no link; test_learn_more guards that every
seeded topic has one.
"""

# generator_name -> YouTube video ID; the comment is the video's title.
LEARN_MORE_VIDEOS = {{
{body}
}}


def learn_more_url(generator_name):
    """The topic's "Learn more" YouTube URL, or None if it has no curated video."""
    video_id = LEARN_MORE_VIDEOS.get(generator_name) if generator_name else None
    if not video_id:
        return None
    return f"https://www.youtube.com/watch?v={{video_id}}"
'''
open('C:/Users/pauli/Projects/solveki/backend/myapp/learn_more.py', 'w', encoding='utf-8').write(code)
print('mapped', len(topics) - len(missing), 'missing', missing, 'unknown-title', bad)
