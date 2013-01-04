# -*- coding: utf-8 -*-
from wsgiref.validate import check_content_type

import os, subprocess, datetime, logging, re
from django.conf import settings
from django.http import HttpResponse, Http404
from lubico.django.contrib.gitana.exceptions import WrongGitCommandError, GitBackendError

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = "lubico.django.contrib.gitana"

log = logging.getLogger(__name__)

if not getattr(settings, 'GITANA_GIT_LIB_PATH', False):
    settings.GITANA_GIT_LIB_PATH = '/usr/lib/git-core/'

class GitBackend:

    repository  = None
    requestor   = None
    service     = None
    path        = None
    env         = None

    def __init__(self, repository, requestor, service = None):
        self.repository = repository
        self.requestor  = requestor
        self.service    = service

    def has_access(self):
        need_writing = self.service == 'git-receive-pack'
        has_access = self.repository.can_review(self.requestor)
        if need_writing:
            has_access = self.repository.can_contribute(self.requestor)
        return has_access

    def validate_service(self):
        if not self.service:
            raise WrongGitCommandError('Unsupported service: getanyfile')
        if self.service not in ['git-upload-pack', 'git-receive-pack', 'git-upload-archive']:
            raise WrongGitCommandError('Unsupported service: %s' % self.service)

    def packet_write(self, string):
        return "%04x%s" % (len(string) + 4, string)

    def packet_flush(self):
        return "%04x" % 0

    def run_service(self, raw_data = None, args_in = []):
        self.validate_service()
        pass

    def get_info_refs(self):
        args = ['--advertise-refs']
        return self.run_service(None, args)

    def deliver_local_file(self, file_name, content_type, cache=False):

        repository = self.repository
        real_file = os.path.abspath(os.path.join(repository.full_path, file_name))
        if self.has_access() or not os.path.exists(real_file):
            raise Http404

        lines = open(real_file).readlines()
        response = HttpResponse(
            lines,
            content_type=content_type
        )
        return self.cache_wrapper(response, cache)

    def get_objects_info_packs(self):
        repository = self.repository
        response = ""
        objects_path = os.path.join(repository.full_path, 'objects', 'pack')
        for file in os.listdir(objects_path):
            if file.endswith('.pack'):
                response += "P %s\n" % os.path.basename(file)
        response += "\n"
        return self.cache_wrapper(HttpResponse(
            content = response,
            content_type = 'text/plain; charset=utf-8'
        ), False)


    def cache_wrapper(self, response, cache='forever'):
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


class GitStatelessHttpBackendWrapper(GitBackend):

    def run_service(self, raw_data = None, args_in = []):
        self.validate_service()

        cmd = os.path.abspath(os.path.join(settings.GITANA_GIT_LIB_PATH, self.service))
        args = [cmd, '--stateless-rpc'] + args_in + [self.repository.full_path]
        env = dict(
            GIT_COMMITTER_NAME=self.requestor.get_full_name().encode('latin1'),
            GIT_COMMITTER_EMAIL=self.requestor.email.encode('latin1')
        )
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

        if raw_data and len(raw_data) :
            p.stdin.write(raw_data)

        body = p.stdout.read()
        log.debug(body)
        err = p.stderr.read()
        if len(err):
            log.error('%s returned the error "%s"' % (self.service, err))
            raise GitBackendError(message=err)

        return HttpResponse(
            content = body,
            content_type = 'application/x-%s-result' % self.service
        )

    def get_info_refs(self):
        service = self.service
        repository = self.repository
        content_type = 'application/x-%s-advertisement' % service

        response = GitBackend.get_info_refs(self)
        response2 = HttpResponse(
            content_type = content_type,
            content = self.packet_write("# service=%s\n" % service)
                      + self.packet_flush()
                      + response.content
        )
        log.debug(response2)
        return self.cache_wrapper(response2, False)