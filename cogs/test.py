import discord
from discord.ext import commands

class Test(commands.Cog):
    # create the slash command group called 'test', accessed with /test [COMMAND]
    test = discord.SlashCommandGroup("test", "for testing purposes")

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    # create a command called 'hello'
    @test.command(description="Say Hi!")
    async def hello(self, ctx):
        # do stuff here
        await ctx.respond(f"Hello <@{ctx.author.id}>!")

def setup(bot):
    bot.add_cog(Test(bot))

def teardown(bot):
    bot.remove_cog('Test')
