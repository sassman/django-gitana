# -*- coding: utf-8 -*-

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = "lubico.django.contrib.gitana"

class WrongGitCommandError(Exception):
    pass
class NoValidRepository(Exception):
    pass
class NoValidAccount(Exception):
    pass
class GitBackendError(Exception):
    pass