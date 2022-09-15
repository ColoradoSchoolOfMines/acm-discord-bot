'''
Unit testing for the models.py script

This is free and unencumbered software released into the public domain.
For more information, please refer to <http://unlicense.org/>
'''

import os
import sys
import inspect
import shutil

current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import models

def test_load_dot_env(dir: str = models.ENV_DIR):
    """ Assert that loaded .env contains all keys in models.ENVs """
    models.load_dot_env(dir=dir)
    assert os.path.isfile(f'{dir}/.env'), f'.env '
    for env in models.ENVs:
        assert (models.get_env_safe(env)
                is not None), f'Can\'t find env \"{env.value}\"'


def test_create_dot_env():
    """ Assert that a newly created .env contains all keys in models.ENVs """
    TEST_DIR = "temp_testing"
    assert not os.path.isfile(
        f'{TEST_DIR}/.env'), f'{TEST_DIR}/.env already exists, unsafe to test with'
    test_load_dot_env(dir=TEST_DIR)
    assert os.path.isfile(
        f'{TEST_DIR}/.env'), f'{TEST_DIR}/.env was not created'
    shutil.rmtree(TEST_DIR)


def test_create_dot_env_dir():
    """ Assert that models.create_dot_env() still works if directory already exists """
    TEST_DIR = "temp_testing"
    os.mkdir(TEST_DIR)
    models.create_dot_env(dir=TEST_DIR)
    shutil.rmtree(TEST_DIR)
