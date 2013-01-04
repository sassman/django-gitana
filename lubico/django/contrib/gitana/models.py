# -*- coding: utf8 -*-

import sys, os, shutil, subprocess
from lubico.django.contrib.gitana.validators import SSHPublicKeyValidator
from lockfile import FileLock
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.sites.models import Site

__author__ = 'sassman <sven.assmann@lubico.biz>'
__version__ = "1.0.1"
__license__ = "GNU Lesser General Public License"
__package__ = "lubico.django.contrib.gitana"

if not getattr(settings, 'ROOT_PATH', False):
    raise ImproperlyConfigured('ROOT_PATH is not configured, please set ROOT_PATH = os.path.dirname(os.path.abspath(__file__)) to settings.py')

if not getattr(settings, 'GITANA_USERNAME', False):
    raise ImproperlyConfigured('GITANA_USERNAME is not configured, please set GITANA_USERNAME = "git" in settings.py')

if not getattr(settings, 'GITANA_USER_HOME_PATH', False):
    raise ImproperlyConfigured('GITANA_USER_HOME_PATH is not configured, please set GITANA_USER_HOME_PATH = "/home/git" in settings.py')

if not getattr(settings, 'GITANA_REPOSITORY_ROOT', False):
    raise ImproperlyConfigured('GITANA_REPOSITORY_ROOT is not configured, please set e.g. GITANA_REPOSITORY_ROOT = "/home/git/gitana_repos"')

if not getattr(settings, 'GITANA_SITE_ID', False):
    raise ImproperlyConfigured("GITANA_SITE_ID is not valid or sites app not configured.")

if not getattr(settings, 'GITANA_GIT_BIN_PATH', False):
    raise ImproperlyConfigured('GITANA_GIT_BIN_PATH is not valid or e.g. GITANA_GIT_BIN_PATH = "/usr/bin/git"')

if not getattr(settings, 'GITANA_GIT_REMOTE', False):
    raise ImproperlyConfigured('GITANA_GIT_REMOTE is not configured e.g. GITANA_GIT_REMOTE = "origin"')

class Repository(models.Model):
    account         = models.ForeignKey(User)
    contributors    = models.ManyToManyField(User, related_name='contributors', null=True, blank=True)
    reviewers       = models.ManyToManyField(User, related_name='reviewers', null=True, blank=True)

    name            = models.CharField(max_length=255)
    slug            = models.SlugField()

    modified        = models.DateTimeField(auto_now=True)
    created         = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ( ('account', 'slug'),)
        verbose_name_plural = _('repositories')

    def __unicode__(self):
        return self.repository_name

    @property
    def git_remote_add(self):
        return "git remote add %(remote)s %(url)s" % dict(url=self.full_ssh_url, remote = settings.GITANA_GIT_REMOTE)

    @property
    def physical_name(self):
        return '%s.git' % self.slug

    @property
    def repository_name(self):
        return '%s/%s' % (self.account.username, self.physical_name)

    @property
    def root_path(self):
        return getattr(settings, 'GITANA_REPOSITORY_ROOT', False)

    @property
    def full_path(self):
        return os.path.abspath(os.path.join(self.root_path, self.repository_name))

    @property
    def absolute_scope_path(self):
        return os.path.abspath(os.path.join(self.root_path, self.account.username))

    @property
    def full_url(self):
        urls = self.full_ssh_url
        urls += " \n or "
        urls += self.full_http_url
        return urls

    @property
    def full_http_url(self):
        site = Site.objects.get(id = settings.GITANA_SITE_ID)
        try:
            path = reverse('gitana_get_info_refs', kwargs=dict(
                account_slug=self.account.username,
                repository_slug=self.slug,
            ))
            path = path.replace('/info/refs', '')
            return "%s://%s%s" % ('https', site.domain, path)
        except:
            return ''

    @property
    def full_ssh_url(self):
        site = Site.objects.get(id = settings.GITANA_SITE_ID)
        return "%s@%s:%s" % (settings.GITANA_USERNAME, site.domain, self.repository_name)

    def save(self, *args, **kwargs):
        try:
            if not os.path.exists(self.full_path):
                os.umask(0002)
                os.makedirs(self.full_path)
                subprocess.check_call("%s init --bare '%s'" % (settings.GITANA_GIT_BIN_PATH, self.full_path), shell=True)
        except OSError as e:
            raise ValidationError(e)
            #raise e
        super(Repository, self).save(*args, **kwargs)

    def delete(self, using=None):
        if os.path.exists(self.full_path):
            shutil.rmtree(self.full_path)
        super(Repository, self).delete(using)

    def can_contribute(self, user):
        return user == self.account or user in self.contributors.all()

    def can_review(self, user):
        return self.can_contribute(user) or user in self.reviewers.all()

class UserKey(models.Model):
    user = models.ForeignKey(User)
    comment = models.CharField(max_length=255, null=True, blank=True)
    pub = models.TextField(null=False, blank=False, validators=[SSHPublicKeyValidator()])

    class Meta:
        permissions = (
            ("my_change_user_key", "Can change only his own keys"),
            ("my_delete_user_key", "Can delete only his own keys"),
            ("my_add_user_key",    "Can add only his own keys"),
        )

    def __unicode__(self):
        c = self.comment
        if not c:
            p = self.pub.split(' ')
            c = len(p) > 2 is p[2] or p[0]
            c = "%s@%s" % (self.user, c)
        return c

    def save(self, force_insert=False, force_update=False, using=None):
        super(UserKey, self).save(force_insert, force_update, using)
        template = 'command="%(python_bin)s %(root)s/manage.py gitserve %(user)s",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty %(key)s\n'
        file = '%(home_path)s/.ssh/authorized_keys' % dict(home_path = settings.GITANA_USER_HOME_PATH)
        file_bak = '%(home_path)s/.ssh/authorized_keys.bak' % dict(home_path = settings.GITANA_USER_HOME_PATH)
        python_bin = getattr(settings, 'GITANA_VIRTUAL_ENV_PYTHON_BIN', sys.executable)
        with FileLock(file):
            os.rename(file, file_bak)
            f_keys = open(file, 'w+')
            for key in UserKey.objects.all():
                f_keys.write(template % dict(
                    python_bin = python_bin,
                    user=key.user.username,
                    key=key.pub,
                    root=settings.ROOT_PATH
                ))
