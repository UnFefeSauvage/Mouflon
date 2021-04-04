# -*- coding: UTF-8 -*-
from .Table import Table
from .ReactionListener import ReactionListener

import discord
from discord.ext import commands, tasks

import os
import re
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
        self.reaction_listener: ReactionListener = ReactionListener()
        self.tables: dict = {}
        self.tasks: dict = {}
        self.buffer: dict = {}

        self.config = json.loads(self.resource_manager.read("JDR/config.json"))

        #files_to_load = os.listdir("JDR/tables")

    #*-*-*-*-*-*-*-*-*-*#
    #*-*-*LISTENERS*-*-*#
    #*-*-*-*-*-*-*-*-*-*#

    @commands.Cog.listener()
    async def on_ready(self):
        #Récupération de la guilde
        self.guild: discord.Guild = self.bot.get_guild(int(self.config["guild_id"]))

        #Récupération du channel d'inscription
        self.inscription_channel: discord.TextChannel = self.guild.get_channel(int(self.config["inscription_channel_id"]))
        #TODO Générer les tasks d'attente
    
    async def close(self):
        #TODO Sauvegarder l'état des tables avant de quitter
        pass
    
    #TODO Gestion d'erreur
    @commands.Cog.listener()
    async def on_message(self,msg: discord.Message):
        author_id = str(msg.author.id)
        channel_id = msg.channel.id

        if author_id in self.buffer:
            if not self.buffer[author_id]["task"].done():
                if self.buffer[author_id]["task_input"]["channel"].id == channel_id:
                    # Si ce message était attendu par une fonction interactive,
                    # récupérer l'input et lancer la phase suivante
                    self.buffer[author_id]["task_input"] = msg.content
                    self.buffer[author_id]["task"].cancel()

    #*-*-*-*-*-*-*-*-*#
    #*-*-COMMANDS--*-*#
    #*-*-*-*-*-*-*-*-*#

    @commands.command()
    async def creer_table(self, ctx: commands.Context):
        """Permet de créer de façon interactive tout ce qui est nécéssaire à une table de JDR"""
        #Récupération de données pratiques        
        author_id = str(ctx.author.id)
        channel_id = str(ctx.channel.id)

        #Création de l'espace de buffer pour la création de la table
        if not (author_id in self.buffer):
            self.buffer[author_id] = {}
        
        #Si une tâche d'édition est déjà en cours, ne pas continuer
        if "task" in self.buffer[author_id]:
            if not self.buffer[author_id]["task"].done():
                await ctx.send("Tu es déjà en train d'éditer une partie!")
                return
        
        #TODO Check le nombre de parties déjà créées

        table_data = {
            "author": ctx.author,
            "channel": ctx.channel
        }

        #Création des données de base de la table, récupérées par la tâche d'édition
        self.buffer[author_id]["task_input"] = table_data
        self.buffer[author_id]["task"] = asyncio.Task(asyncio.sleep(0), name="placeholder")

        await self.edit_table(table_data)
    
    @commands.command()
    async def annuler_table(self, ctx):
        #TODO Coder l'annulation interactive d'une table de l'utilisateur
        pass
    

    #*-*-*-*-*-*-*#
    #*-*-TASKS-*-*#
    #*-*-*-*-*-*-*#

    @commands.command()
    async def test(self, ctx):
        waiting_task = asyncio.create_task(asyncio.sleep(10),name="Waiting test")
        result = await asyncio.wait_for(waiting_task,5)
        await ctx.send(result.__repr__())

    async def edit_table(self, table_data, phase=0):
        #   table_data: {
        #       author : discord.Member, (0)
        #       channel : discord.TextChannel, (0) (only for edition)
        #       title : str, (1)
        #       description : str, (2)
        #       creation_time : int, (0)
        #       player_role : discord.Role, (4)
        #       gm_role : discord.Role, (5)
        #       inscription_time : int, (3)
        #       announced : int (6)
        #   }
        logger.debug(f"edit_table invoked (phase {phase})")
        
        channel: discord.TextChannel = table_data["channel"]
        author_id: str = str(table_data["author"].id)
        channel_id: str = str(table_data["channel"].id)

        input_data: Any = self.buffer[author_id]["task_input"]


        if phase == 0:

            info_embed = discord.Embed(
                title="1.Nom de la table",
                description="Envoies en message le nom de ta table"
            )

            await channel.send(embed=info_embed)

        if phase == 1:
            table_data["title"] = input_data

            info_embed = discord.Embed(
                title="2.Description de la table",
                description="Envoies en message la description de ta table (peut être long et formaté)"
            )

            await channel.send(embed=info_embed)

        if phase == 2:
            table_data["description"] = input_data

            info_embed = discord.Embed(
                title="3. Délai d'inscription",
                description="Pendant combien de temps pourra-t-on s'inscrire?\n"
                           +"(Exprimer en j/h/m/s  exemple: 3j30m)\n"
                           +"0 pour un temps illimité\n"
                           +"Tu peux toujours arrêter l'inscription via <ajouter commande>"
            )
            
            await channel.send(embed=info_embed)

        if phase == 3:

            total_time: int = 0
            parts: list = re.findall(r'[0-9]+[jhms]', input_data)
            scale = {'s': 1, 'm': 60, 'h': 3600, 'j': 86400}
            for part in parts:
                unit: str = part[-1]
                value: int = int(part[:-1])
                total_time += value * scale[unit]
            
            table_data["inscription_time"] = total_time

            info_embed = discord.Embed(
                title="4. Rôle joueur",
                description="Envoies en message le nom du rôle joueur à créer.\n"
                           +"Il sera donné à tous ceux qui réagiront au message d'inscription.\n"
                           +"*(Il est modifiable à volonté)*"
            )

            await channel.send(embed=info_embed)
        
        if phase == 4:
            #Création du rôle de joueur
            permissions_joueur = discord.Permissions()
            player_role: discord.Role = await self.guild.create_role(
                name=input_data,
                color=discord.Color(0x88ff88),
                permissions=permissions_joueur,
                mentionable=True,
                reason=f'Rôle de joueur pour la table "{table_data["title"]}"'
            )
            table_data["player_role"] = player_role

            info_embed = discord.Embed(
                title="5. Rôle MJ",
                description="Envoies en message le nom du rôle MJ à créer.\n"
                           +"Il te sera assigné de base et tu pourra le donner à d'autres personnes avec <ajouter commande>.\n"
                           +"*(Il est modifiable à volonté)*"
            )

            await channel.send(embed=info_embed)
        
        if phase == 5:
            # Création du rôle de MJ
            permissions_mj = discord.Permissions()
            gm_role: discord.Role = await self.guild.create_role(
                name=input_data,
                color=discord.Color(0x8888ff),
                permissions=permissions_mj,
                mentionable=True,
                reason=f'Rôle de MJ pour la table "{table_data["title"]}"'
            )
            table_data["gm_role"] = gm_role

            # Récupération du rôle de joueur
            player_role: discord.Role = table_data["player_role"]

            # Création des permission de la catégorie
            category_permissions = {
                self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                gm_role: discord.PermissionOverwrite(
                    read_messages=True,
                    read_message_history=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_messages=True,
                    deafen_members=True,
                    mute_members=True,
                    move_members=True,
                    priority_speaker=True
                ),
                player_role: discord.PermissionOverwrite(
                    read_messages=True,
                    read_message_history=True,
                    send_messages=True,
                    attach_files=True
                )
            }
            # Création de la catégorie
            new_category = await self.guild.create_category(
                table_data["title"],
                overwrites=category_permissions,
                reason=f'Création de la table "{table_data["title"]}"'
            )

            await self.guild.create_text_channel(
                "jdr",
                category=new_category,
                reason=f'Création de la table "{table_data["title"]}"'
            )
            await self.guild.create_voice_channel(
                "vocal",
                category=new_category,
                reason=f'Création de la table "{table_data["title"]}"'
            )

            # Assignation du rôle de MJ
            gm: discord.Member = table_data["author"]
            await gm.add_roles(
                gm_role,
                reason=f'Créateur de la table "{table_data["title"]}"'
            )

            info_embed = discord.Embed(
                title="6. Annonce",
                description="Veux tu annoncer la table tout de suite et l'ouvrir aux inscriptions?\n"
                           +"O -> oui\n"
                           +"N'importe quoi d'autre -> non\n"
                           +f"(Tu pourra l'annoncer quand tu voudra avec =annoncer_table)"
            )

            await channel.send(embed=info_embed)

        if phase == 6:
            #TODO Créer la surveillance de réacions, la tâche de fermeture d'inscription

            # Si l'utilisateur a répondu oui, annoncer la table
            if input_data == "O":
                table_data["announced"] = int(time.time())

            table = Table(
                author=table_data["author"],
                title=table_data["title"],
                description=table_data["description"],
                player_role=table_data["player_role"],
                gm_role=table_data["gm_role"],
                inscription_time=table_data["inscription_time"],
                annouced=table_data["announced"]
            )

            if table.is_announced():
                anouncement_msg: discord.Message = await self.announce_table(table)
            
            #TODO Déplacer cette partie du code dans self.announce_table
            #* Callbacks (async lambdas don't exist :< )
            async def acb(mid, emoji, member):
                await member.add_roles(
                    table_data["player_role"],
                    reason='A réagi pour être joueur de la table'
                )
            
            async def rmcb(mid, emoji, member):
                await member.remove_roles(
                    table_data["player_role"],
                    reason='A enlevé sa réaction pour être joueur'
                )

            self.reaction_listener.add_callbacks(
                anouncement_msg.id,
                ":white_check_mark:",
                add_callbacks= [acb],
                rm_callbacks= [rmcb]
            )

            # Enregistrement de la table
            self.tables[table_data["author"]] = table
            del self.buffer[author_id]

            # On a fini la création, pas de phase suivante
            return

        #Si on est pas à la dernière phase:
        
        #On remet dans buffer les données nécéssaires pour guetter le prochain message
        self.buffer[author_id]["task_input"] = table_data

        #On attend le prochain input
        self.buffer[author_id]["task"] = asyncio.create_task(
            wait_for_seconds(
                300,
                cancel_handler=callback(self.edit_table,table_data,phase+1)
            )
        )
        

    async def announce_table(self, table: Table, channel=None) -> discord.Message:
        # Si non précisé, le canal est celui par défaut
        if channel is None:
            channel: discord.TextChannel = self.guild.get_channel(int(self.config["inscription_channel_id"]))
        
        #TODO Set reaction listener and inscription timer/limiter
        announcement_embed = self.generate_table_announcement_embed(table)
        return await channel.send(embed=announcement_embed)
        

    #*-*-*-*-*-*-*-*-*#
    #*-*-UTILITIES-*-*#
    #*-*-*-*-*-*-*-*-*#

    def generate_table_announcement_embed(self, table: Table) -> discord.Embed:
        author: discord.Member = table.get_author()
        return discord.Embed(
            title=table.get_title(),
            description=table.get_description()+"\n\n:white_check_mark: pour participer"
        ).set_author(name=author.display_name+" propose:", icon_url=author.avatar_url)

async def wait_for_seconds(secs, *, then=None, cancel_handler=None):
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

def callback(func, *args, **kwargs):
    async def inner():
        await func(*args, **kwargs)
    return inner