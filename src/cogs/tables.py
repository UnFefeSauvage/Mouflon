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
    def __init__(self, bot, resource_manager):
        logger.info("Initialisation du module JDR...")
        self.bot = bot
        self.resource_manager = resource_manager
        self.tables = {}
        self.tasks = {}
        self.buffer = {}

        self.config = json.loads(self.resource_manager.read("resources/JDR/config.json"))

        files_to_load = os.listdir("resources/JDR/tables")

    
    @commands.Cog.listener()
    async def on_ready(self):
        #TODO Générer les tasks d'attente
    
    async def close(self):
        #TODO Sauvegarder l'état des tables avant de quitter
    
    #TODO Gestion d'erreur

    #*-*-*-*-*-*-*-*-*#
    #*-*-COMMANDS--*-*#
    #*-*-*-*-*-*-*-*-*#

    @commands.command()
    async def creer_table(self, ctx):
        #TODO Coder la création intéractive de table
        pass

    async def annuler_table(self, ctx):
        #TODO Coder l'annulation interactive d'une table de l'utilisateur
    