#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'KireinaHoro'
SITENAME = 'KireinaHoro (jsteward) \'s place'
SITEURL = 'jsteward.moe'

PATH = 'content'

TIMEZONE = 'Asia/Shanghai'

DEFAULT_LANG = 'en'

THEME = 'themes/built-texts'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
    ('About & Contact', '/pages/about-contact.html'),
    ('Gentoo', 'https://www.gentoo.org'),
    ('Pelican', 'http://getpelican.com/'),
    ('Tsinghua University TUNA Association',
     'https://tuna.moe/'),
)

# Social widget
SOCIAL = (
    ('github', 'https://github.com/KireinaHoro'),
    ('telegram', 'https://telegram.me/jsteward'),
    ('twitter', 'https://twitter.com/KireinaHoro'),
    ('keybase', 'https://keybase.io/jsteward'),
)

DEFAULT_PAGINATION = 5

DEFAULT_METADATA = {
    'status': 'draft',
}

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
