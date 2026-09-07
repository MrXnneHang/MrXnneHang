import base64
import json
import os
import re
from urllib.request import Request, urlopen

API_URL = "https://wakatime.com/api/v1/users/current/summaries?range=last_7_days"


def fetch_summary() -> dict:
    key = os.environ["WAKATIME_API_KEY"]
    auth = base64.b64encode(f"{key}:".encode()).decode()
    request = Request(API_URL, headers={"Authorization": f"Basic {auth}"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def build_table(summary: dict, key: str, title: str, column: str) -> str:
    totals = {}
    for day in summary["data"]:
        for item in day.get(key, []):
            totals[item["name"]] = totals.get(item["name"], 0) + item["total_seconds"]

    total = sum(totals.values())
    if not total:
        return "_No WakaTime activity recorded in the last 7 days._"

    rows = []
    for name, seconds in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        minutes = round(seconds / 60)
        hours, minutes = divmod(minutes, 60)
        rows.append(f"| {name} | {hours}h {minutes}m | {seconds / total:.1%} |")
    return "\n".join([title, "", f"| {column} | Active time | Share |", "| --- | ---: | ---: |", *rows])


def main() -> None:
    with open("README.md", encoding="utf-8") as file:
        readme = file.read()
    summary = fetch_summary()
    languages = build_table(summary, "languages", "### Last 7 days", "Language")
    workflow = build_table(summary, "editors", "### Current workflow · Last 7 days", "Tool")
    readme = re.sub(r"<!-- languages starts -->.*<!-- languages ends -->", f"<!-- languages starts -->\n\n{languages}\n\n<!-- languages ends -->", readme, flags=re.S)
    readme = re.sub(r"<!-- waka starts -->.*<!-- waka ends -->", f"<!-- waka starts -->\n\n{workflow}\n\n<!-- waka ends -->", readme, flags=re.S)
    with open("README.md", "w", encoding="utf-8") as file:
        file.write(readme)


if __name__ == "__main__":
    main()
