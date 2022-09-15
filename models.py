'''
Models for reading/writing data to database files

This is free and unencumbered software released into the public domain.
For more information, please refer to <http://unlicense.org/>
'''

import dotenv
from enum import Enum
import os
import logging

ENV_DIR = "static"

class ENVs(Enum):
    """Defines env variables that should be present in a .env file accessable to the script """
    TOKEN = "TOKEN"
    DEBUG_TOKEN = "DEBUG_TOKEN"
    DEBUG_GUILDS = "DEBUG_GUILDS"


def create_dot_env(dir: str=ENV_DIR):
    """Creates a new .env file with blank fields for each key in models.ENVs

    Args:
        dir (str): directory to create .env in. Defaults to models.ENV_DIR.
    """
    if not os.path.exists(dir):
        os.mkdir(dir)
    with open(f'{dir}/.env', 'w') as file:
        file.write("# Environmental variables for project")
        for env in ENVs:
            file.write(f'\n{env.value}=')


def load_dot_env(dir: str=ENV_DIR):
    """Loads a .env file. If none found, log a warning and create a new .env

    Args:
        dir (str): directory to load .env. Defaults to models.ENV_DIR.
    """
    if not os.path.isfile(f'{dir}/.env'):
        create_dot_env(dir=dir)
        logging.warning(
            f'No .env found in {dir}, created new one with blank fields')
    dotenv.load_dotenv(f'{dir}/.env')


def get_env_safe(key: ENVs, accept_empty=True):
    """Get variable from .env and assert that it was found before resuming program

    Args:
        key (ENVs): enum associated to the enviromental variable
        accept_empty (bool): whether to allow an empty env to be returned. Defaults to True.

    Returns:
        value of the enviromental variable
    """
    value = os.getenv(key.value)
    assert (value is not None), f'Can\'t find env \"{key.value}\"'
    if not accept_empty:
        assert (value != ""), f'The env \"{key.value}\" is unexpectedly empty'

    return value
