"""Structural checks for offline illustrated manuals; no browser required."""
import argparse
import base64
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class ManualParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.errors, self.step_images = [], [], [], []
        self.images = self.depth = self.step_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.links.append(a['href'][1:])
        if tag in ('script', 'link') and (a.get('src') or a.get('href')):
            self.errors.append('External script/stylesheet dependency')
        if tag == 'article':
            self.depth += 1
            if 'step' in a.get('class', '').split():
                self.step_depth = self.depth
                self.step_images.append(0)
        if tag == 'img':
            self.images += 1
            src = a.get('src', '')
            if not src.startswith('data:image/'):
                self.errors.append('Nonembedded image: ' + src[:80])
            elif ';base64,' in src:
                try:
                    if not base64.b64decode(src.split(',', 1)[1], validate=True):
                        self.errors.append('Empty image payload')
                except ValueError:
                    self.errors.append('Invalid embedded image payload')
            if self.step_depth:
                self.step_images[-1] += 1
        if tag == 'svg' and self.step_depth:
            self.step_images[-1] += 1

    def handle_endtag(self, tag):
        if tag == 'article':
            if self.depth == self.step_depth:
                self.step_depth = 0
            self.depth -= 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html', type=Path)
    ap.add_argument('--parts', type=int, required=True)
    ap.add_argument('--steps', type=int, required=True)
    args = ap.parse_args()
    p = ManualParser()
    p.feed(args.html.read_text(encoding='utf-8'))
    if len(p.ids) != len(set(p.ids)):
        p.errors.append('Duplicate IDs')
    p.errors.extend('Missing anchor: ' + x for x in p.links if x not in p.ids)
    cards = [x for x in p.ids if re.fullmatch(r'P\d{2,}', x)]
    if len(cards) != args.parts:
        p.errors.append(f'Expected {args.parts} part cards; found {len(cards)}')
    if len(p.step_images) != args.steps:
        p.errors.append(f'Expected {args.steps} steps; found {len(p.step_images)}')
    p.errors.extend(f'Step {i} has no image' for i, n in enumerate(p.step_images, 1) if n < 1)
    result = dict(valid=not p.errors, part_cards=len(cards), steps=len(p.step_images),
                  images=p.images, errors=p.errors, scope='Structure only; manual visual and mechanical review still required.')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['valid'] else 1)


if __name__ == '__main__':
    main()
