"""
This module is called after project is created.

It does the following:
1. Generates and saves random secret key
2. Prints further instructions

A portion of this code was adopted from Django's standard crypto functions and
utilities, specifically:
https://github.com/django/django/blob/master/django/utils/crypto.py

And from pydanny's cookiecutter-django:
https://github.com/pydanny/cookiecutter-django

"""

import os
import secrets
import shutil
import string

# CHANGEME mark
CHANGEME = '__CHANGEME__'

# Get the root project directory
PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
PROJECT_NAME = '{{ cookiecutter.project_name }}'

# Messages
PROJECT_SUCCESS = """
Your project {0} is created.
Now you can start working on it:

    cd {0}
"""

DATABASE_NAME = '{{ cookiecutter.database }}'


def _get_random_string(length=50):
    """
    Returns a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits

    >>> secret = _get_random_string()
    >>> len(secret)
    50

    """
    punctuation = string.punctuation.replace(
        '"', '',
    ).replace(
        "'", '',
    ).replace(
        '\\', '',
    ).replace(
        '$', '',  # see issue-271
    )

    chars = string.digits + string.ascii_letters + punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))


def _create_secret_key(config_path):
    # Generate a SECRET_KEY that matches the Django standard
    secret_key = _get_random_string()

    with open(config_path, 'r+') as config_file:
        # Replace CHANGEME with SECRET_KEY
        file_contents = config_file.read().replace(CHANGEME, secret_key, 1)

        # Write the results to the file:
        config_file.seek(0)
        config_file.write(file_contents)
        config_file.truncate()


def _database_config(config_path):
    common = """# === Database ===

# These variables are special, since they are consumed
# by both django and postgres docker image.
# Cannot be renamed if you use postgres in docker.
# See: https://hub.docker.com/_/postgres
    """

    db_config = f"""# === Mysql ===
MYSQL_DB={PROJECT_NAME}
MYSQL_USER={PROJECT_NAME}
MYSQL_PASSWORD={PROJECT_NAME}
"""
    db_port = '3306'
    db_common_settings_config = """{
    # PostgresSql
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': config('POSTGRES_DB'),
    #     'USER': config('POSTGRES_USER'),
    #     'PASSWORD': config('POSTGRES_PASSWORD'),
    #     'HOST': config('DJANGO_DATABASE_HOST'),
    #     'PORT': config('DJANGO_DATABASE_PORT', cast=int),
    #     'CONN_MAX_AGE': config('CONN_MAX_AGE', cast=int, default=60),
    #     'OPTIONS': {
    #         'connect_timeout': 10,
    #         'options': '-c statement_timeout=15000ms',
    #     },
    # },
    # Mysql
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': config('MYSQL_DB'),
        'USER': config('MYSQL_USER'),
        'PASSWORD': config('MYSQL_PASSWORD'),
        'HOST': config('DJANGO_DATABASE_HOST'),
        'PORT': config('DJANGO_DATABASE_PORT', cast=int),
        'CONN_MAX_AGE': config('CONN_MAX_AGE', cast=int, default=60),
        'OPTIONS': {
            'autocommit': True,
            'use_oure': True,
            'init_command': "SET GLOBAL connect_timeout=10000;SET GLOBAL interactive_timeout=15000;"
        },
    },
}"""
    if DATABASE_NAME == 'postgresql':
        db_config = f"""# === Postgres ===
POSTGRES_DB={PROJECT_NAME}
POSTGRES_USER={PROJECT_NAME}
POSTGRES_PASSWORD={PROJECT_NAME}
"""
        db_port = '5432'
        db_common_settings_config = """{
    # PostgresSql
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('DJANGO_DATABASE_HOST'),
        'PORT': config('DJANGO_DATABASE_PORT', cast=int),
        'CONN_MAX_AGE': config('CONN_MAX_AGE', cast=int, default=60),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=15000ms',
        },
    },
    # Mysql
    # 'default': {
    #     'ENGINE': 'mysql.connector.django',
    #     'NAME': config('MYSQL_DB'),
    #     'USER': config('MYSQL_USER'),
    #     'PASSWORD': config('MYSQL_PASSWORD'),
    #     'HOST': config('DJANGO_DATABASE_HOST'),
    #     'PORT': config('DJANGO_DATABASE_PORT', cast=int),
    #     'CONN_MAX_AGE': config('CONN_MAX_AGE', cast=int, default=60),
    #     'OPTIONS': {
    #         'autocommit': True,
    #         'use_oure': True,
    #         'init_command': "SET GLOBAL connect_timeout=10000;SET GLOBAL interactive_timeout=15000;"
    #     },
    # },
}"""

    db_config2 = f"""# Used only by django:
DJANGO_DATABASE_HOST=localhost
DJANGO_DATABASE_PORT={db_port}
"""

    with open(config_path, 'r+') as config_file:
        # file_contents = config_file.read().replace('__DATABASE_PORT__', db_port, 1)
        # Write the results to the file:
        # config_file.seek(0)
        # config_file.write(file_contents)
        config_file.writelines(common)
        config_file.writelines(db_config)
        config_file.writelines(db_config2)
        config_file.truncate()

    common_settings_config = os.path.join(
        PROJECT_DIRECTORY,
        'server',
        'settings',
        'components',
        'common.py',
    )
    with open(common_settings_config, 'r+') as common_settings_config_file:
        file_contents = common_settings_config_file.read()\
            .replace('\'__DATABASES_CONFIG__\'', db_common_settings_config, 1)
        common_settings_config_file.seek(0)
        common_settings_config_file.write(file_contents)
        common_settings_config_file.truncate()


def print_futher_instuctions():
    """Shows user what to do next after project creation."""
    print(PROJECT_SUCCESS.format(PROJECT_NAME))  # noqa: WPS421


def copy_local_configuration():
    """
    Handler to copy local configuration.

    It is copied from ``.template`` files to the actual files.
    """
    secret_template = os.path.join(
        PROJECT_DIRECTORY, 'config', '.env.template',
    )
    secret_config = os.path.join(
        PROJECT_DIRECTORY, 'config', '.env',
    )
    shutil.copyfile(secret_template, secret_config)
    _create_secret_key(secret_config)

    # database config
    _database_config(secret_config)

    # Local config:
    local_template = os.path.join(
        PROJECT_DIRECTORY,
        'server',
        'settings',
        'environments',
        'local.py.template',
    )
    local_config = os.path.join(
        PROJECT_DIRECTORY,
        'server',
        'settings',
        'environments',
        'local.py',
    )
    shutil.copyfile(local_template, local_config)


copy_local_configuration()
print_futher_instuctions()
