import discord
import requests
from discord.ext import tasks, commands
import aiosqlite
import os


class Calendar(commands.Cog):
    calendar = discord.SlashCommandGroup("calendar", "calendar functionality")

    def __init__(self, bot : discord.Bot):
        self.bot = bot
        self.loop.start()

    def cog_unload(self):
        self.loop.stop()

    @calendar.command(description="retrieve calendar")
    async def get(self, ctx):
        GUILDID = str(ctx.guild_id)

        #get data
        response = requests.get("https://acm.mines.edu/schedule/ical.ics")
        if not response:
            await ctx.respond("error: " + str(response))
        data = ((response.text).replace("\n ", "")).split("\r\n")
        
        #create data/ if it doesnt exist
        if not os.path.exists("data/"):
            os.mkdir("data/")
        
        #open database
        async with aiosqlite.connect("data/database.db") as db:
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

        #test announcement
        await self.announce(await self.getchannel(ctx))

        print("successfully retrieved calendar")
        await ctx.respond("successfully retrieved calendar", ephemeral=True)
    

    @tasks.loop(seconds=5.0)
    async def loop(self):
        print("hello")

    async def announce(self, channel):
        announcement = discord.Embed(title="announcement!", description="this is a test announcement", color=0x0085c8)
        await channel.send(embed=announcement)
        return

    #gets guild-specific announcement channel from db
    async def getchannel(self, ctx):

        GUILDID = str(ctx.guild_id)

        #create data/ if it doesnt exist
        if not os.path.exists("data/"):
            os.mkdir("data/")

        #open database
        async with aiosqlite.connect("data/database.db") as db:
            #create announcement_channels table if it doesnt exist
            await db.execute("CREATE TABLE IF NOT EXISTS announcement_channels(guildID integer, announcementChannel integer)")
            #find channel id from table
            async with db.execute(f"SELECT * FROM announcement_channels WHERE guildID={GUILDID}") as cursor:
                list = await cursor.fetchall()
            if list == []:
                #if announcement channel not known, set the channel
                channel = await self.setchannel(ctx)
                list.append((GUILDID, channel.id))

        #find channel from id
        channel = discord.utils.get(ctx.guild.text_channels, id=list[0][1])
        if channel == None:
            channel = await self.setchannel(ctx)

        return channel

    #queries user and sets guild-specific announcement channel in db
    @calendar.command(description="Set the announcement channel")
    async def setchannel(self, ctx):

        GUILDID = str(ctx.guild_id)

        #define modal
        class Modal(discord.ui.Modal):
            def __init__(self, text, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.add_item(discord.ui.InputText(label=text[:45], style=discord.InputTextStyle.singleline, placeholder="Channel ID"))
            async def callback(self, interaction: discord.Interaction):
                if self.children[0].value.isnumeric():
                    channel = discord.utils.get(ctx.guild.text_channels, id=int(self.children[0].value))
                    if channel == None:
                        await interaction.response.send_message("Error: Invalid Channel ID", ephemeral=True)
                        return
                await interaction.response.send_message(f"Annoucement channel set to: `{channel.name}`", ephemeral=True)
                return

        #create data/ if it doesnt exist
        if not os.path.exists("data/"):
            os.mkdir("data/")

        #find current channel
        async with aiosqlite.connect("data/database.db") as db:
            #create announcement_channels table if it doesnt exist
            await db.execute("CREATE TABLE IF NOT EXISTS announcement_channels(guildID integer, announcementChannel integer)")
            #find channel from table
            async with db.execute(f"SELECT * FROM announcement_channels WHERE guildID={GUILDID}") as cursor:
                list = await cursor.fetchall()
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
                await db.commit()

        print(f"successfully set channel to: {channel.name} ({channel.id})")
        return channel

    
def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')