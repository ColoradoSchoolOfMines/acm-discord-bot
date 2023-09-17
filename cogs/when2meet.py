import discord
from discord.ext import commands

class When2Meet(commands.Cog):
    # create the slash command group called 'test', accessed with /test [COMMAND]
    when2meet = discord.SlashCommandGroup("when2meet", "for testing purposes")

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    # create a command called 'create'
    @when2meet.command(description="Say Hi!")
    async def create(self, ctx):
        # do stuff here
        await ctx.respond("https://www.when2meet.com/")

def setup(bot):
    bot.add_cog(When2Meet(bot))

def teardown(bot):
    bot.remove_cog('When2Meet')
