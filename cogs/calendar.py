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

    @calendar.command(description="retrieve calendar")
    async def get(self, ctx):
        GUILDID = str(ctx.guild_id)

        #get data
        response = requests.get("https://acm.mines.edu/schedule/ical.ics")
        if not response:
            await ctx.respond("error: " + str(response))
        data = ((response.text).replace("\n ", "")).split("\r\n")
        
        #open database
        db = await self.openDatabase()
        #drop table if it already exists
        await db.execute(f"DROP TABLE IF EXISTS events_{GUILDID}")
        #create a new empty table
        await db.execute(f"CREATE TABLE events_{GUILDID}(summary text, start text, end text, uid integer PRIMARY KEY, description text, location text)")
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
                await db.execute(f"INSERT INTO events_{GUILDID} VALUES(\'{summary}\',\'{start}\',\'{end}\',{uid},\'{description}\',\'{location}\')")
        #commit changes to database
        await db.commit()
        #close database
        await db.close()

        #test announcement
        await self.announce(await self.getchannelid(ctx))

        print("successfully retrieved calendar")
        await ctx.respond("successfully retrieved calendar", ephemeral=True)
    
    @tasks.loop(seconds=30.0)
    async def loopp(self):
        print("---")

    async def announce(self, channel):
        announcement = discord.Embed(title="announcement!", description="this is a test announcement", color=0x0085c8)
        await channel.send(embed=announcement)
        return


    #gets guild-specific announcement channel from db
    async def getchannelid(self, GUILDID):

        #open database
        db = await self.openDatabase()
        #create announcement_channels table if it doesnt exist
        await db.execute("CREATE TABLE IF NOT EXISTS setup(guildID integer primary key unique, announcementChannel integer)")
        #find channel id from table
        async with db.execute(f"SELECT * FROM setup WHERE guildID={GUILDID}") as cursor:
            list = await cursor.fetchall()
        if list == []:
            #announcement channel is unknown
            return None
        #close database
        await db.close()

        return list[0]


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

        print(known)
        
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