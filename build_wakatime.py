import base64
import json
import os
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://wakatime.com/api/v1/users/current/summaries?range=last_7_days"
MAX_ITEMS = 4
COLORS = ("#66aaa9", "#88add1", "#b6a3d6", "#d5bd78")


def fetch_summary() -> dict:
    auth = base64.b64encode(f"{os.environ['WAKATIME_API_KEY']}:".encode()).decode()
    request = Request(API_URL, headers={"Authorization": f"Basic {auth}"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def totals_for(summary: dict, key: str) -> list[tuple[str, float]]:
    totals = {}
    for day in summary["data"]:
        for item in day.get(key, []):
            totals[item["name"]] = totals.get(item["name"], 0) + item["total_seconds"]
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)[:MAX_ITEMS]


def chart(title: str, items: list[tuple[str, float]], y: int) -> str:
    parts = [f'<g transform="translate(0 {y})"><text x="24" y="0" class="heading">{escape(title)}</text>']
    total = sum(seconds for _, seconds in items)
    if not total:
        return ''.join(parts) + '<text x="24" y="40" class="muted">No activity recorded yet</text></g>'
    offset = 0
    for index, (name, seconds) in enumerate(items):
        percent = seconds / total * 100
        parts.append(f'<circle cx="67" cy="69" r="33" fill="none" stroke="{COLORS[index]}" stroke-width="13" pathLength="100" stroke-dasharray="{percent:.6f} {100 - percent:.6f}" stroke-dashoffset="{-offset:.6f}" transform="rotate(-90 67 69)"/>')
        offset += percent
        hours, minutes = divmod(round(seconds / 60), 60)
        row_y = 25 + index * 29
        parts.append(f'<circle cx="124" cy="{row_y - 4}" r="3" fill="{COLORS[index]}"/><text x="136" y="{row_y}" class="label">{escape(name)}</text><text x="136" y="{row_y + 12}" class="muted">{hours}h {minutes:02}m · {percent:.1f}%</text>')
    return ''.join(parts) + '</g>'


def build_card(summary: dict) -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="350" height="425" viewBox="0 0 350 425" role="img" aria-labelledby="title desc">
<title id="title">Languages &amp; Tools · Last 7 days</title>
<desc id="desc">WakaTime active time. Top four tools and languages; percentages within each displayed top four.</desc>
<defs>
  <linearGradient id="water" x2="1" y2="1"><stop stop-color="#f1faf6"/><stop offset=".55" stop-color="#edf5fb"/><stop offset="1" stop-color="#f5f0fa"/></linearGradient>
  <clipPath id="edge"><rect x="1" y="1" width="348" height="423" rx="24"/></clipPath>
</defs>
<style>
text{font-family:Verdana,Arial,sans-serif;fill:#355b65}.heading{font-size:14px;font-weight:600}.label{font-size:12px}.muted{font-size:10px;fill:#587580}.rule{stroke:#cbdedc}
@media(prefers-color-scheme:dark){#water stop:first-child{stop-color:#182f35}#water stop:nth-child(2){stop-color:#20323e}#water stop:last-child{stop-color:#302f43}text{fill:#dcece9}.muted{fill:#afc7cf}.rule{stroke:#405760}}
</style>
<rect x="1" y="1" width="348" height="423" rx="24" fill="url(#water)" stroke="#86b6b5" stroke-opacity=".55"/>
<g clip-path="url(#edge)" fill="none" stroke="#85bcbc" opacity=".22">
<ellipse cx="326" cy="24" rx="56" ry="18"/><ellipse cx="326" cy="24" rx="73" ry="26"/>
<path d="M-15 390 Q55 360 125 390 T365 390 M-15 401 Q55 371 125 401 T365 401"/>
</g>
<g fill="#b6a3d6" opacity=".45" transform="translate(315 366)">
<ellipse cy="-6" rx="3" ry="6"/><ellipse cy="-6" rx="3" ry="6" transform="rotate(72)"/><ellipse cy="-6" rx="3" ry="6" transform="rotate(144)"/><ellipse cy="-6" rx="3" ry="6" transform="rotate(216)"/><ellipse cy="-6" rx="3" ry="6" transform="rotate(288)"/><circle r="2" fill="#d5bd78"/>
</g>
<path d="M310 66v10m-5-5h10M29 365v6m-3-3h6" stroke="#d5bd78" stroke-linecap="round" opacity=".7"/>
<text x="24" y="30" class="heading">Languages &amp; Tools</text>
<text x="24" y="49" class="muted">LAST 7 DAYS · ACTIVE TIME</text>
''' + chart("Workflow", totals_for(summary, "editors"), 83) + '''
<path d="M24 218H326" class="rule"/>
''' + chart("Languages", totals_for(summary, "languages"), 245) + '''
<text x="24" y="407" class="muted">WakaTime · Top 4 per chart · Share within top 4</text>
</svg>'''


def main() -> None:
    card = build_card(fetch_summary())
    Path(__file__).with_name("assets").joinpath("stats.svg").write_text(card, encoding="utf-8")


if __name__ == "__main__":
    main()
