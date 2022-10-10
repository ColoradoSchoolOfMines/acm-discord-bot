import logging
from tokenize import Name
import discord
from discord.ext import commands, tasks
import time
import re

class RoleTable():
    TIMEOUT_MIN = 10
    TIMEOUT_SEC = TIMEOUT_MIN * 60
    
    roles = [{}]

    def __init__(self, ctx):
        self.ctx = ctx
        self.time_last_active = time.time()
    
    def add(self, role: str, emoji: str) -> bool:
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
            emoji = emoji.rstrip()
            # Accepts format <@&int> for role
            if re.fullmatch("^<@&[0-9]+>$", role):
                role_id = int(role[3:-1])
            else:
                raise NameError("Role does not match regex")
            emoji = emoji.rstrip()
            #Accepts format <:str:int> for emoji
            if re.fullmatch("^<:.+:[0-9]+>$", emoji):
                emoji = emoji.split(":")[1]
            ###TODO: Include unicode emojis
            #elif re.fullmatch("",emoji):
            #    pass
            else:
                raise NameError("Emoji does not match regex")
        except NameError:
            logging.error(f'Role Not Recorded\tRole:{role_id}\tEmoji:{emoji}\n')
            return False
        
        # Add emoji and role to table
        logging.info(f'Emoji Recorded\nRole:{role_id}\n\nEmoji:{emoji}\n')
        self.roles.append({role_id,emoji})
        return True
    
    def commit(self, ctx):
        self.ctx = ctx
        

class Roles(commands.Cog):
    role = discord.SlashCommandGroup("role", "commands for creating self assigned roles")
    table = role.create_subgroup("table", "commands for self assign tables")
    test = role.create_subgroup("test", "testing commands for creating self assigned roles", guild_ids=1019757534095089724)
    
    active_tables = []

    def __init__(self, bot : discord.Bot):
        self.bot = bot
        self.role_table_watchdog.start()

    def cog_unload(self):
        self.role_table_watchdog.cancel()

    @table.command()
    async def open(self, ctx: discord.ApplicationContext):
        existing_table = await self.find_active_table(ctx.channel_id)
        if existing_table != None:
            self.active_tables.remove(existing_table)
        self.active_tables.append(RoleTable(ctx))
        logging.info(f'Table created in: {ctx.channel_id} ')
        response = "You have started creating a self assign table!\nUse /roles add to start adding roles"
        await ctx.respond(response, ephemeral=True)
    
    @table.command()
    async def add(self, ctx: discord.ApplicationContext, role: str, emoji: str):
        table = await self.find_active_table(ctx.channel_id)
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
    
    async def find_active_table(self, channel_id) -> RoleTable:
        if len(self.active_tables) != 0:
            for table in self.active_tables:
                if table.ctx.channel_id == channel_id:
                    return table
        return None

    @test.command(description="")
    async def test_input(self, ctx: discord.ApplicationContext, role: str, emoji: str):
        """tests collection of emoji and role data"""
        logging.info(f'Role:{role}\tEmoji:{emoji}')
        await ctx.respond(f'role: {role}, emoji: {emoji}')

    @tasks.loop(seconds=1)
    async def role_table_watchdog(self):
        for table in self.active_tables:
            if time.time() - table.time_last_active > RoleTable.TIMEOUT_SEC:
                logging.info(f'Table timed out in: {table.ctx.channel_id} ')
                await table.ctx.respond("Timed Out", ephemeral=True)
                self.active_tables.remove(table)

def setup(bot):
    bot.add_cog(Roles(bot))

def teardown(bot):
    bot.remove_cog('Roles')
    