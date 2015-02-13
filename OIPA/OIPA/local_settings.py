DEBUG = True
ADMINS = []
JENKINS_TASKS = []
PROJECT_APPS = []
STATIC_ROOT = '~/static/'
STATIC_URL = 'static/'
LOGGING = []
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.mysql',
        'NAME': 'new_mohinga',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}


