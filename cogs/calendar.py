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
    
    @tasks.loop(seconds=5.0)
    async def loopp(self):
        print("hello")

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
        async with db.execute(f"SELECT * FROM announcement_channels WHERE guildID={GUILDID}") as cursor:
            list = await cursor.fetchall()
        if list == []:
            #announcement channel is unknown
            return None
        #close database
        await db.close()

        return list[0]


    #queries user and sets guild-specific announcement channel in db
    @calendar.command(description="Configure the calendar cog")
    async def setup(self, ctx):
        GUILDID = str(ctx.guild_id)

        #define modal
        class Modal(discord.ui.Modal):
            def __init__(self, text, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.add_item(discord.ui.InputText(label=text[:45], style=discord.InputTextStyle.singleline, placeholder="Channel ID"))
            async def callback(self, interaction: discord.Interaction):
                #check that channel exists
                if self.children[0].value.isnumeric():
                    channel = discord.utils.get(ctx.guild.text_channels, id=int(self.children[0].value))
                    if channel == None:
                        await interaction.response.send_message("Error: Invalid Channel ID", ephemeral=True)
                        return
                await interaction.response.send_message("Successfully configured calendar!", ephemeral=True)
                return

        #open datbase
        db = await self.openDatabase()
        #create announcement_channels table if it doesnt exist
        await db.execute("CREATE TABLE IF NOT EXISTS setup(guildID integer not null unique, announcementChannel integer not null, url integer not null, primary key(\"guildID\"))")
        #find channel from table
        async with db.execute(f"SELECT * FROM setup WHERE guildID={GUILDID}") as cursor:
            list = await cursor.fetchall()
            print(list)
            return
            if list == []:
                #if announcement channel not known
                label = "there is no current channel set"
            else:
                #find current channel
                currChannel = discord.utils.get(ctx.guild.text_channels, id=list[0][1])
                if currChannel == None:
                    label = "current channel is invalid"
                else:
                    label = f"current channel is: {currChannel.name}"

            #prompt user with modal
            modal = Modal(label, title="Set Announcement Channel")
            await ctx.send_modal(modal)
            await modal.wait()
            channel = discord.utils.get(ctx.guild.text_channels, id=int(modal.children[0].value))

            if list == []:
                #if not known, insert new data
                await cursor.execute(f"INSERT INTO announcement_channels VALUES({GUILDID}, {channel.id})")
            else:
                #if already known, update data
                await cursor.execute(f"UPDATE announcement_channels SET announcementChannel = {channel.id}")
        #commit changes to database
        await db.commit()
        #close database
        await db.close()

        print(f"successfully set channel to: {channel.name} ({channel.id})")
        return channel

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