import os

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(os.path.dirname(__file__), 'test.db')

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