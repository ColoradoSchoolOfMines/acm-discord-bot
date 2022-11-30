""" Unit testing for the roles.py cog """

import os
import sqlite3
import sys
import inspect
import time
import discord

current_dir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import cogs.roles as roles
import conftest

### Role Cog Testing
def test_active_tables():
    cog = roles.Roles(discord.Bot())

    # table creation
    cog.add_active_table(1)
    assert cog.find_active_table(1) != None

    # duplicate table
    cog.add_active_table(1)
    assert len(cog.active_tables) == 1
    assert cog.find_active_table(1) != None

    # second table
    cog.add_active_table(2)
    assert len(cog.active_tables) == 2
    assert cog.find_active_table(2) != None

### Role Table Testing
def test_table_add():
    test_start_time = time.time()
    table = roles.RoleTable(9876)
    assert test_start_time < table.time_last_active
    
    # Records correct input
    test_add_time = time.time()
    assert test_add_time > table.time_last_active
    assert table.add("<@&1234>", "<:test:1022906071234379776>")
    assert table.roles[0][0] == "test"
    assert table.roles[0][1] == 1234
    assert test_add_time < table.time_last_active

    # Rejects incorrect input
    assert not table.add("<@1234>", "<:test:1022906071234379776>")
    assert not table.add("1234", "test")
    assert not table.add("<@&1234>", "test")
    assert not table.add("", "")
    assert len(table.roles) == 1

def test_table_commit():
    table = roles.RoleTable(9876)
    # Add a role to table and make sure commited table is correct
    assert table.add("<@&1234>", "<:test:1022906071234379776>")
    assert table.commit(1)
    assert os.path.isfile(f'{conftest.TEST_DIR}/{"database.db"}'), f'{conftest.TEST_DIR}/{"database.db"} was not created'
    with sqlite3.connect(table.DBFILE) as db:
        cursor = db.execute(f'SELECT message_id, emoji_name, role_id FROM role_table WHERE message_id = {1}')
        row = cursor.fetchone()
        message_id = row[0]
        emoji_name = row[1]
        role_id = row[2]
        assert message_id == 1
        assert emoji_name == "test"
        assert role_id == 1234
        assert db.execute(f'SELECT message_id, emoji_name, role_id FROM role_table').arraysize == 1
    assert not table.commit(2)  # If role already has a mapping, don't allow a second mapping
    os.remove(f'{conftest.TEST_DIR}/{"database.db"}')

def test_table_remove():
    cog = roles.Roles(discord.Bot())
    cog.add_active_table(1)
    table = cog.find_active_table(1)
    assert table != None
    assert table.add("<@&1234>", "<:test:1022906071234379776>")
    assert table.commit(1)
    assert os.path.isfile(f'{conftest.TEST_DIR}/{"database.db"}'), f'{conftest.TEST_DIR}/{"database.db"} was not created'
