# -*- coding: utf8 -*-

from django.conf.urls.defaults import *
from lubico.django.contrib.gitana.views import *
from lubico.django.contrib.gitana.decorators import logged_in_or_basicauth

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.0"
__license__ = "GNU Lesser General Public License"
__package__ = "django_gitana"

""" Urls that needs to be wrap
    taken form the git-http-backend sources:

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

urlpatterns = patterns('',

    url(GetTextFileView.get_url_pattern(),
        logged_in_or_basicauth(GetTextFileView.as_view()),
        name='gitana_get_text_file'
    ),
    url(GetInfoRefsView.get_url_pattern(),
        logged_in_or_basicauth(GetInfoRefsView.as_view()),
        name='gitana_get_info_refs'
    ),
    url(GetInfoPacksView.get_url_pattern(),
        logged_in_or_basicauth(GetInfoPacksView.as_view()),
        name='gitana_get_info_packs'
    ),
    url(GetLooseObjectView.get_url_pattern(),
        logged_in_or_basicauth(GetLooseObjectView.as_view()),
        name='gitana_get_loose_object'
    ),
    url(GetPackFileView.get_url_pattern(),
        logged_in_or_basicauth(GetPackFileView.as_view()),
        name='gitana_get_pack_file'
    ),
    url(GetIdxFileView.get_url_pattern(),
        logged_in_or_basicauth(GetIdxFileView.as_view()),
        name='gitana_get_idx_file'
    ),
    url(ServiceRpcView.get_url_pattern(),
        logged_in_or_basicauth(ServiceRpcView.as_view()),
        name='gitana_service_rpc'
    ),

)


