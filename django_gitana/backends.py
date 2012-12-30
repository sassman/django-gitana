# -*- coding: utf-8 -*-
from wsgiref.validate import check_content_type

import os, subprocess, datetime, logging, re
from django.http import HttpResponse
from gitana.exceptions import WrongGitCommandError, GitBackendError

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.0"
__license__ = "GNU Lesser General Public License"
__package__ = "django_gitana"

log = logging.getLogger(__name__)

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

        args = ['/usr/lib/git-core/'+self.service, '--stateless-rpc'] + args_in + [self.repository.full_path]
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

"""
this was the backend adapter

class GitHttpBackendWrapper(GitBackend):

    def run_service(self, raw_data = None, args_in = []):
        env = dict(
            #GIT_PROJECT_ROOT        = repository.full_path.encode('latin1'),
            GIT_HTTP_EXPORT_ALL     = "1",
            GIT_COMMITTER_NAME      = self.requestor.get_full_name().encode('latin1'),
            GIT_COMMITTER_EMAIL     = self.requestor.email.encode('latin1'),
            #PATH_INFO               = path,
            PATH_TRANSLATED         = os.path.join(self.repository.full_path, self.path).encode('latin1'),
            #REQUEST_URI             = path,
            REQUEST_METHOD          = self.env.get('REQUEST_METHOD'),
            QUERY_STRING            = self.env.get('QUERY_STRING'),
            REMOTE_USER             = self.requestor.username.encode('latin1'),
            REMOTE_ADDR             = self.env.get('REMOTE_ADDR'),
            CONTENT_TYPE            = self.env.get('CONTENT_TYPE', ''),
            SERVER_PROTOCOL         = self.env.get('SERVER_PROTOCOL'),
            HTTP_CONTENT_ENCODING   = self.env.get('HTTP_CONTENT_ENCODING', ''),
        )

        cmd = '/usr/lib/git-core/git-http-backend'
        if self.service:
            cmd = [cmd, "/"+self.service]
        log.debug("going to launch git-http-backend from path %s with env=%s", cmd, env)

        log.debug("-------------------")
        log.debug(raw_data)
        log.debug("-------------------")

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=env)
        if raw_data and len(raw_data) :
            p.stdin.write(raw_data)

        body = p.stdout.read()
        log.debug(body)
        err = p.stderr.read()
        if len(err):
            log.error('git-http-backend returned the error "%s"' % err)
            raise GitBackendError(message=err)

        #body, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()

        head, body = body.split('\r\n\r\n')
        ct = ''
        r = re.compile(r'Content-Type: (?P<ct>[-\w]+/[-\w]+)')
        m = r.search(head)
        if m:
            ct = m.group(1)

        return HttpResponse(
            content = body,
            content_type = ct
        )
"""