""" Models for reading/writing data to database files """

import dotenv
from enum import Enum
import os

dotenv.load_dotenv("static/.env")  # load all the variables from the .env file

class ENVs(Enum):
    """Defines env variables that should be present in a .env file accessable to the script """
    TOKEN = "TOKEN"
    DEBUG_TOKEN = "DEBUG_TOKEN"
    DEBUG_GUILDS = "DEBUG_GUILDS"


def get_env_safe(key: ENVs):
    """Get variable from .env and assert that it was found before resuming program

    Args:
        key (ENVs): enum associated to the enviromental variable

    Returns:
        value of the enviromental variable
    """
    value = os.getenv(key.value)
    assert(value is not None), f'Can\'t find token \"{key.value}\" and/or \".env\"'
    return value
