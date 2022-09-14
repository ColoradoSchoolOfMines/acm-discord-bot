'''
Entry point for python application. Run this file to start the bot.
Copyright (C) 2022 Keenan Buckley

This file is part of {PROJECT_NAME}.

{PROJECT_NAME} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import sys
import discord
import logging
import models

logging.basicConfig(level=logging.INFO, filename='discord.log',
                    filemode='w', format='date+time:%(asctime)s | %(message)s')
DEBUG_GUILDS = models.get_env_safe(models.ENVs.DEBUG_GUILDS).split(',')
bot = discord.Bot(debug_guilds=DEBUG_GUILDS)
extensions = [
    "loot"
]


@bot.event
async def on_ready():
    print(f'{bot.user} is ready and online!')
    logging.info(f'{bot.user} is ready and online!')
    logging.info(f'Connected to {len(bot.guilds)} Guilds:')
    for guild in bot.guilds:
        logging.info(f'{guild}|{guild.id}')


@bot.slash_command(guild_ids=DEBUG_GUILDS)
async def refresh(ctx):
    reload_extensions()
    await ctx.respond("Refreshed extensions!")


def load_extensions():
    for ext in extensions:
        bot.load_extension(f'cogs.{ext}')


def unload_extensions():
    for ext in extensions:
        bot.unload_extension(f'cogs.{ext}')


def reload_extensions():
    for ext in extensions:
        bot.reload_extension(f'cogs.{ext}')


def main():
    # Whether to deploy to testing bot or main bot (defaults to testing)
    token = models.ENVs.DEBUG_TOKEN
    if len(sys.argv) > 1 and sys.argv[1] == 'deploy':
        token = models.ENVs.TOKEN

    # Run Pycord Bot until keyboard interrupt
    logging.info(f'Starting Pycord Bot...')
    load_extensions()
    bot.run(models.get_env_safe(token))
    unload_extensions()

    # Safely shut down connections and save data
    print(f'\nShutting down...')
    logging.info(f'Shutting down...')


if __name__ == '__main__':
    main()
