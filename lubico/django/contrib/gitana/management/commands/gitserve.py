# -*- coding: utf8 -*-
from django.http import Http404, HttpRequest

from lubico.django.contrib.gitana.views import GitanaShellView
import os
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.management.base import BaseCommand, CommandError
from lubico.django.contrib.gitana.exceptions import WrongGitCommandError
from lubico.django.contrib.gitana.models import Repository

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.0"
__license__ = "GNU Lesser General Public License"
__package__ = "lubico.django.contrib.gitana.management.commands"

class Command(BaseCommand):
    args = '<username> [<SSH_ORIGINAL_COMMAND>]'
    help = 'Wraps git-shell within controlled repository access check for certain users'
    cmd = None
    git_cmd = None
    git_repository = None
    current_user = None

    def handle(self, *args, **options):
        """
        expected environment SSH_ORIGINAL_COMMAND='git-receive-pack '\''username/repository.git'\'''
        or a 2nd argument that contains the same content as the environment variable
        """
        if not len(args):
            raise CommandError('No user specified')

        if len(args) == 2:
            self.cmd = args[1]

        username = args[0]
        try:
            request = HttpRequest()
            request.user = self.current_user = User.objects.get(username=username, is_active=True)
            if not self.cmd:
                self.cmd = os.environ.get('SSH_ORIGINAL_COMMAND', None)
            if self.cmd is None or len(self.cmd) == 0:
                raise WrongGitCommandError()

            (self.git_cmd, self.git_repository) = self.cmd.split(' ')

            view = GitanaShellView(
                request = request,
                uri = self.git_repository.replace("'", ''),
                service = self.git_cmd
            )
            if not view.get_backend().has_access():
                raise PermissionDenied('access')

            repository = view.get_repository()
            # TODO refactor this check into repository model
            repository_path = repository.full_path
            if not os.path.exists(repository_path): # TODO think about creation on the fly
                raise Repository.DoesNotExist

            git_cmd_new = "%s '%s'" % (self.git_cmd, repository_path)
            os.execvp('git', ['git', 'shell', '-c', git_cmd_new])

        except User.DoesNotExist:
            raise CommandError('[0] No such account %s found.' % username)
        except ValidationError, e:
            raise CommandError('[1] No such repository %s found.' % self.git_repository)
        except Http404 as e:
            raise CommandError('[2] No such repository %s found.' % self.git_repository)
        except PermissionDenied, e:
            raise CommandError('[3] You are not allowed to %s repository %s' % (e.message, self.git_repository))
        except WrongGitCommandError:
            raise CommandError('Do you think i\'m a login shell?')
        except Exception, e:
            raise CommandError('Live long and prosper. >> %s' % e)