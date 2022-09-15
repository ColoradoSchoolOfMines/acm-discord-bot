'''
Models for reading/writing data to database files

This is free and unencumbered software released into the public domain.
For more information, please refer to <http://unlicense.org/>
'''

import dotenv
from enum import Enum
import os

dotenv.load_dotenv("static/.env")  # load all the variables from the .env file

class ENVs(Enum):
    """Defines env variables that should be present in a .env file accessable to the script """
    TOKEN = "TOKEN"
    DEBUG_TOKEN = "DEBUG_TOKEN"
    DEBUG_GUILDS = "DEBUG_GUILDS"


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
