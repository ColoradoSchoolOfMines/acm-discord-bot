import logging
import discord
from discord.ext import commands, tasks
import time

class RoleTable():
    TIMEOUT_MIN = 10
    TIMEOUT_SEC = TIMEOUT_MIN * 60
    
    roles = [{}]

    def __init__(self, ctx):
        self.ctx = ctx
        self.time_last_active = time.time()
    
    def add(self, role: str, emoji: str):
        self.roles.append({role,emoji})

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
            table.add(role, emoji)
            await ctx.respond(f'Added {role}:{emoji}', ephemeral=True)
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
    