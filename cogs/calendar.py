import discord
import requests
from discord.ext import commands
import aiosqlite


class Calendar(commands.Cog):
    calendar = discord.SlashCommandGroup("calendar", "calendar functionality")

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    def cog_unload(self):
        pass

    #parse ical file and return array of events
    async def parseData(self, data, GUILDID:int):
        return
    
    #announce event
    async def announceEvent(self, event):
        return

    #http request and process data
    async def check(self):
        return

    #displays the current guild's configuration
    @calendar.command(description="Display calendar configuration info")
    async def info(self, ctx):
        await ctx.respond("*display info here*")
        return
    
    #change the current configuration
    @calendar.command(description="Configure calendar settings")
    async def setup(self, ctx):
        await ctx.respond("*configure setup here*")
        return

    #for testing purposes...
    @calendar.command(description="This is for testing purposes...")
    async def test(self, ctx):
        await ctx.respond("*testing testing 123*")
        return

    

def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')