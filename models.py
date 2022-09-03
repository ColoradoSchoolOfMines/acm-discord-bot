'''
Models for reading/writing data to database files
Copyright (C) 2022 Keenan Buckley

This file is part of {PROJECT_NAME}.

{PROJECT_NAME} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
    MONGODB_URI = "MONGODB_URI"
    MONGODB_CERT_PATH = "MONGODB_CERT_PATH"


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
