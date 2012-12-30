# -*- coding: utf8 -*-

import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.0"
__license__ = "GNU Lesser General Public License"
__package__ = "django_gitana.management.commands"

class Command(BaseCommand):
    args = '[<toggle>=ON]'
    help = 'Enables/Disables git push/pull over ssh'

    def handle(self, *args, **options):
        toggle = True
        if len(args) > 0 and args[0] != 'ON':
            toggle = False

        try:
            base_cmd = '--shell %(shell)s --home %(home)s %(username)s' % dict(
                username = settings.GITANA_USERNAME,
                home = settings.GITANA_USER_HOME_PATH,
                shell = '/bin/sh' if toggle else '/bin/false'
            )
            try:
                import pwd
                pw = pwd.getpwnam(settings.GITANA_USERNAME)
                uid = pw.pw_uid
                cmd = 'sudo usermod %s' % base_cmd
            except KeyError as e:
                cmd = 'sudo adduser --system %s' % base_cmd
            subprocess.call(cmd, shell = True)
            self.stdout.write('run command "%s"\n' % cmd)
        except Exception as e:
            raise CommandError('Something went wrong! %s' % (e.message))
