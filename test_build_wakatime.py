import xml.etree.ElementTree as ET

from build_wakatime import build_card, totals_for


def test_card():
    items = [{"name": "A & <B>" if i == 6 else str(i), "total_seconds": i * 600} for i in range(7)]
    summary = {"data": [{"editors": items, "languages": items}]}
    assert len(totals_for(summary, "editors")) == 4
    svg = build_card(summary)
    root = ET.fromstring(svg)
    assert root.attrib["width"] == "350"
    assert 'A &amp; &lt;B&gt;' in svg and '1h 00m' in svg
    assert svg.count('stroke-dasharray=') == 8
    assert '33.3%' in svg and 'Share within top 4' in svg
    ET.fromstring(build_card({"data": []}))
    assert build_card({"data": []}).count('No activity recorded yet') == 2


if __name__ == "__main__":
    test_card()
    print("Card checks passed")
