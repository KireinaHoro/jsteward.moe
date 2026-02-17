#!/usr/bin/env python
# -*- coding: utf-8 -*- #

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from imaging.photoswipe import PhotoSwipeImageExtension
from imaging.gallery import image_getter

AUTHOR = 'Pengcheng Xu'
SITENAME = 'Pengcheng Xu'
SITEURL = 'https://jsteward.moe'

COMMIT = os.environ['COMMIT'][:7]

PATH = 'content'
OUTPUT_PATH = os.environ['out']

TIMEZONE = 'Asia/Shanghai'

DEFAULT_LANG = 'en'

THEME = 'theme'

FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/{slug}.atom.xml'
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DISQUS_SITENAME = "jsteward"
ANALYTICS = '''
<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "186b51cd5c0b40cd97940589dc4916d5"}'></script><!-- End Cloudflare Web Analytics -->
'''

# Blogroll
LINKS = (
    ('About & Contact', '/index.html'),
    ('Gentoo', 'https://www.gentoo.org'),
    ('NixOS', 'https://nixos.org/'),
    ('Pelican', 'http://getpelican.com/'),
    ('TUNA @ THU', 'https://tuna.moe/'),
)

# Social widget
SOCIAL = (
    ('github', 'https://github.com/KireinaHoro'),
    ('instagram', 'https://www.instagram.com/khjsteward/'),
    ('linkedin', 'https://www.linkedin.com/in/pengcheng-xu-6a241a9a/'),
    ('google scholar', 'https://scholar.google.com/citations?hl=de&user=h6ZFXyEAAAAJ'),
    ('orcid', 'https://orcid.org/0000-0002-2724-7893'),
)

DEFAULT_PAGINATION = 5

DEFAULT_METADATA = {
    'status': 'draft',
}

MARKDOWN = {
    'extensions': [f'markdown.extensions.{x}' for x in [
        'codehilite',
        'fenced_code',
        'meta',
        'attr_list',
        'md_in_html',
    ]] + [
        PhotoSwipeImageExtension(inputdir=PATH, outputdir=OUTPUT_PATH),
    ],
    'output_format': 'html5',
    'extension_configs': {
        'markdown.extensions.toc': {'title': 'Table of Contents'},
    }
}

# use index.html for personal introduction and place blog index at a separate place
INDEX_SAVE_AS = 'blog_index.html'

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# use short date format
DEFAULT_DATE_FORMAT = '%d/%m/%y %H:%M'

JINJA_GLOBALS = {
    "get_gallery_images": image_getter(PATH, OUTPUT_PATH),
}
