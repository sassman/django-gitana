django-gitana
=============

What's it
---------

django-gitana is a django application that allows to manage git (vcs) repositories within the django admin application.
It also provides a ssh and http push/pull implementation that allows to combine access control as common in django from
django auth app with git repositories.
Each repository has "reviewers" for read only access and "contributors" for read-write access to the repository.
The idea is to manage simple and safe closed repositories.

What's not
----------

a frontend to browse your git repository code like gitweb or gitosis.
It only provides you the "backend" to push, pull, clone etc. within django

Installation
------------

    pip install -e git://github.com/lubico-business/django-gitana.git#egg=django-gitana

Getting Started
---------------

add to your django `settings.py` to your `INSTALLED_APPS` the following:

    INSTALLED_APPS = (
        ...
        'lubico.django.contrib.gitana',
    )

don't forget to sync db:

    python manage.py syncdb

### enable git push over ssh

setup an user unix accout to push as wrapper:

    sudo adduser --home /home/git --shell /bin/sh --system git

or do it django style via manage.py:

    python manage.py toggle_ssh_push_and_pull

### configure gitana app

    GITANA_USERNAME = 'git'

Configures the unix user account that is used to handle ssh based push and ssh key authorized keys files


    GITANA_SITE_ID = SITE_ID

Configures the Site Id that is configured for gitana. Normally this is SITE_ID but this can differ from you normal site
layout. e.g. your main page is hosted on http://yourpage.com but gitana should work with http://code.yourpage.com


    GITANA_REPOSITORY_ROOT = '/home/git/repos/'

Configures the root folder for storing the git repositories.


    GITANA_USER_HOME_PATH = '/home/git/'

configures the home directory of your GITANA_USERNAME account. Normally this is /home/git since GITANA_USERNAME='git'


    GITANA_GIT_BIN_PATH = '/usr/bin/git'

configures the binary path of git


    GITANA_GIT_REMOTE = 'origin'

configures the default remote name


    GITANA_VIRTUAL_ENV_PYTHON_BIN = os.path.abspath(os.path.join(ROOT_PATH, '../.venv/bin/python'))

Note: optional, default is sys.executable
configures the path of python binary if your setup is wrapped within a virual environment


    GITANA_GIT_LIB_PATH = '/usr/lib/git-core/'

Note: optional, default is as shown
configures the path of git bin utils


Thanks to
---------

special thanks to all the guys that builds git and especial git-http-backend cgi that comes along with git sources