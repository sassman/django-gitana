# -*- coding: utf8 -*-

from gitana.views import GitanaShellView
import os
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.management.base import BaseCommand, CommandError
from gitana.exceptions import WrongGitCommandError
from gitana.models import Repository

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.0"
__license__ = "GNU Lesser General Public License"
__package__ = "django_gitana.management.commands"

class Command(BaseCommand):
    args = '<username> [<SSH_ORIGINAL_COMMAND>]'
    help = 'Wraps git-shell within controlled repository access check for certain users'
    cmd = None
    current_user = None

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError('No user specified')

        cmd = None
        if len(args) == 2:
            cmd = args[1]

        username = args[0]
        try:
            self.current_user = user = User.objects.filter(username=username, is_active=True).get()
            # expected environment SSH_ORIGINAL_COMMAND='git-receive-pack '\''username/repository.git'\'''
            if not cmd:
                cmd = os.environ.get('SSH_ORIGINAL_COMMAND', None)
            if cmd is None or len(cmd) == 0:
                raise WrongGitCommandError()

            (git_cmd, cmd_args) = cmd.split(' ')

            view = GitanaShellView(
                uri = cmd_args.replace("'", ''),
                service = git_cmd
            )

            repository = view.get_repository()
            if repository is None:
                raise Repository.DoesNotExist

            can_review = repository.can_review(user)
            if git_cmd == 'git-receive-pack':   # client do: git push
                if not repository.can_contribute(user):
                    if can_review:
                        raise PermissionDenied('contribute')
                    raise Repository.DoesNotExist
            elif git_cmd in ('git-upload-pack', 'git-upload-archive'):  # client do: git pull
                if not can_review:
                    raise Repository.DoesNotExist
            else:
                raise WrongGitCommandError()

            repository_path = repository.full_path
            if not os.path.exists(repository_path): # TODO think about creation on the fly
                raise Repository.DoesNotExist

            git_cmd_new = '%s \'%s\'' % (git_cmd, repository_path)
            #cmd = 'git shell -c \'%s \'\'%s\'\'\'' % (git_cmd, '.')
            #subprocess.Popen(cmd, stdout=self.stdout, stderr=self.stdout, cwd=repository_path).communicate()
            os.execvp('git', ['git', 'shell', '-c', git_cmd_new])

        except User.DoesNotExist:
            raise CommandError('User "%s" does not exist' % username)
        except ValidationError, e:
            raise CommandError('[1] No such repository %s found. Please visit www.gitploy.com/repositories' % cmd_args)
        except Repository.DoesNotExist:
            raise CommandError('[2] No such repository %s found. Please visit www.gitploy.com/repositories' % cmd_args)
        except User.DoesNotExist:
            raise CommandError('2: No matched account for %s found' % cmd_args)
        except PermissionDenied, e:
            raise CommandError('You are not allowed to %s repository "%s"' % (e.message, repository.repository_name))
        except WrongGitCommandError:
            raise CommandError('Brutality! Do you think i\'m a login shell?')
        except Exception, e:
            raise CommandError('Heroic Brutality! %s' % e)

        #self.stdout.write('User "%s" accepted\n' % user.username)
