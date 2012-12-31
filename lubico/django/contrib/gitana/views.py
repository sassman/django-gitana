# -*- coding: utf-8 -*-
from lubico.django.contrib.gitana.exceptions import WrongGitCommandError
import os, subprocess, datetime, logging, re

from django.core.exceptions import PermissionDenied
from django.views.generic.base import View
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.views.decorators.gzip import gzip_page
from lubico.django.contrib.gitana.models import Repository
from lubico.django.contrib.gitana.backends import GitStatelessHttpBackendWrapper

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.0"
__license__ = "GNU Lesser General Public License"
__package__ = "django_gitana"

log = logging.getLogger(__name__)

class GitanaBaseMixin(View):

    url_base_prefix         = r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git/'
    kwarg_account_slug      = 'account_slug'
    kwarg_repository_slug   = 'repository_slug'
    kwarg_file_name         = 'file_name'
    kwarg_service           = 'service'

    @classmethod
    def get_url_pattern(cls):
        return GitanaBaseMixin.url_base_prefix + cls.url_pattern

    def get_account(self):
        """
        return the account that is associated with the given repository, or 404
        """
        account_slug = self.kwargs.get(self.kwarg_account_slug, None)
        return get_object_or_404(User, username__iexact = account_slug)

    def get_repository(self):
        """
        return the repository for the given slug and account, or 404
        """
        repository_slug = self.kwargs.get(self.kwarg_repository_slug, None)
        account = self.get_account()
        repository = get_object_or_404(Repository, slug__iexact = repository_slug, account = account)
        return repository

    def get_service(self):
        """
        return the git service that is requested
        """
        return self.kwargs.get(self.kwarg_service, self.request.GET.get(self.kwarg_service, None))

    def get_backend(self):
        """
        return git backend that can handle the serives and the requests
        """
        return GitStatelessHttpBackendWrapper(
            self.get_repository(),
            self.request.user,
            self.get_service(),
        )

class GitanaShellView(GitanaBaseMixin):
    cmd_pattern = r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        uri = self.kwargs.get('uri', None)
        pattern = re.compile(self.cmd_pattern)
        result = pattern.match(uri)
        match_dict = result.groupdict()

        self.kwargs[self.kwarg_account_slug] = match_dict['account_slug']
        self.kwargs[self.kwarg_repository_slug] = match_dict['repository_slug']

class GetInfoRefsView(GitanaBaseMixin):
    url_pattern = r'info/refs$'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        try:
            self.kwargs = kwargs
            return self.get_backend().get_info_refs()
        except WrongGitCommandError,e:
            log.exception(e.message, e)
            return HttpResponseForbidden(content=e.message)
        except Exception, e:
            log.exception(e)
            raise Http404()

class GetTextFileView(GitanaBaseMixin):
    """
    delivers a static file from the git repository to the requestor
    """
    url_pattern = r'(?P<file_name>HEAD|objects/info/http-alternates|objects/info/alternates)$'
    content_type = 'text/plain; charset=utf-8'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        self.kwargs = kwargs
        return self.get_backend().deliver_local_file(
            self.kwargs.get('file_name', None),
            self.content_type
        )

    @gzip_page
    def dispatch(self, request, *args, **kwargs):
        return super(GetTextFileView, self).dispatch(request, *args, **kwargs)

class GetLooseObjectView(GetTextFileView):
    url_pattern = r'(?P<file_name>objects/[0-9a-f]{2}/[0-9a-f]{38})$'
    content_type = 'application/x-git-loose-object'

class GetPackFileView(GetTextFileView):
    url_pattern = r'(?P<file_name>objects/pack/pack-[0-9a-f]{40}\.pack)$'
    content_type = 'application/x-git-packed-objects'

class GetIdxFileView(GetTextFileView):
    url_pattern = r'(?P<file_name>objects/pack/pack-[0-9a-f]{40}\.idx)$'
    content_type = 'application/x-git-packed-objects-toc'

class GetInfoPacksView(GitanaBaseMixin):
    url_pattern = r'objects/info/packs$'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        return self.get_backend().get_objects_info_packs()

    @gzip_page
    def dispatch(self, request, *args, **kwargs):
        return super(GetInfoPacksView, self).dispatch(request, *args, **kwargs)

class ServiceRpcView(GitanaBaseMixin):
    url_pattern = r'(?P<service>git\-upload\-pack|git\-receive\-pack)$'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        self.kwargs = kwargs
        return self.get_backend().run_service(request.body)

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(ServiceRpcView, self).dispatch(request, *args, **kwargs)