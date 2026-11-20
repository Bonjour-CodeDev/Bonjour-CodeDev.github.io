"""Validate static links and the manuscript figure collection (standard library only)."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIGURES = {'motivation', 'method', 'training', 'confusion_matrix', 'filling',
           'case', 'case-attn', 'preliminary', 'filling-supp'}

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.figures = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, ('Duplicate HTML id', attrs['id'])
            self.ids.add(attrs['id'])
        if tag == 'img':
            assert 'alt' in attrs, 'Image needs alternative text'
            if 'src' in attrs:
                assert attrs.get('width') and attrs.get('height'), 'Image needs intrinsic dimensions'
        if tag == 'a' and 'data-zoom' in attrs:
            assert attrs.get('aria-label') and attrs.get('data-title'), 'Figure needs an accessible title'
            assert attrs['href'].endswith('-full.webp')
            self.figures.add(Path(attrs['href']).name.removesuffix('-full.webp'))
        for key in ('src', 'href'):
            if attrs.get(key):
                self.links.append(attrs[key])

for path in (ROOT/'index.html', ROOT/'SCALER/index.html'):
    page = Page()
    page.feed(path.read_text())
    for link in page.links:
        parsed = urlsplit(link)
        if parsed.scheme or parsed.netloc:
            continue
        if parsed.path:
            assert (path.parent / unquote(parsed.path)).exists(), (path, link)
        elif parsed.fragment:
            assert parsed.fragment in page.ids, (path, link)
    if path.parent.name == 'SCALER':
        assert page.figures == FIGURES, page.figures
        assert {'figure-viewer', 'viewer-stage', 'viewer-image', 'viewer-title',
                'zoom-in', 'zoom-out', 'zoom-fit', 'zoom-actual', 'zoom-level',
                'viewer-close', 'quickstart', 'citation-code', 'toast'} <= page.ids
print('Static links, image dimensions, accessible figure titles, and all nine paper figures passed.')
