import base64
import json
import math
import os
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

ASSETS = Path(__file__).with_name('assets')
MAX_ITEMS = 4
COLORS = ('#66aaa9', '#88add1', '#b6a3d6', '#d5bd78')


def fetch_json(endpoint):
    auth = base64.b64encode(f"{os.environ['WAKATIME_API_KEY']}:".encode()).decode()
    request = Request('https://wakatime.com/api/v1/users/current/' + endpoint, headers={'Authorization': f'Basic {auth}'})
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def totals_for(summary, key):
    totals = {}
    for day in summary['data']:
        for item in day.get(key, []):
            totals[item['name']] = totals.get(item['name'], 0) + item['total_seconds']
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def duration(seconds):
    hours, minutes = divmod(round(seconds / 60), 60)
    return f'{hours:,}h {minutes:02}m'


def chart(title, items, y):
    items = items[:MAX_ITEMS]
    total = sum(seconds for _, seconds in items)
    parts = [f'<g transform="translate(0 {y})"><text x="30" y="0" class="heading">{escape(title)}</text>']
    offset = 0
    for index, (name, seconds) in enumerate(items):
        if seconds <= 0:
            continue
        percent = seconds / total * 100
        def point(radius, angle):
            angle = math.radians(angle * 3.6 - 90)
            return f'{72 + radius * math.cos(angle):.6f} {58 + radius * math.sin(angle):.6f}'
        start, middle, end = offset, offset + percent / 2, offset + percent
        parts.append(f'<path class="segment" fill="{COLORS[index]}" d="M {point(36, start)} A 36 36 0 0 1 {point(36, middle)} A 36 36 0 0 1 {point(36, end)} L {point(24, end)} A 24 24 0 0 0 {point(24, middle)} A 24 24 0 0 0 {point(24, start)} Z"/>')
        offset += percent
        row = 26 + index * 23
        parts.append(f'<circle cx="131" cy="{row - 4}" r="3" fill="{COLORS[index]}"/><text x="143" y="{row}" class="label">{escape(name)}</text><text x="355" y="{row}" text-anchor="end" class="muted">{duration(seconds)} · {percent:.1f}%</text>')
    if not total:
        parts.append('<text x="30" y="50" class="muted">No activity recorded yet</text>')
    return ''.join(parts) + '</g>'


def build_card(summary, all_time):
    portrait = ASSETS.joinpath('portrait.txt').read_text(encoding='utf-8')
    categories = totals_for(summary, 'categories')
    total = sum(seconds for _, seconds in categories)
    bars, x = [], 30
    for index, (name, seconds) in enumerate(categories):
        width = seconds / total * 325 if total else 0
        bars.append(f'<rect x="{x:.4f}" y="550" width="{width:.4f}" height="8" fill="{COLORS[index % len(COLORS)]}"/>')
        x += width
        bars.append(f'<text x="30" y="{580 + index * 19}" class="muted">{escape(name)} · {duration(seconds)} · {seconds / total:.1%}</text>' if total else '')
    footer_y = max(648, 607 + len(categories) * 19)
    height = footer_y + 54
    data = all_time['data']
    if not data.get('is_up_to_date'):
        raise ValueError('All-time statistics are still being calculated; keeping the existing card')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" viewBox="0 0 760 {height}" role="img" aria-labelledby="title desc">
<title id="title">XnneHang · About me, Languages &amp; Tools</title>
<desc id="desc">Weekly WakaTime activity and all-time active time. Chart percentages are within each top four. Frieren illustration fills the right side.</desc>
<defs>
<linearGradient id="water" x2="1" y2="1"><stop stop-color="#f1faf6"/><stop offset=".55" stop-color="#edf5fb"/><stop offset="1" stop-color="#f5f0fa"/></linearGradient>
<clipPath id="edge"><rect x="1" y="1" width="758" height="{height - 2}" rx="24"/></clipPath>
</defs>
<style>text{{font-family:Verdana,Arial,sans-serif;fill:#355b65}}.heading{{font-size:14px;font-weight:600}}.label{{font-size:12px}}.muted{{font-size:11px;fill:#587580}}.rule{{stroke:#cbdedc}}
@media(prefers-color-scheme:dark){{#water stop:first-child{{stop-color:#182f35}}#water stop:nth-child(2){{stop-color:#20323e}}#water stop:last-child{{stop-color:#302f43}}text{{fill:#dcece9}}.muted{{fill:#afc7cf}}.rule{{stroke:#405760}}}}</style>
<rect x="1" y="1" width="758" height="{height - 2}" rx="24" fill="url(#water)" stroke="#86b6b5" stroke-opacity=".55"/>
<g clip-path="url(#edge)">
<g fill="none" stroke="#85bcbc" opacity=".22"><ellipse cx="695" cy="40" rx="115" ry="30"/><ellipse cx="695" cy="40" rx="140" ry="43"/><path d="M-20 {height - 20} Q90 {height - 45} 200 {height - 20} T440 {height - 20}"/></g>
<image x="365" y="18" width="375" height="{height - 18}" preserveAspectRatio="xMidYMax meet" href="{portrait}"/>
</g>
<text x="30" y="36" class="muted">A LITTLE ABOUT ME</text>
<text x="30" y="73" font-size="23" font-weight="600">Ciallo ～(∠・ω&lt; )⌒★!</text>
<text x="30" y="102" class="heading">I'm XnneHang.</text>
<g class="label"><text x="30" y="134">Intern at NevaMind-AI.</text><text x="30" y="156">Interested in Long-Term Memory.</text><text x="30" y="186">Reading, writing, anime — and curiosity.</text><text x="30" y="208">I love interesting things and trying them out.</text><text x="30" y="230">I want to bring waifus into the real world.</text></g>
<path d="M30 250Q110 245 192 250T355 250" class="rule" fill="none"/>
<text x="30" y="276" class="heading">Languages &amp; Tools</text><text x="30" y="295" class="muted">LAST 7 DAYS · TOP 4 PER CHART</text>
{chart('Workflow', totals_for(summary, 'editors'), 322)}
{chart('Languages', totals_for(summary, 'languages'), 434)}
{''.join(bars)}
<path d="M30 {footer_y - 22}H355" class="rule"/>
<text x="30" y="{footer_y}" class="heading">All-time active time · {duration(data['total_seconds'])}</text>
<text x="30" y="{footer_y + 19}" class="muted">Since {escape(data['range']['start_date'])} · Visit my blog →</text>
<text x="30" y="{height - 12}" font-size="9" class="muted">WakaTime · Ring shares within top 4; category shares across all activity.</text>
</svg>'''


def main():
    card = build_card(fetch_json('summaries?range=last_7_days'), fetch_json('all_time_since_today'))
    ASSETS.joinpath('stats.svg').write_text(card, encoding='utf-8')


if __name__ == '__main__':
    main()
