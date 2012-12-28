# -*- coding: utf-8 -*-

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "0.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = "gitana.validators"

import re
from django.core.validators import RegexValidator

class SSHPublicKeyValidator(RegexValidator):
    regex = re.compile(r'^ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3} ([^@]+@[^@]+)$', re.IGNORECASE)