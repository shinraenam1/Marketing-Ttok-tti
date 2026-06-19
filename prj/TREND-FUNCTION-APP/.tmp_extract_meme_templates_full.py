import json
import re
from collections import defaultdict
from pathlib import Path

IN_PATH = Path('.tmp_stage1_detail_dump.json')
OUT_PATH = Path('.tmp_meme_template_result_full.json')

QUOTE_RE = re.compile(r"[\"'\u201c\u201d\u2018\u2019]([^\"'\u201c\u201d\u2018\u2019\n]{4,120})[\"'\u201c\u201d\u2018\u2019]")
EXPLICIT_RE = re.compile(r"(?:^|\s)(나\s+\d{2}년생\s+[^\s,.!?]{1,16}인데~?)(?:\s|$)")
PATTERN_END_RE = re.compile(r"([^\n]{4,80}(?:인데~|도 해~|해~))")


def normalize_template(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\b\d{2}년생\b", "○○년생", t)
    t = re.sub(r"(○○년생\s+)[^\s,.!?]{1,16}(?=인데)", r"\1○○○", t)
    t = re.sub(r"\b\d+(?:\.?\d+)?\b", "○○", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def iter_texts(doc: dict):
    yield str(doc.get('title', ''))
    yield str(doc.get('excerpt', ''))
    yield str(doc.get('body_text_head', ''))
    yield str(doc.get('emphasis_text', ''))


def extract_templates(text: str):
    out = []
    for m in EXPLICIT_RE.finditer(text):
        out.append(m.group(1).strip())
    for m in QUOTE_RE.finditer(text):
        phrase = m.group(1).strip()
        if any(k in phrase for k in ["년생", "인데", "챌린지", "밈", "~"]):
            out.append(phrase)
    for m in PATTERN_END_RE.finditer(text):
        phrase = m.group(1).strip()
        if any(k in phrase for k in ["년생", "인데~", "해~"]):
            out.append(phrase)

    unique = []
    seen = set()
    for item in out:
        n = normalize_template(item)
        if len(n) < 4:
            continue
        if n in seen:
            continue
        seen.add(n)
        unique.append((n, item))
    return unique


def main():
    data = json.loads(IN_PATH.read_text(encoding='utf-8'))
    per_source = data.get('sources') or data.get('samples') or {}

    bucket = defaultdict(lambda: {'count': 0, 'examples': []})

    for source, docs in per_source.items():
        for d in docs:
            text = "\n".join(iter_texts(d))
            for norm, raw in extract_templates(text):
                item = bucket[norm]
                item['count'] += 1
                if len(item['examples']) < 3:
                    item['examples'].append(
                        {
                            'source': source,
                            'title': d.get('title', ''),
                            'url': d.get('url', ''),
                            'raw_match': raw,
                        }
                    )

    ranked = sorted(
        (
            {
                'template': k,
                'count': v['count'],
                'examples': v['examples'],
            }
            for k, v in bucket.items()
        ),
        key=lambda x: (x['count'], len(x['template'])),
        reverse=True,
    )

    out = {
        'note': 'meme-like template extraction from stage1 detail sample',
        'total_templates': len(ranked),
        'top_templates': ranked[:30],
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
