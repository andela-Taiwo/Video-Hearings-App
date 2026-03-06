import os


APP_ENV = os.environ.get('APP_ENV', 'dev')

if APP_ENV in ('dev', 'production'):
    exec('from .{} import *'.format(APP_ENV))
