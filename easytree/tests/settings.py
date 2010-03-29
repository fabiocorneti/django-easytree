import os

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'easytree'
DATABASE_USER = 'easytree'
DATABASE_PASSWORD = 'easytree'

INSTALLED_APPS = (
    'silverbullet.geo',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'pound.accountmanager',
    'pound.accountmanager.tests',
    'burraco',
)
SITE_ID = 1

ROOT_URLCONF = ''

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'easytree',
    'easytree.tests',
)
SITE_ID = 1

# This merely needs to be present - as long as your test case specifies a
# urls attribute, it does not need to be populated.
ROOT_URLCONF = ''

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')