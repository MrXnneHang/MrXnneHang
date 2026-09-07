import xml.etree.ElementTree as ET
from build_wakatime import build_card, chart


def test_card():
    items = [{'name': 'A & <B>', 'total_seconds': 3600}, {'name': 'Other', 'total_seconds': 1800}]
    summary = {'data': [{'editors': items, 'languages': items, 'categories': items}]}
    all_time = {'data': {'is_up_to_date': True, 'total_seconds': 72000, 'range': {'start_date': '2024-07-21'}}}
    svg = build_card(summary, all_time)
    root = ET.fromstring(svg)
    image = root.find('.//{http://www.w3.org/2000/svg}image')
    assert image.attrib['y'] == '0' and image.attrib['height'] == root.attrib['height']
    assert image.attrib['preserveAspectRatio'] == 'xMidYMid slice'
    assert 'A &amp; &lt;B&gt;' in svg and '20h 00m' in svg
    for values in ([63, 18, 12, 7], [100]):
        group = ET.fromstring(chart('Languages', [(str(i), v) for i, v in enumerate(values)], 0))
        segments = group.findall('path')
        assert len(segments) == len(values)
        for segment in segments:
            path = segment.attrib['d']
            assert path.count('A 36 36') == 2 and path.count('A 24 24') == 2
            assert path.endswith(' Z')
    ET.fromstring(build_card({'data': []}, all_time))
    all_time['data']['is_up_to_date'] = False
    try:
        build_card(summary, all_time)
    except ValueError:
        pass
    else:
        raise AssertionError('Incomplete history must not be published')


if __name__ == '__main__':
    test_card()
    print('Card checks passed')
