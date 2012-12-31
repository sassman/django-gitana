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
    url='https://github.com/lubico-business/django-gitana',
    license='LICENSE.txt',
    packages = [
        'lubico',
        'lubico.django',
        'lubico.django.contrib',
        'lubico.django.contrib.gitana',
        'lubico.django.contrib.gitana.management',
        'lubico.django.contrib.gitana.management.commands',
    ],
    long_description = open('README.txt').read(),
    install_requires=[
        'setuptools',
        'Django >= 1.4.1',
        'lockfile >= 0.9.1',
    ],
)
