import json
import os
import re
import time
from html import escape
from urllib.request import Request, urlopen

BLOG_API = "https://xnnehang.top/api/posts.json"
SITE_URL = "https://xnnehang.top"
MAX_POSTS = 3
COVER_WIDTH = 160

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

def format_post(post: dict) -> str:
    title = escape(post["title"], quote=False)
    desc = escape(post["description"], quote=False)
    url = escape(post["url"], quote=True)
    date = escape(post["published"], quote=False)
    cover = post.get("coverUrl")

    cover_cell = ""
    if cover:
        cover_esc = escape(cover, quote=True)
        alt = escape(f"{post['title']} cover", quote=True)
        cover_cell = (
            f'<td width="{COVER_WIDTH}" valign="top">'
            f'<a href="{url}">'
            f'<img src="{cover_esc}" alt="{alt}" width="{COVER_WIDTH}" />'
            f"</a></td>"
        )

    return (
        "<tr>"
        f"{cover_cell}"
        f'<td valign="top"><a href="{url}">{title}</a><br>'
        f"<sub>{desc}<br>{date}</sub></td>"
        "</tr>"
    )


def build_blog_section() -> str:
    try:
        posts = fetch_json(BLOG_API)
        if not posts:
            return ""
        rows = [format_post(p) for p in posts[:MAX_POSTS]]
        return "<table>\n{}\n</table>".format("\n".join(rows))
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
