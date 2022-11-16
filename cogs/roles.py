import logging
import sqlite3
import discord
from discord.ext import commands, tasks
import time
import re

class RoleTable():
    TIMEOUT_MIN = 10
    TIMEOUT_SEC = TIMEOUT_MIN * 60
    DBFILE = "data/database.db"

    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self.time_last_active = time.time()
        self.roles = []
    
    def add(self, role: str, emoji_str: str) -> bool:
        """Adds the role and emoji to the role table

        Args:
            role (str)
            emoji (str)
        Returns:
            bool: whether the addition succeeded
        """
        # Clean input
        role_id: int
        try:
            role = role.rstrip()
            emoji_str = emoji_str.rstrip()
            # Accepts format <@&int> for role
            if re.fullmatch("^<@&[0-9]+>$", role):
                role_id = int(role[3:-1])
            else:
                raise NameError("Role does not match regex")
            emoji = discord.PartialEmoji.from_str(emoji_str)
            if emoji.is_custom_emoji():
                pass
            #TODO: filter for unicode emojis
            #elif re.fullmatch("",emoji):
            #    pass
            else:
                raise NameError("Emoji does not match regex")
        except NameError:
            logging.error(f'Role Not Recorded\tRole:{role}\tEmoji:{emoji_str}')
            return False
        
        # Add emoji and role to table
        logging.info(f'Emoji Recorded\nRole:{role_id}\n\nEmoji:{emoji}\n')
        self.roles.append((emoji.name,role_id))
        self.time_last_active = time.time()
        return True
    
    def commit(self, message_id) -> bool:
        with sqlite3.connect(self.DBFILE) as db:
            for role in self.roles:
                try:
                    db.execute("""CREATE TABLE IF NOT EXISTS role_table (
                                    message_id	INTEGER NOT NULL,
                                    emoji_name	TEXT NOT NULL,
                                    role_id     INTEGER NOT NULL UNIQUE,
                                    PRIMARY KEY("message_id","emoji_name")
                                );""")
                    db.execute(f'INSERT INTO role_table (message_id,emoji_name,role_id) VALUES ({message_id},\'{role[0]}\',{role[1]});')
                    db.commit()
                except sqlite3.IntegrityError as ie:
                    logging.error(f'{ie}: ({message_id},\'{role[0]}\',{role[1]})')
                    return False
        return True

class Roles(commands.Cog):
    role = discord.SlashCommandGroup("role", "commands for creating self assigned roles")
    table = role.create_subgroup("table", "commands for self assign tables")
    test = role.create_subgroup("test", "testing commands for creating self assigned roles", guild_ids=1019757534095089724)

    def __init__(self, bot : discord.Bot):
        self.bot = bot
        self.active_tables = []
        self.role_table_watchdog.start()

    def cog_unload(self):
        self.role_table_watchdog.cancel()

    def find_active_table(self, channel_id) -> RoleTable:
        if len(self.active_tables) != 0:
            for table in self.active_tables:
                if table.channel_id == channel_id:
                    return table
        return None

    def add_active_table(self, channel_id: int):
        existing_table = self.find_active_table(channel_id)
        if existing_table != None:
            self.active_tables.remove(existing_table)
        self.active_tables.append(RoleTable(channel_id))
    
    @table.command()
    async def open(self, ctx: discord.ApplicationContext):
        self.add_active_table(ctx.channel_id)
        logging.info(f'Table created in: {ctx.channel_id} ')
        response = "You have started creating a self assign table!\nUse /roles add to start adding roles"
        await ctx.respond(response, ephemeral=True)

    @table.command()
    async def add(self, ctx: discord.ApplicationContext, role: str, emoji: str):
        table = self.find_active_table(ctx.channel_id)
        if table != None:
            if table.add(role, emoji):
                await ctx.respond(f'Added {role}:{emoji}', ephemeral=True)
            else:
                await ctx.respond(f'Could not add {role}:{emoji} to table', ephemeral=True)
        else:
            await ctx.respond("No active table", ephemeral=True)

    @table.command()
    async def commit(self, ctx: discord.ApplicationContext):
        table = await self.find_active_table(ctx.channel_id)
        if table != None:
            self.active_tables.remove(table)
            await ctx.respond(f'Stopping table', ephemeral=True)
        else:
            await ctx.respond("No active table", ephemeral=True)

    @test.command(description="")
    async def test_input(self, ctx: discord.ApplicationContext, role: str, emoji: str):
        """tests collection of emoji and role data"""
        logging.info(f'Role:{role}\tEmoji:{emoji}')
        await ctx.respond(f'role: {role}, emoji: {emoji}')

    @tasks.loop(seconds=1)
    async def role_table_watchdog(self):
        for table in self.active_tables:
            if time.time() - table.time_last_active > RoleTable.TIMEOUT_SEC:
                logging.info(f'Table timed out in: {table.channel_id} ')
                await table.ctx.respond("Timed Out", ephemeral=True)
                self.active_tables.remove(table)

def setup(bot):
    bot.add_cog(Roles(bot))

def teardown(bot):
    bot.remove_cog('Roles')
    