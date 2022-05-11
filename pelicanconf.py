#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Pengcheng Xu'
SITENAME = 'Pengcheng Xu\'s Place'
SITEURL = 'http://localhost:8000'

import os
COMMIT = os.environ['COMMIT'][:7]

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
    ('Tsinghua University TUNA Association',
     'https://tuna.moe/'),
)

# Social widget
SOCIAL = (
    ('github', 'https://github.com/KireinaHoro'),
    ('linkedin', 'https://www.linkedin.com/in/pengcheng-xu-6a241a9a/'),
    ('telegram', 'https://telegram.me/jsteward'),
    ('twitter', 'https://twitter.com/KireinaHoro'),
    ('keybase', 'https://keybase.io/jsteward'),
)

DEFAULT_PAGINATION = 5

DEFAULT_METADATA = {
    'status': 'draft',
}

# use index.html for personal introduction and place blog index at a separate place
INDEX_SAVE_AS = 'blog_index.html'

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
