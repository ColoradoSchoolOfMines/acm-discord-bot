import discord
import requests
from discord.ext import tasks, commands
import aiosqlite
import os
import time
import calendar


class Calendar(commands.Cog):
    calendar = discord.SlashCommandGroup("calendar", "calendar functionality")

    def __init__(self, bot : discord.Bot):
        self.bot = bot
        self.check.start()

    def cog_unload(self):
        self.check.stop()


    #parse .ics data into events
    def parseData(self, data, GUILDID:int):
        events = []
        location = ""
        description = ""
        for l in data:
            line = l.split(':', 1)
            id = line[0].split(';', 1)[0]
            if id == "SUMMARY":
                name = line[1].replace("'","")
            elif id == "DTSTART":
                startTime = line[1]
            elif id == "DTEND":
                endTime = line[1]
            elif id == "DESCRIPTION":
                description = line[1].replace("'", "")
            elif id == "LOCATION":
                location = line[1].replace("'","")
            elif line == ["END", "VEVENT"]:
                events.append((name, GUILDID, startTime, endTime, description, location))
        return events
    

    #main loop to get data, write to db, and announce
    @tasks.loop(minutes=60.0)
    async def check(self):

        #get information
        db = await self.openDatabase()
        await db.execute("""CREATE TABLE IF NOT EXISTS setup(
                            guildID INTEGER PRIMARY KEY,
                            announcementChannel INTEGER,
                            url TEXT
                        )""")
        async with db.execute(f"SELECT * FROM setup") as cursor:
            known = await cursor.fetchall()
        await db.close()
        print(f"\nfound {len(known)} guilds:")

        #query each guild
        events = []
        print("querying...")
        for guildid, channelid, url in known:
            print(f"  {guildid}: ", end ="")
            if url == None:
                print("no url to query")
                continue
            else:
                #get data
                response = requests.get(url)
                if not response:
                    print("invalid url")
                    continue
                data = response.text.replace("\r\n ", "").replace("\,", ",").split("\r\n")
                events += self.parseData(data, guildid)
                print("success")

        #write events to db
        db = await self.openDatabase()
        await db.execute("DROP TABLE IF EXISTS events")
        await db.execute("""CREATE TABLE events(
                            name TEXT NOT NULL,
                            guildID INTEGER NOT NULL,
                            startTime TEXT NOT NULL,
                            endTime TEXT NOT NULL,
                            description TEXT,
                            location TEXT
                        )""")
        for event in events:
            await db.execute(f"INSERT INTO events VALUES('{event[0]}', {event[1]} ,'{event[2]}','{event[3]}','{event[4]}','{event[5]}')")
        await db.commit()
        await db.close()

        #make an announcement for each guild
        currTime = int(time.time())
        print("announcing...")
        for guildid, channelid, url in known:
            print(f"  {guildid}: ", end ="")

            #find next or most recent event
            minIndex = -1
            minValue = 10**100
            for i, event in enumerate(events):
                if event[1] != guildid: continue
                format = "%Y%m%d"
                if 'T' in event[2]: #if date AND time
                    format += "T%H%M%S"
                diff = calendar.timegm(time.strptime(event[2], format)) - currTime
                if diff > 0 and diff < minValue:
                    minValue = diff
                    minIndex = i

            #make announcement
            if channelid == None:
                print("no announcement channel")
            elif (await self.announceEvent(guildid, channelid, events[minIndex])):
                print("invalid announcement channel")
            else:
                print("success")


    #make announcement in given channel
    async def announceEvent(self, guildid:int, channelid:int, event):

        #get guild from guildid
        guilds = [x for x in self.bot.guilds if x.id == guildid]
        if guilds == []:
            return -1

        #get channel from guild
        channel = discord.utils.get(guilds[0].text_channels, id=int(channelid))
        if channel == None:
            return -1
        
        #build announcement
        announcement = discord.Embed(title="Upcoming Event:", color=0x0085c8)
        informat = "%Y%m%d"
        outformat = "%A, %B %d"
        if 'T' in event[2]: #if date AND time
            informat += "T%H%M%S"
            outformat = "%I:%M%p " + outformat
        description = time.strftime(outformat, time.strptime(event[2], informat))
        if event[5] != "":
            description += f"\n{event[5]}"
        if event[4] != "":
            description += f"\n{event[4]}"
        announcement.add_field(name=event[0], value=description)

        #announce!
        await channel.send("@(insert role here)") # <-- temporary
        await channel.send(embed=announcement)
        return 0


    #queries user and sets announcement channel and url in database
    @calendar.command(description="Configure calendar settings")
    async def setup(self, ctx):

        GUILDID = str(ctx.guild_id)

        def validateChannelID(channelid:str):
            if not channelid.isnumeric():
                return False
            channel = discord.utils.get(ctx.guild.text_channels, id=int(channelid))
            if channel == None:
                return False
            else:
                return True
        
        def validateURL(url:str):
            try:
                response = requests.get(url)
                if not response:
                    return False
                else:
                    return True
            except Exception:
                return False

        #define modal
        class Modal(discord.ui.Modal):
            channel = "NULL"
            url = "NULL"
            def __init__(self, channeltext, urltext, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.add_item(discord.ui.InputText(label=channeltext[:45], style=discord.InputTextStyle.singleline, placeholder="Channel ID"))
                self.add_item(discord.ui.InputText(label=urltext[:45], style=discord.InputTextStyle.singleline, placeholder="Calendar URL"))
            async def callback(self, interaction: discord.Interaction):
                #validate channel
                if validateChannelID(self.children[0].value):
                    self.channel = self.children[0].value
                    message = f"Set Channel to: `{discord.utils.get(ctx.guild.text_channels, id=int(self.channel)).name}`"
                else:
                    message = "Invalid Channel, nothing was changed"
                #validate url
                if validateURL(self.children[1].value):
                    self.url = f"\"{self.children[1].value}\""
                    c = '\"'
                    message += f"\nSet URL to: `{self.url.replace((c),'')}`"
                else:
                    message += "\nInvalid URL, nothing was changed"
                #send response
                embed = discord.Embed(title="Calendar Setup:", description=message, color=0x0085c8)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        #get known information
        db = await self.openDatabase()
        await db.execute("""CREATE TABLE IF NOT EXISTS setup(
                            guildID INTEGER PRIMARY KEY,
                            announcementChannel INTEGER,
                            url TEXT
                        )""")
        async with db.execute(f"SELECT * FROM setup WHERE guildID={GUILDID}") as cursor:
            known = await cursor.fetchall()
        await db.close()
        
        #set modal text
        if known == []:
            channeltext = "(there is no current channel set)"
            urltext = "(there is no current url set)"
        else:
            if known[0][1] == None:
                channeltext = "(there is no current channel set)"
            elif (discord.utils.get(ctx.guild.text_channels, id=known[0][1])) == None:
                channeltext = "current channel is invalid"
            else:
                channeltext = f"current channel is: {known[0][1]}"
            if known[0][2] == None:
                urltext = "(there is no current url set)"
            else:
                urltext = f"current url is: {known[0][2]}"

        #prompt user with modal
        modal = Modal(channeltext, urltext, title="Calendar Setup")
        await ctx.send_modal(modal)
        await modal.wait()

        #write data to database
        db = await self.openDatabase()
        async with db.execute(f"SELECT * FROM setup WHERE guildID={GUILDID}") as cursor:
            if known == []:
                #if not known, insert new data
                await cursor.execute(f"INSERT INTO setup VALUES({GUILDID}, {modal.channel}, {modal.url})")
            else:
                #else update data
                if modal.channel != "NULL":
                    await cursor.execute(f"""UPDATE setup SET announcementChannel = {modal.channel} WHERE guildID={GUILDID}""")
                    print(f"\nchanged {GUILDID}'s channel to: {modal.channel}")
                if modal.url != "NULL":
                    await cursor.execute(f"""UPDATE setup SET url = {modal.url} WHERE guildID={GUILDID}""")
                    print(f"\nchanged {GUILDID}'s url to: {modal.url}")
        await db.commit()
        await db.close()

        return


    #opens database from: data/database.db
    async def openDatabase(self):
        if not os.path.exists("data/"):
            os.mkdir("data/")
        return await aiosqlite.connect("data/database.db")
    

def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')