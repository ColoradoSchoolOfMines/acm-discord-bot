import discord
import requests
from discord.ext import commands

class Calendar(commands.Cog):
    calendar = discord.SlashCommandGroup("calendar", "calendar functionality")

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    @calendar.command(description="retrieve calendar")
    async def get(self, ctx):

        URL = "https://acm.mines.edu/schedule/ical.ics"
        response = requests.get(URL)
        if not response:
            await ctx.respond("error: " + str(response))
        data = response.text
        print(data)

        await ctx.respond("success")


def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')