import discord
import requests
from discord.ext import commands
import aiosqlite
import os


class Calendar(commands.Cog):
    calendar = discord.SlashCommandGroup("calendar", "calendar functionality")

    def __init__(self, bot : discord.Bot):
        self.bot = bot

    def cog_unload(self):
        pass

    #parse ical file and return array of events
    async def parseData(self, data, GUILDID:int):
        return
    
    #announce event
    async def announceEvent(self, event):
        return

    #http request and process data
    async def check(self):
        return


    #displays the current guild's configuration
    @calendar.command(description="Display calendar configuration info")
    async def info(self, ctx):

        #get known information
        db = await self.openDatabase()
        await db.execute("""CREATE TABLE IF NOT EXISTS setup(
                            guildID INTEGER PRIMARY KEY NOT NULL,
                            url TEXT,
                            announcementChannel INTEGER
                        )""")
        async with db.execute(f"SELECT * FROM setup WHERE guildID={ctx.guild_id}") as cursor:
            known = await cursor.fetchall()
        await db.close()

        #make embed with information
        embed = discord.Embed(title="Calendar Configuration:", color=0x0085c8)
        if known == []:
            embed.add_field(name='', value="There is currently no information for this server. You can use `/calendar setup` to configure calendar settings.")
        else:
            guildid, url, channel = known[0]
            if url == None or self.validateURL(url):
                embed.add_field(name="Calendar URL:", value=f"`{url}`", inline=False)
            else:
                embed.add_field(name="Calendar URL:", value=f"`{url}`\nNote: This URL is invalid", inline=False)
            if channel == None or self.validateChannel(str(channel), ctx):
                channelName = discord.utils.get(ctx.guild.text_channels, id=channel).name
                embed.add_field(name="Announcement Channel:", value=f"`{channel}` (#{channelName})", inline=False)
            else:
                embed.add_field(name="Announcement Channel:", value=f"`{channel}`\nNote: This channel ID is invalid", inline=False)

        #send embed
        await ctx.respond(embed=embed, ephemeral=True)
        return
    

    #change the current configuration
    @calendar.command(description="Configure calendar settings")
    async def setup(self, ctx):

        #define modal
        class Modal(discord.ui.Modal):
            url = ""
            channel = ""
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.add_item(discord.ui.InputText(label="CALENDAR URL:", style=discord.InputTextStyle.singleline, required=False))
                self.add_item(discord.ui.InputText(label="ANNOUNCEMENT CHANNEL ID:", style=discord.InputTextStyle.singleline, required=False))
            async def callback(self, interaction: discord.Interaction):
                self.url = self.children[0].value
                self.channel = self.children[1].value
                await interaction.response.defer()

        #send modal
        modal = Modal(title="Calendar Setup")
        await ctx.send_modal(modal)
        await modal.wait()

        embed = discord.Embed(title="Calendar Configuration:", color=0x0085c8)
        db = await self.openDatabase()

        #if no entry exists, initialize a new one with all NULL values
        await db.execute("""CREATE TABLE IF NOT EXISTS setup(
                            guildID INTEGER PRIMARY KEY NOT NULL,
                            url TEXT,
                            announcementChannel INTEGER
                        )""")
        async with db.execute(f"SELECT * FROM setup WHERE guildID={ctx.guild_id}") as cursor:
            if await cursor.fetchall() == []:
                await db.execute(f"INSERT INTO setup VALUES({ctx.guild_id}, NULL, NULL)")
        
        #validate and update url:
        message = ""
        if modal.url == "":
            message = "URL was not changed"
        elif self.validateURL(modal.url):
            await db.execute(f"UPDATE setup SET url = \"{modal.url}\" WHERE guildID={ctx.guild_id}")
            message = f"URL was changed to `{modal.url}`"
        else:
            message = f"URL was not changed (`{modal.url}` is an invalid URL)"
        embed.add_field(name="Calendar URL:", value=message, inline=False)

        #validate and update channel:
        message = ""
        if modal.channel == "":
            message = "Channel was not changed"
        elif self.validateChannel(modal.channel, ctx):
            await db.execute(f"UPDATE setup SET announcementChannel = {modal.channel} WHERE guildID={ctx.guild_id}")
            channelName = discord.utils.get(ctx.guild.text_channels, id=int(modal.channel)).name
            message = f"Channel was changed to `{modal.channel}` (#{channelName})"
        else:
            message = f"Channel was not changed (`{modal.channel}` is an invalid channel)"
        embed.add_field(name="Announcement Channel:", value=message, inline=False)

        await db.commit()
        await db.close()

        await ctx.respond(embed=embed, ephemeral=True)
        return


    #for testing purposes...
    @calendar.command(description="This is for testing purposes...")
    async def test(self, ctx):
        await ctx.respond("*testing testing 123*")
        return


    #opens database from: data/database.db
    async def openDatabase(self):
        if not os.path.exists("data/"):
            os.mkdir("data/")
        return await aiosqlite.connect("data/database.db")

    #checks that a channel ID is valid
    def validateChannel(self, channelid:str, ctx):
        if not channelid.isnumeric(): return False
        channel = discord.utils.get(ctx.guild.text_channels, id=int(channelid))
        if channel == None: return False
        else: return True

    #checks that a url is valid
    def validateURL(self, url:str):
        try:
            response = requests.get(url)
            if not response: return False
            else: return True
        except Exception:
            return False

    

def setup(bot):
    bot.add_cog(Calendar(bot))

def teardown(bot):
    bot.remove_cog('Calendar')