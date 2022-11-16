import inspect
import os
import shutil
import sys
import pytest

current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import cogs.roles as roles

TEST_DIR = "temp_testing"

@pytest.fixture(scope="module", autouse=True)
def my_fixture():
    # Initialization
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.mkdir(TEST_DIR)
    roles.RoleTable.DBFILE = f'{TEST_DIR}/database.db'

    yield pytest.param
    
    #Teardown
    shutil.rmtree(TEST_DIR)