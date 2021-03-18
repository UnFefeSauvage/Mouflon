# -*- coding: UTF-8 -*-
import discord
from discord.ext import commands, tasks

import os
import random
import time
import json
import logging
import asyncio
import operator

#* * # * # * # * # * # * # * # * # * *#
#* * # MISE EN PLACE DU LOGGING  # * *#
#* * # * # * # * # * # * # * # * # * *#

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(name)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler.setFormatter(logFormatter)
logger.addHandler(handler)

class JDRCog(commands.Cog):
    """Un ensemble de commandes et évènements permettant de gérer des tables de JDR"""
    def __init__(self, bot: discord.Client, resource_manager):
        logger.info("Initialisation du module JDR...")
        self.bot: discord.Client = bot
        self.resource_manager = resource_manager
        self.tables: dict = {}
        self.tasks: dict = {}
        self.buffer: dict = {}

        self.config = json.loads(self.resource_manager.read("resources/JDR/config.json"))

        files_to_load = os.listdir("resources/JDR/tables")

    
    @commands.Cog.listener()
    async def on_ready(self):
        #TODO Générer les tasks d'attente
        pass
    
    async def close(self):
        #TODO Sauvegarder l'état des tables avant de quitter
        pass
    
    #TODO Gestion d'erreur

    #*-*-*-*-*-*-*-*-*#
    #*-*-COMMANDS--*-*#
    #*-*-*-*-*-*-*-*-*#

    @commands.command()
    async def creer_table(self, ctx):
        #TODO Coder la création intéractive de table
        pass
    
    @commands.command()
    async def annuler_table(self, ctx):
        #TODO Coder l'annulation interactive d'une table de l'utilisateur
        pass
    

    #*-*-*-*-*-*-*#
    #*-*-TASKS-*-*#
    #*-*-*-*-*-*-*#



async def wait_for_seconds(secs, then, cancel_handler=None):
    if secs > 0:
        try:
            await asyncio.sleep(secs)
        except asyncio.CancelledError:
            if cancel_handler is None:
                raise
            else:
                await cancel_handler()
                return

    if not (then is None):
        await then()
