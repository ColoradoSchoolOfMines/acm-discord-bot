""" Unit testing for the models.py script """

import os
import sys
import inspect

current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import models
import conftest

def test_load_dot_env(dir: str = models.STATIC_DIR):
    """ Assert that loaded .env contains all keys in models.ENVs """
    models.load_dot_env(dir=dir)
    assert os.path.isfile(f'{dir}/{models.ENV_FILENAME}'), f'{models.ENV_FILENAME} doesn\'t exist'
    for env in models.ENVs:
        assert (models.get_env_safe(env) is not None), f'Can\'t find env \"{env.value}\"'

def test_create_dot_env():
    """ Assert that a newly created .env contains all keys in models.ENVs """
    assert not os.path.isfile(f'{conftest.TEST_DIR}/{models.ENV_FILENAME}'), f'{conftest.TEST_DIR}/{models.ENV_FILENAME} already exists, unsafe to test with'
    test_load_dot_env(dir=conftest.TEST_DIR)
    assert os.path.isfile(f'{conftest.TEST_DIR}/{models.ENV_FILENAME}'), f'{conftest.TEST_DIR}/{models.ENV_FILENAME} was not created'

def test_create_dot_env_dir():
    """ Assert that models.create_dot_env() still works if directory already exists """
    models.create_dot_env(dir=conftest.TEST_DIR)
