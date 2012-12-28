# -*- coding: utf-8 -*-
from gitana.exceptions import WrongGitCommandError
import os, subprocess, datetime, logging, re

from django.core.exceptions import PermissionDenied
from django.views.generic.base import View
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from gitana.models import Repository

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "0.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = "gitana.views"

log = logging.getLogger(__name__)

def cache_wrapper(response, cache='forever'):
    if cache=='forever':
        now = datetime.date.today()
        response['Date'] = now
        response['Expires'] = now + datetime.timedelta(days=365)
        response['Cache-Control'] = 'public, max-age=31536000'
    elif not cache:
        response['Expires'] = 'Mon, 28 Mar 1983 00:00:00 CET'
        response['Pragma'] = 'no-cache'
        response['Cache-Control'] = 'no-cache'
    return response

class GitanaBaseMixin(View):

    kwarg_account_slug      = 'account_slug'
    kwarg_repository_slug   = 'repository_slug'
    kwarg_file_name         = 'file_name'
    kwarg_service           = 'service'

    def get_repository(self):
        repository_slug = self.kwargs.get(self.kwarg_repository_slug, None)
        repository = get_object_or_404(Repository,
            slug__iexact=repository_slug,
        )
        return repository

    def get_service(self):
        return self.kwargs.get(self.kwarg_service, None)

    def packet_write(self, string):
        return "%04x%s" % (len(string) + 4, string)

    def validate_service(self, service):
        if not service:
            raise WrongGitCommandError('Unsupported service: getanyfile')
        if service not in ['git-upload-pack', 'git-receive-pack', 'git-upload-archive']:
            raise WrongGitCommandError('Unsupported service: %s' % service)

    def deliver_local_file(self, content_type, cache=False):
        file_name = self.kwargs.get(self.kwarg_file_name, None)

        repository = self.get_repository()
        real_file = repository.full_path+'/'+file_name
        if not repository.can_review(self.request.user) or not os.path.exists(real_file):
            raise Http404

        lines = open(real_file).readlines()
        response = HttpResponse(
            lines,
            content_type=content_type
        )
        return cache_wrapper(response, cache)

    def run_service(self, content_type, args_in=[], content = ''):
        service = self.get_service()

        if not service or service not in ['git-upload-pack', 'git-receive-pack']:
            raise Http404

        repository = self.get_repository()

        if service == 'git-upload-pack' and not repository.can_review(self.request.user):
            return HttpResponseForbidden(content="Not your repository")
        elif service == 'git-receive-pack' and not repository.can_contribute(self.request.user):
            return HttpResponseForbidden(content="You got a read-only repository")

        args = ['/usr/lib/git-core/'+service, '--stateless-rpc'] + args_in + [repository.full_path]
        env = dict(
            GIT_COMMITTER_NAME=self.request.user.get_full_name().encode('latin1'),
            GIT_COMMITTER_EMAIL=self.request.user.email.encode('latin1')
        )

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, env=env)
        if self.request.method.lower() == 'post':
            ret = process.communicate(input=self.request.body)[0]
        else:
            ret = process.communicate()[0]
    #    log.write('this the process returns:\n')
    #    log.write(ret)
    #    content+=ret.encode('utf-8')
        content+=ret
        response = HttpResponse(
            content=content,
            content_type=content_type
        )
        return cache_wrapper(response, False)

    def dispatch(self, request, *args, **kwargs):
        log.debug("method entry %s", self)
        return super(GitanaBaseMixin, self).dispatch(request, *args, **kwargs)

    def git_http_backend_wrapper(self, path=""):
        service = self.get_service()
        self.validate_service(service)

        repository = self.get_repository()
        log.debug('repository=%s' % repository.slug)
        need_writing = service == 'git-receive-pack'
        log.debug('need_writing=%s' % need_writing)
        has_access = repository.can_review(self.request.user)
        log.debug('has_access(can review)=%s' % has_access)
        if need_writing:
            has_access = repository.can_contribute(self.request.user)

        log.debug('has_access=%s' % has_access)

        if not has_access:
            raise PermissionDenied("You're not allowed to perform that action")

        # TODO only experimental, is not working..
        #if not path:
        #    path = service

        # ok lets setup some git specials
        env = dict(
            #GIT_PROJECT_ROOT        = repository.full_path.encode('latin1'),
            GIT_HTTP_EXPORT_ALL     = "1",
            GIT_COMMITTER_NAME      = self.request.user.get_full_name().encode('latin1'),
            GIT_COMMITTER_EMAIL     = self.request.user.email.encode('latin1'),
            #PATH_INFO               = path,
            PATH_TRANSLATED         = os.path.join(repository.full_path, path).encode('latin1'),
            #REQUEST_URI             = path,
            REQUEST_METHOD          = self.request.META.get('REQUEST_METHOD'),
            QUERY_STRING            = self.request.META.get('QUERY_STRING'),
            REMOTE_USER             = self.request.user.username.encode('latin1'),
            REMOTE_ADDR             = self.request.META.get('REMOTE_ADDR'),
            CONTENT_TYPE            = self.request.META.get('CONTENT_TYPE', ''),
            SERVER_PROTOCOL         = self.request.META.get('SERVER_PROTOCOL'),
            HTTP_CONTENT_ENCODING   = self.request.META.get('HTTP_CONTENT_ENCODING', ''),
        )

        cmd = '/usr/lib/git-core/git-http-backend'
        log.debug("going to launch git-http-backend from path %s with env=%s", cmd, env)
        if service:
            cmd = [cmd, "/"+service]
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()
        log.debug("strerr: %s" % err)
        log.debug("strout: %s" % out)

        response = httpparse_str(out)
        body = response.read()
        head, body = body.split('\r\n\r\n')

        ct = ''
        r = re.compile(r'Content-Type: (?P<ct>[-\w]+/[-\w]+)')
        m = r.search(head)
        if m:
            ct = m.group(1)

        #log.debug("response body=%s" % body)
        #log.debug("content-type=%s" % ct)
        #log.debug("status=%s" % response.status)

        response = HttpResponse(
            content=body,
            status=response.status,
            content_type=ct
        )
        return response

