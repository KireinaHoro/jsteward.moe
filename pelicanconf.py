#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
from photoswipe_images import PhotoSwipeImageExtension

AUTHOR = 'Pengcheng Xu'
SITENAME = 'Pengcheng Xu'
SITEURL = 'http://localhost:8080'

import os
import sys

COMMIT = os.environ['COMMIT'][:7]

from pathlib import Path

PATH = 'content'

TIMEZONE = 'Asia/Shanghai'

DEFAULT_LANG = 'en'

THEME = 'theme'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

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
        PhotoSwipeImageExtension(inputdir=PATH),
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

# automatically scan photos for galleries
from PIL import Image
def get_gallery_images(gallery_id):
    print(f'>>> Scanning images for gallery {gallery_id}...')

    base_path = Path(PATH) / 'images' / 'gallery' / gallery_id
    if not base_path.exists():
        print(f'!!! Gallery path {base_path} does not exist!')
        sys.exit(1)

    images = []

    for file in sorted(base_path.glob("*.avif")):
        try:
            with Image.open(file) as img:
                width, height = img.size
        except Exception as e:
            print(f'!!! failed to open {file}: {e}; skipping...')
            continue

        print(f'... {file} ({width} x {height})')
        images.append({
            'name': file.stem,
            'width': width,
            'height': height,
        })

    print(f'>>> Done, added {len(images)} images')
    return images

JINJA_GLOBALS = {
    "get_gallery_images": get_gallery_images
}
