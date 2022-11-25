import discord
import requests
from discord.ext import tasks, commands
import aiosqlite
import os


class Calendar(commands.Cog):
    calendar = discord.SlashCommandGroup("calendar", "calendar functionality")

    def __init__(self, bot : discord.Bot):
        self.bot = bot
        self.loopp.start()

    def cog_unload(self):
        self.loopp.stop()

    def parseData(self, data, GUILDID:int):
        events = []

        #parse data
        for l in data:
            line = l.split(':', 1)
            id = line[0].split(';', 1)[0]
            if id == "SUMMARY":
                name = line[1]
            elif id == "DTSTART":
                startTime = line[1]
            elif id == "DTEND":
                endTime = line[1]
            elif id == "DESCRIPTION":
                description = line[1].replace("'", "")
            elif id == "LOCATION":
                location = line[1]
            elif line == ["END", "VEVENT"]:
                events.append((name, GUILDID, startTime, endTime, description, location))

        return events
    
    @tasks.loop(seconds=60.0)
    async def loopp(self):

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

        #for each guild
        events = []
        for i in range(len(known)):
            guildid = known[i][0]
            channelid = known[i][1]
            url = known[i][2]
            print(f"querying #{i+1}: {known[i]}")
            if url == None:
                print("    No url to query")
                continue
            else:
                #get data
                response = requests.get(url)
                if not response:
                    print("    invalid url")
                    continue
                data = ((response.text).replace("\n ", "")).split("\r\n")
                events += self.parseData(data, guildid)

            # #write events
            # db = await self.openDatabase()
            # await db.execute("""CREATE TABLE IF NOT EXISTS events(
            #                     name TEXT,
            #                     guildID INTEGER,
            #                     startTime TEXT,
            #                     endTime TEXT,
            #                     description TEXT,
            #                     location TEXT
            #                 )""")
            # await db.close()

            #test announcement
            if channelid == None:
                print("    No announcement channel")
            elif (await self.announce(guildid, channelid)):
                print("    Invalid announcement channel")
            else:
                print("    Made announcement")


    async def announce(self, guildid:int, channelid:int):
        #get guild
        guilds = [x for x in self.bot.guilds if x.id == guildid]
        if guilds == []:
            return -1
        #get channel
        channel = discord.utils.get(guilds[0].text_channels, id=int(channelid))
        if channel == None:
            return -1
        #make announcement
        announcement = discord.Embed(title="announcement!", description="this is a test announcement", color=0x0085c8)
        await channel.send(embed=announcement)
        return 0

    #queries user and sets guild-specific announcement channel in db
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
                message = "Set Channel to: "
                if validateChannelID(self.children[0].value):
                    self.channel = self.children[0].value
                    message += f"`{discord.utils.get(ctx.guild.text_channels, id=int(self.channel)).name}`"
                else:
                    message += "`Invalid Channel`"
                #validate url
                message += "\nSet URL to: "
                if validateURL(self.children[1].value):
                    self.url = f"\"{self.children[1].value}\""
                    c = '\"'
                    message += f"`{self.url.replace((c),'')}`"
                else:
                    message += "`Invalid URL`"
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
                #if already known, update data
                await cursor.execute(f"""UPDATE setup SET
                                        announcementChannel = {modal.channel},
                                        url = {modal.url}
                                        WHERE guildID={GUILDID}""")
        await db.commit()
        await db.close()

        print(f"changed channel to: {modal.children[0].value}\nchanged url to: {modal.children[1].value}")
        return


    #opens database from: data/database.db
    async def openDatabase(self):
        #create data/ if it doesnt exist
        if not os.path.exists("data/"):
            os.mkdir("data/")
        return await aiosqlite.connect("data/database.db")
    
def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')

#channel: 1032389925271781479
#url: https://acm.mines.edu/schedule/ical.ics