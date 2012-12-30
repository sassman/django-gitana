# -*- coding: utf-8 -*-

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "0.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = "gitana.exceptions"

class WrongGitCommandError(Exception):
    pass
class NoValidRepository(Exception):
    pass
class NoValidAccount(Exception):
    pass
class GitBackendError(Exception):
    pass