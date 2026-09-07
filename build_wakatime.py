import base64
import json
import os
import re
from urllib.request import Request, urlopen

API_URL = "https://wakatime.com/api/v1/users/current/summaries?range=last_7_days"
MAX_ITEMS = 4


def fetch_summary() -> dict:
    key = os.environ["WAKATIME_API_KEY"]
    auth = base64.b64encode(f"{key}:".encode()).decode()
    request = Request(API_URL, headers={"Authorization": f"Basic {auth}"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def totals_for(summary: dict, key: str) -> list[tuple[str, float]]:
    totals = {}
    for day in summary["data"]:
        for item in day.get(key, []):
            totals[item["name"]] = totals.get(item["name"], 0) + item["total_seconds"]
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)[:MAX_ITEMS]


def build_pie_svg(title: str, items: list[tuple[str, float]]) -> str:
    total = sum(seconds for _, seconds in items)
    if not total:
        return ""
    colors = ("#58a6ff", "#f78166", "#d2a8ff", "#3fb950")
    offset, slices, legend = 0, [], []
    for index, (name, seconds) in enumerate(items):
        percent = seconds / total * 100
        # Slight overlap removes anti-aliased seams between pie slices.
        slices.append(f'<circle cx="58" cy="75" r="38" fill="none" stroke="{colors[index]}" stroke-width="18" pathLength="100" stroke-dasharray="{percent + 0.1:.3f} {99.9 - percent:.3f}" stroke-dashoffset="{-offset:.3f}" transform="rotate(-90 58 75)"/>')
        offset += percent
        minutes = round(seconds / 60)
        hours, minutes = divmod(minutes, 60)
        legend.append(f'<text class="label" x="112" y="{47 + index * 20}" font-size="13"><tspan fill="{colors[index]}">●</tspan> {name} {hours}h {minutes:02}m · {percent:.0f}%</text>')
    style = '<style>.label{fill:#24292f}@media(prefers-color-scheme:dark){.label{fill:#c9d1d9}}</style>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="350" height="125" viewBox="0 0 350 125"><title>{title} · Last 7 days</title>' + style + "".join(slices + legend) + "</svg>"


def replace(readme: str, marker: str, content: str) -> str:
    return re.sub(rf"<!-- {marker} starts -->.*<!-- {marker} ends -->", f"<!-- {marker} starts -->\n\n{content}\n\n<!-- {marker} ends -->", readme, flags=re.S)


def main() -> None:
    with open("README.md", encoding="utf-8") as file:
        readme = file.read()
    summary = fetch_summary()
    with open("assets/workflow.svg", "w", encoding="utf-8") as file:
        file.write(build_pie_svg("Workflow", totals_for(summary, "editors")))
    with open("assets/languages.svg", "w", encoding="utf-8") as file:
        file.write(build_pie_svg("Languages", totals_for(summary, "languages")))
    with open("README.md", "w", encoding="utf-8") as file:
        file.write(readme)


if __name__ == "__main__":
    main()
