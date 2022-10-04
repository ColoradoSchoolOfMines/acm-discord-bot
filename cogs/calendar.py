import discord
import requests
from discord.ext import commands
import aiosqlite
#from ics import Calendar, Event

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
        
        #parse and write to database
        async with aiosqlite.connect("data/database.db") as db:
            #delete table if it already exists
            await db.execute("DROP TABLE IF EXISTS events")
            #create a new empty table
            await db.execute("CREATE TABLE events(summary text, start text, end text, stamp text, uid integer PRIMARY KEY, description text, location text)")
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
                elif id == "DTSTAMP":
                    stamp = line[1]
                elif id == "UID":
                    uid = int(line[1])
                elif id == "DESCRIPTION":
                    description = line[1].replace("'", "")
                elif id == "LOCATION":
                    location = line[1]
                elif line == ["END", "VEVENT"]:
                    await db.execute("INSERT INTO events VALUES(\'"+summary+"\',\'"+start+"\',\'"+end+"\',\'"+stamp+"\',"+str(uid)+",\'"+description+"\',\'"+location+"\')")
            #commit changes
            await db.commit()

        print("success")
        await ctx.respond("success")


def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')