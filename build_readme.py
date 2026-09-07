import base64
import json
import textwrap
from pathlib import Path
import os
import re
import time
from html import escape
from urllib.request import Request, urlopen

BLOG_API = "https://xnnehang.top/en/api/posts.json"
SITE_URL = "https://xnnehang.top"
MAX_POSTS = 3
ASSETS = Path(__file__).with_name('assets')

# Cache-bust param forces Cloudflare / CDN to fetch fresh data each run.
# Browser-like UA avoids 403s from edge bot-checks.
FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_json(url: str) -> list | dict:
    req = Request(f"{url}?t={int(time.time())}", headers=FETCH_HEADERS)
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def replace_chunk(content: str, marker: str, chunk: str) -> str:
    pattern = re.compile(
        r"<!-- {} starts -->.*<!-- {} ends -->".format(marker, marker),
        re.DOTALL,
    )
    replacement = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)
    return pattern.sub(replacement, content)


# ---------------------------------------------------------------------------
# Blog posts section
# ---------------------------------------------------------------------------

def cover_data(url: str) -> str:
    if not url.startswith('https://'):
        raise ValueError('Cover URL must use HTTPS')
    with urlopen(Request(url, headers=FETCH_HEADERS), timeout=20) as response:
        data = response.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise ValueError('Cover exceeds 8 MiB')
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'image/png'
    elif data.startswith(b'\xff\xd8\xff'):
        mime = 'image/jpeg'
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        mime = 'image/webp'
    else:
        raise ValueError('Unsupported cover image')
    return f'data:{mime};base64,' + base64.b64encode(data).decode()


def build_post_card(post: dict, cover: str = '') -> str:
    # ponytail: character wrapping targets English titles; measured font layout if multilingual posts need it.
    lines = textwrap.wrap(post['title'], width=52) or ['Untitled']
    height = max(144, 68 + len(lines) * 22)
    title = ''.join(f'<tspan x="210" y="{35 + i * 22}">{escape(line)}</tspan>' for i, line in enumerate(lines))
    image = f'<image x="12" y="12" width="174" height="{height - 24}" preserveAspectRatio="xMidYMid slice" clip-path="url(#cover)" href="{escape(cover, quote=True)}"/>' if cover else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" viewBox="0 0 760 {height}" role="img" aria-labelledby="title">
<title id="title">{escape(post['title'])} · {escape(post['published'])}</title>
<defs><linearGradient id="water" x2="1" y2="1"><stop stop-color="#f1faf6"/><stop offset=".55" stop-color="#edf5fb"/><stop offset="1" stop-color="#f5f0fa"/></linearGradient><clipPath id="cover"><rect x="12" y="12" width="174" height="{height - 24}" rx="14"/></clipPath></defs>
<style>text{{font-family:Verdana,Arial,sans-serif;fill:#355b65}}.date{{fill:#587580}}@media(prefers-color-scheme:dark){{#water stop:first-child{{stop-color:#182f35}}#water stop:nth-child(2){{stop-color:#20323e}}#water stop:last-child{{stop-color:#302f43}}text{{fill:#dcece9}}.date{{fill:#afc7cf}}}}</style>
<rect x="1" y="1" width="758" height="{height - 2}" rx="22" fill="url(#water)" stroke="#86b6b5" stroke-opacity=".55"/>
<rect x="12" y="12" width="174" height="{height - 24}" rx="14" fill="#85bcbc" fill-opacity=".2"/>{image}
<text font-size="15" font-weight="600">{title}</text>
<text x="210" y="{height - 24}" font-size="11" class="date">{escape(post['published'])}</text>
<text x="720" y="{height - 24}" font-size="17" class="date">↗</text>
</svg>'''


def format_post(post: dict, index: int) -> str:
    url = post['url']
    if not url.startswith('https://'):
        raise ValueError('Post URL must use HTTPS')
    return f'<a href="{escape(url, quote=True)}"><img src="assets/blog-{index}.svg" alt="{escape(post["title"], quote=True)} · {escape(post["published"], quote=True)}" width="760" /></a>'


def build_blog_section() -> str:
    try:
        posts = fetch_json(BLOG_API)
        if not posts:
            return ""
        posts = posts[:MAX_POSTS]
        # Fetch and render every card before replacing any existing assets.
        cards = [build_post_card(p, cover_data(p['coverUrl']) if p.get('coverUrl') else '') for p in posts]
        rows = [format_post(p, i) for i, p in enumerate(posts, 1)]
        ASSETS.mkdir(exist_ok=True)
        for i, card in enumerate(cards, 1):
            ASSETS.joinpath(f'blog-{i}.svg').write_text(card, encoding='utf-8')
        return '\n\n'.join(rows)
    except Exception as exc:
        print(f"[blog] fetch failed: {exc}")
        return ""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    blog_md = build_blog_section()
    if blog_md:
        content = replace_chunk(content, "blog", blog_md)
        print(f"[blog] updated with {len(blog_md)} chars")
    else:
        print("[blog] no update (empty result or fetch error)")

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("README updated successfully.")
