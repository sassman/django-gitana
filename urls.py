# -*- coding: utf8 -*-

from django.conf.urls.defaults import *
from gitana.views import *
from gitana.decorators import logged_in_or_basicauth

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

"""
url(r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/(?P<file_name>HEAD|objects/info/http-alternates|objects/info/alternates)$',
    'gitana.views.get_text_file'
),
(r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/(?P<file_name>objects/[0-9a-f]{2}/[0-9a-f]{38})$',
        'gitana.views.get_loose_object'),
(r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/info/refs$', 'gitana.views.get_info_refs'),
(r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/(?P<service>git\-upload\-pack|git\-receive\-pack)$', 'gitana.views.service_rpc'),
"""

gitana_url_prefix = r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/'

urlpatterns = patterns(gitana_url_prefix,

    url(GetTextFileView.url_pattern,
        logged_in_or_basicauth(GetTextFileView.as_view()),
        name='gitana_get_text_file'
    ),
    url(GetInfoRefsView.url_pattern,
        logged_in_or_basicauth(GetInfoRefsView.as_view()),
        name='gitana_get_info_refs'
    ),
    url(GetInfoPacksView.url_pattern,
        logged_in_or_basicauth(GetInfoPacksView.as_view()),
        name='gitana_get_info_packs'
    ),
    url(GetLooseObjectView.url_pattern,
        logged_in_or_basicauth(GetLooseObjectView.as_view()),
        name='gitana_get_loose_object'
    ),
    url(GetPackFileView.url_pattern,
        logged_in_or_basicauth(GetPackFileView.as_view()),
        name='gitana_get_pack_file'
    ),
    url(GetIdxFileView.url_pattern,
        logged_in_or_basicauth(GetIdxFileView.as_view()),
        name='gitana_get_idx_file'
    ),
    url(ServiceRpcView.url_pattern,
        logged_in_or_basicauth(ServiceRpcView.as_view()),
        name='gitana_service_rpc'
    ),

)


