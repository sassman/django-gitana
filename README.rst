=============	
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

::

    pip install -e git://github.com/lubico-business/django-gitana.git#egg=django-gitana

important runtime especially
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

to be able to manage user ssh public keys it is necessary to run as user that is configured ``GITANA_USERNAME`` usually
 you use ``git``. A sample apache2 vhost configuration can looks like the following:

::

    <VirtualHost *:80>

        ServerName code.yoursite.com
        ServerAlias *.yoursite.com

        DocumentRoot /var/www/code.yoursite.com/code/webroot
        CustomLog /var/www/code.yoursite.com/code/data/logs/access.log combined

        WSGIPassAuthorization On
        WSGIApplicationGroup %{GLOBAL}
        WSGIDaemonProcess yoursite.com threads=10 user=git python-path=/var/www/code.yoursite.com/code:/var/www/code.yoursite.com/venv/lib/python2.7/site-packages
        WSGIProcessGroup yoursite.com
        WSGIScriptAlias / /var/www/code.yoursite.com/code/wsgi.py

    </VirtualHost>

the important thing is ``WSGIDaemonProcess user=git`` that enables your wsgi application to manage ssh keys and will
 retain the correct permissions on file system to all created repositories

python-path is only relevant if you going to establish your application together with a python virtual environment.

Getting Started
---------------

add to your django ``settings.py`` to your ``INSTALLED_APPS`` the following:
::

    INSTALLED_APPS = (
        ...
        'lubico.django.contrib.gitana',
    )

don't forget to sync db:
::

    python manage.py syncdb


enable git push and pull over http(s)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
add the following to your ``urls.py`` if you want to enable git operations over http

::

    urlpatterns += patterns('',
        url('', include('lubico.django.contrib.gitana.urls')),
    )

Note: it is highly recommended to use https instead of using http, only then your passwords are transmitted over a
secure socket connection.


enable git push and pull over ssh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
setup an user unix accout to push as wrapper:
::

    sudo adduser --home /home/git --shell /bin/sh --system git

or do it django style via manage.py:
::

    python manage.py toggle_ssh_push_and_pull

configure gitana app
^^^^^^^^^^^^^^^^^^^^
::

    GITANA_USERNAME = 'git'

Configures the unix user account that is used to handle ssh based push and ssh key authorized keys files

----

::

    GITANA_SITE_ID = SITE_ID

Configures the Site Id that is configured for gitana. Normally this is SITE_ID but this can differ from you normal site
layout. e.g. your main page is hosted on http://yourpage.com but gitana should work with http://code.yourpage.com

----

:: 

    GITANA_REPOSITORY_ROOT = '/home/git/repos/'

Configures the root folder for storing the git repositories.

----

:: 

    GITANA_USER_HOME_PATH = '/home/git/'

configures the home directory of your GITANA_USERNAME account. Normally this is /home/git since GITANA_USERNAME='git'

----

:: 

    GITANA_GIT_BIN_PATH = '/usr/bin/git'

configures the binary path of git

----

:: 

    GITANA_GIT_REMOTE = 'origin'

configures the default remote name

----

:: 

    GITANA_VIRTUAL_ENV_PYTHON_BIN = os.path.abspath(os.path.join(ROOT_PATH, '../.venv/bin/python'))

Note: optional, default is sys.executable
configures the path of python binary if your setup is wrapped within a virual environment

----

:: 

    GITANA_GIT_LIB_PATH = '/usr/lib/git-core/'

Note: optional, default is as shown
configures the path of git bin utils


Thanks to
---------

special thanks to all the people that builds git and especial git-http-backend cgi that comes along with git sources