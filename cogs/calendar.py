import discord
import requests
from discord.ext import commands
import aiosqlite
import os


class Calendar(commands.Cog):
    calendar = discord.SlashCommandGroup("calendar", "calendar functionality")

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    @calendar.command(description="retrieve calendar")
    async def get(self, ctx):

        #get data
        response = requests.get("https://acm.mines.edu/schedule/ical.ics")
        if not response:
            await ctx.respond("error: " + str(response))
        data = ((response.text).replace("\n ", "")).split("\r\n")
        
        guildID = str(ctx.guild_id)

        #create data/ if it doesnt exist
        if not os.path.exists("data/"):
            os.mkdir("data/")
        
        async with aiosqlite.connect("data/database.db") as db:
            #drop table if it already exists
            await db.execute("DROP TABLE IF EXISTS events_" + guildID)
            #create a new empty table
            await db.execute('CREATE TABLE events_' + guildID + '(summary text, start text, end text, uid integer PRIMARY KEY, description text, location text)')
            #parse data
            for l in data:
                line = l.split(':', 1)
                id = line[0].split(';', 1)[0]
                if id == "SUMMARY":
                    summary = line[1]
                elif id == "DTSTART":
                    start = line[1]
                elif id == "DTEND":
                    end = line[1]
                elif id == "UID":
                    uid = int(line[1])
                elif id == "DESCRIPTION":
                    description = line[1].replace("'", "")
                elif id == "LOCATION":
                    location = line[1]
                elif line == ["END", "VEVENT"]:
                    await db.execute('INSERT INTO events_' + guildID + ' VALUES(\''+summary+'\',\''+start+'\',\''+end+'\','+str(uid)+',\''+description+'\',\''+location+'\')')
            #commit changes to database
            await db.commit()

        #test announcement
        channel = discord.utils.get(ctx.guild.text_channels, id=1032389925271781479)
        await announce(channel)

        print("success")
        await ctx.respond("success", ephemeral=True)

async def announce(channel):
    embed = discord.Embed(title="announcement!", description="this is a test announcement", color=0x0085c8)
    await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')

# we only need (no repeating events):
# SUMMARY
# DTSTART
# DTEND
# DESCRIPTION
# LOCATION
#
# all known parameters for .ics file:
# SUMMARY
# DTSTART
# DTEND
# DTSTAMP
# UID
# DESCRIPTION
# LOCATION
#
