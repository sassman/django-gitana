# -*- coding: utf8 -*-

from django.conf.urls.defaults import *

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "0.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = ""

""" Urls that needs to be wrap

    {"GET", "/HEAD$", get_text_file},
    {"GET", "/info/refs$", get_info_refs},
    {"GET", "/objects/info/alternates$", get_text_file},
    {"GET", "/objects/info/http-alternates$", get_text_file},
    {"GET", "/objects/info/packs$", get_info_packs},
    {"GET", "/objects/[0-9a-f]{2}/[0-9a-f]{38}$", get_loose_object},
    {"GET", "/objects/pack/pack-[0-9a-f]{40}\\.pack$", get_pack_file},
    {"GET", "/objects/pack/pack-[0-9a-f]{40}\\.idx$", get_idx_file},

    {"POST", "/git-upload-pack$", service_rpc},
    {"POST", "/git-receive-pack$", service_rpc}
"""

#urlpatterns = patterns('',
#    (r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/(?P<file_name>HEAD|objects/info/http-alternates|objects/info/alternates)$',
#            'gitana.views.get_text_file'),
#    (r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/(?P<file_name>objects/[0-9a-f]{2}/[0-9a-f]{38})$',
#            'gitana.views.get_loose_object'),
#    (r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/info/refs$', 'gitana.views.get_info_refs'),
#    (r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/(?P<service>git\-upload\-pack|git\-receive\-pack)$', 'gitana.views.service_rpc'),
#)