class GitanaShellView(GitanaBaseMixin):
    cmd_pattern = r'^(?P<account_slug>[-\w]+)/(?P<repository_slug>[-\w]+)\.git'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_repository(self):
        uri = self.kwargs.get('uri', None)
        pattern = re.compile(self.cmd_pattern)
        result = pattern.match(uri)
        match_dict = result.groupdict()

        repository_slug = match_dict['repository_slug']
        account = User.objects.get(username = match_dict['account_slug'])

        repository = Repository.objects.filter(
            slug = repository_slug,
            account = account
        )
        if not repository.count():
            # at this point we want to create the repository silent
            repository = Repository(
                account = account,
                slug = repository_slug,
                name=repository_slug
            )
            repository.save()
        else:
            repository = repository.get()

        return repository

class GetInfoRefsView(GitanaBaseMixin):
    url_pattern = r'info/refs$'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        try:
            self.kwargs = kwargs
            service = request.GET.get(self.kwarg_service, None)
            self.kwargs[self.kwarg_service] = service
            return self.git_http_backend_wrapper(self.url_pattern[:len(self.url_pattern)-1])
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
    content_type = 'text/pain'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        self.kwargs = kwargs
        return self.deliver_local_file(request, self.content_type)

class GetLooseObjectView(GetTextFileView):
    url_pattern = r'(?P<file_name>objects/[0-9a-f]{2}/[0-9a-f]{38})$'
    content_type = 'application/x-git-loose-object'

class GetPackFileView(GetTextFileView):
    url_pattern = r'(?P<file_name>objects/pack/pack-[0-9a-f]{40}\.pack)$'

class GetIdxFileView(GetTextFileView):
    url_pattern = r'(?P<file_name>objects/pack/pack-[0-9a-f]{40}\.idx)$'

# TODO Not yet full tested
class GetInfoPacksView(GitanaBaseMixin):
    url_pattern = r'objects/info/packs$'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        log.debug("method entry %s", self.url_pattern)
        return self.git_http_backend_wrapper(self.url_pattern[:len(self.url_pattern)-1])

class ServiceRpcView(GitanaBaseMixin):
    url_pattern = r'(?P<service>git\-upload\-pack|git\-receive\-pack)$'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        self.kwargs = kwargs
        log.debug("method entry %s with service=%s", self.url_pattern, self.kwargs)
        return self.git_http_backend_wrapper()

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(ServiceRpcView, self).dispatch(request, *args, **kwargs)