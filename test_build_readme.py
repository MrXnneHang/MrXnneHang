import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import build_readme as blog


def test_cards():
    post = {'title': 'Memory & <code> ' * 15, 'published': '2026-09-07', 'url': 'https://example.com/post'}
    root = ET.fromstring(blog.build_post_card(post))
    assert int(root.attrib['height']) > 144
    assert root.find('{http://www.w3.org/2000/svg}title').text.startswith(post['title'])
    assert 'https://example.com/post' in blog.format_post(post, 1)
    with tempfile.TemporaryDirectory() as directory:
        assets = Path(directory)
        with patch.object(blog, 'ASSETS', assets), patch.object(blog, 'fetch_json', return_value=[post]):
            assert 'blog-1.svg' in blog.build_blog_section()
            original = assets.joinpath('blog-1.svg').read_bytes()
            with patch.object(blog, 'fetch_json', return_value=[dict(post, coverUrl='https://example.com/cover')]), patch.object(blog, 'cover_data', side_effect=ValueError('invalid image')):
                assert blog.build_blog_section() == ''
            assert assets.joinpath('blog-1.svg').read_bytes() == original


if __name__ == '__main__':
    test_cards()
    print('Blog card checks passed')
