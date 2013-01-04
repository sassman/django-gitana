# -*- coding: utf-8 -*-

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = "lubico.django.contrib.gitana"

import re
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

class SSHPublicKeyValidator(RegexValidator):
    regex = re.compile(r'^ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3} ([^@]+@[^@]+)$', re.IGNORECASE)
    message = _(u'Enter a valid ssh public key.')
