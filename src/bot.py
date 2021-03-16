# -*- coding: UTF-8 -*-
import logging
import json

import discord
from discord.ext import commands

import resources
import cogs

#* * # * # * # * # * # * # * # * # * *#
#* MISE EN PLACE DU RESOURCE_MANAGER *#
#* * # * # * # * # * # * # * # * # * *#

resource_manager = resources.ResourcesManager("resources")
config = json.loads(resource_manager.read("config.json"))


#* * # * # * # * # * # * # * # * # * *#
#* * # MISE EN PLACE DU LOGGING  # * *#
#* * # * # * # * # * # * # * # * # * *#

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(name)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler.setFormatter(logFormatter)
logger.addHandler(handler)


#Les parties de l'API que le bot a l'intention d'utiliser
bot_intents = discord.Intents(
    messages=True,
    members=True,
    guilds=True,
    dm_messages=True
)

bot = commands.Bot(command_prefix=config["prefix"], intents=bot_intents)

@bot.event
async def on_ready():
    logger.info("Bot is connected and ready to go!")

def launch():
    bot.run(config["token"])