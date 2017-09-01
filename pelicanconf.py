#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'KireinaHoro'
SITENAME = 'KireinaHoro (jsteward) \'s place'
SITEURL = 'jsteward.moe'

PATH = 'content'

TIMEZONE = 'Asia/Shanghai'

DEFAULT_LANG = 'zh'

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
        ('Pelican', 'http://getpelican.com/'),
        ('Python.org', 'http://python.org/'),
        )

# Social widget
SOCIAL = (
        ('keybase', 'https://keybase.io/jsteward'),
        ('telegram', 'https://telegram.me/jsteward'),
        ('github', 'https://github.com/KireinaHoro'),
        ('twitter', 'https://twitter.com/KireinaHoro'),
        ('last.fm','http://www.last.fm/user/KireinaHoro'),
        )

DEFAULT_PAGINATION = 10

DEFAULT_METADATA = {
        'status': 'draft',
}

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
