# -*- coding: utf8 -*-

from setuptools import setup

version = '1.0.0'

setup(
    name = 'django-gitana',
    version = version,
    author = 'Sven Aßmann',
    author_email='sven.assmann@lubico.biz',
    description = "Git repository management app for django",
    keywords = 'git django vcs repository-management git-web git-ssh',
    url='http://lubico.biz',
    license='LICENSE.txt',
    packages = [
        'django_gitana',
        'django_gitana.management',
        'django_gitana.management.commands',
    ],
    long_description = open('README.txt').read(),
    install_requires=[
        'setuptools',
        'Django >= 1.4.1',
        'lockfile >= 0.9.1',
    ],
)
