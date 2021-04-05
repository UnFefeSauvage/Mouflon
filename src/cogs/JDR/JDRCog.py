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
        logger.info("Initialisation du module JDR... (pre-connexion)")
        self.bot: discord.Client = bot
        self.resource_manager = resource_manager
        self.reaction_listener: ReactionListener = ReactionListener()
        self.tables: dict = {}
        self.tasks: dict = {}
        self.buffer: dict = {}
        self.guild: discord.Guild = None

        self.config = json.loads(self.resource_manager.read("JDR/config.json"))




    #*-*-*-*-*-*-*-*-*-*#
    #*-*-*LISTENERS*-*-*#
    #*-*-*-*-*-*-*-*-*-*#

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Initialisation du module JDR... (post-connexion)")
        logger.info("Récupération de la guilde associée...")
        #Récupération de la guilde
        self.guild: discord.Guild = self.bot.get_guild(int(self.config["guild_id"]))

        logger.info("Récupération du canal d'annonce")
        #Récupération du channel d'inscription
        self.inscription_channel: discord.TextChannel = self.guild.get_channel(int(self.config["inscription_channel_id"]))

        logger.info("Récupération des Tables...")
        logger.debug("Récupération des IDs des MJs...")
        GMs = os.listdir("resources/JDR/tables")
        logger.debug(f"MJs: {GMs}")

        #Chargement des tables existantes
        for GM_ID in GMs:
            self.tables[GM_ID] = {}
            logger.debug(f"Récupération des tables du MJ {GM_ID}...")
            GM_tables = os.listdir(f"resources/JDR/tables/{GM_ID}")
            for table_file in GM_tables:
                table_data = json.loads(self.resource_manager.read(f"JDR/tables/{GM_ID}/{table_file}"))
                table: Table = await self.table_from_dict(table_data)
                logger.debug(f"Table '{table.get_title()}' (id: {table_file[:-5]}) du MJ '{table.get_author()}' (id: {GM_ID}) récupérée!")
                if table.is_announced():
                    #TODO Traiter les réactions ajoutées ou retirées pendant la déconnexion
                    logger.debug("La table a un message d'annonce, mise en place des listeners...")
                    self.set_table_announcement_listeners(table)
                self.tables[GM_ID][str(table._creation_time)] = table

        logger.info("Initialisation du module JDR terminée!")
        #TODO Générer les tasks d'attente (si on en a)
    
    #FIXME Exécutêr cette méthode lors de l'arrêt du bot
    async def close(self):
        logger.info("Sauvegarde des tables avant arrêt...")
        for GM in self.tables:
            for table in self.tables[GM]:
                self.write_table_to_file(table)
        logger.info("Sauvegarde terminée!")
    
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_listener.process(
            chan_id=payload.channel_id,
            msg_id=payload.message_id,
            emoji=str(payload.emoji),
            member=self.guild.get_member(payload.user_id),
            add=True
        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_listener.process(
            chan_id=payload.channel_id,
            msg_id=payload.message_id,
            emoji=str(payload.emoji),
            member=self.guild.get_member(payload.user_id),
            add=False
        )

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

        await self.create_table(table_data)
    
    @commands.command()
    async def annuler_table(self, ctx):
        #TODO Coder l'annulation interactive d'une table de l'utilisateur
        pass
    

    #*-*-*-*-*-*-*#
    #*-*-TASKS-*-*#
    #*-*-*-*-*-*-*#

    async def create_table(self, table_data, phase=0):
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
        steps = [
            "Premier prompt",
            "Titre",
            "Description",
            "Délai d'inscription",
            "Rôle de joueur",
            "Rôle de MJ",
            "Annonce et enregistrement"
        ]
        logger.debug(f"create_table invoqué (phase {phase}: {steps[phase]})")
        
        channel: discord.TextChannel = table_data["channel"]
        author_id: str = str(table_data["author"].id)
        channel_id: str = str(table_data["channel"].id)

        input_data: Any = self.buffer[author_id]["task_input"]

        #* Premier prompt
        if phase == 0:

            info_embed = discord.Embed(
                title="1.Nom de la table",
                description="Envoies en message le nom de ta table"
            )

            await channel.send(embed=info_embed)

        #* Titre
        if phase == 1:
            table_data["title"] = input_data

            info_embed = discord.Embed(
                title="2.Description de la table",
                description="Envoies en message la description de ta table (peut être long et formaté)"
            )

            await channel.send(embed=info_embed)

        #* Description
        if phase == 2:
            table_data["description"] = input_data
            #FIXME Solution temporaire pour passer l'étape "délai d'inscription"
            phase += 1
            #TODO Prendre en charge les délais d'inscription ou s'en débarasser complètement
            """
            info_embed = discord.Embed(
                title="3. Délai d'inscription",
                description="Pendant combien de temps pourra-t-on s'inscrire?\n"
                           +"(Exprimer en j/h/m/s  exemple: 3j30m)\n"
                           +"0 pour un temps illimité\n"
                           +"Tu peux toujours arrêter l'inscription via <ajouter commande>"
            )
            
            await channel.send(embed=info_embed)
            """

        #* Délai d'inscription (désactivé)
        if phase == 3:
            #FIXME Solution temporaire pour passer l'étape "délai d'inscription"
            table_data["inscription_time"] = 0
            """
            total_time: int = 0
            parts: list = re.findall(r'[0-9]+[jhms]', input_data)
            scale = {'s': 1, 'm': 60, 'h': 3600, 'j': 86400}
            for part in parts:
                unit: str = part[-1]
                value: int = int(part[:-1])
                total_time += value * scale[unit]
            
            table_data["inscription_time"] = total_time
            """
            info_embed = discord.Embed(
                title="3. Rôle joueur",
                description="Envoies en message le nom du rôle joueur à créer.\n"
                           +"Il sera donné à tous ceux qui réagiront au message d'inscription.\n"
                           +"*(Il est modifiable à volonté)*"
            )

            await channel.send(embed=info_embed)
        
        #* Rôle de joueur
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
                title="4. Rôle MJ",
                description="Envoies en message le nom du rôle MJ à créer.\n"
                           +"Il te sera assigné de base et tu pourra le donner à d'autres personnes avec <ajouter commande>.\n"
                           +"*(Il est modifiable à volonté)*"
            )

            await channel.send(embed=info_embed)
        
        #* Rôle de MJ
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
                title="5. Annonce",
                description="Veux tu annoncer la table tout de suite et l'ouvrir aux inscriptions?\n"
                           +"O -> oui\n"
                           +"N'importe quoi d'autre -> non\n"
                           +f"(Tu pourra l'annoncer quand tu voudra avec =annoncer_table)"
            )

            await channel.send(embed=info_embed)

        #* Annonce et enregistrement
        if phase == 6:
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
                announced=table_data["announced"]
            )

            if table.is_announced():
                await self.announce_table(table)
            
            # Enregistrement de la table
            self._add_table(author_id, table)
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
                cancel_handler=callback(self.create_table,table_data,phase+1)
            )
        )
        

    async def announce_table(self, table: Table, channel=None) -> discord.Message:
        # Si non précisé, le canal est celui par défaut
        if channel is None:
            channel: discord.TextChannel = self.guild.get_channel(int(self.config["inscription_channel_id"]))
        
        announcement_embed = self.generate_table_announcement_embed(table)
        message: discord.Message = await channel.send(embed=announcement_embed)

        table.set_announcement_message(message)

        await message.add_reaction("✅")

        self.set_table_announcement_listeners(table)

        self.write_table_to_file(table)
        return message
        

    #*-*-*-*-*-*-*-*-*#
    #*-*-UTILITIES-*-*#
    #*-*-*-*-*-*-*-*-*#

    def _add_table(self, author_id: str, table: Table) -> None:
        # Conversion of int for convenience
        if isinstance(author_id, int):
            author_id = str(author_id)
        
        if not isinstance(author_id, str):
            raise TypeError(f"Expected a user id! (got {type(author_id)} instead)")
        
        if not author_id in self.tables:
            self.tables[author_id] = {}
        
        self.tables[author_id][str(table.get_creation_time())] = table
        


    def generate_table_announcement_embed(self, table: Table) -> discord.Embed:
        author: discord.Member = table.get_author()
        return discord.Embed(
            title=table.get_title(),
            description=table.get_description()+"\n\n✅ pour participer"
        ).set_author(name=author.display_name+" propose:", icon_url=author.avatar_url)

    def write_table_to_file(self, table: Table) -> None:
        table_data = table.to_dict()
        self.resource_manager.write(
            f"JDR/tables/{table_data['author_id']}/{table_data['creation_time']}.json",
            json.dumps(table_data),
            True
        )
    
    async def table_from_dict(self, data: dict):
        if data["announced"]:
            try:
                channel: discord.TextChannel = self.guild.get_channel(data["announcement_channel_id"])
                message = await channel.fetch_message(data["announcement_message_id"])
            except discord.NotFound:
                logger.info(f"The announcement message for the table '{data['title']}' cannot be found! Making the table unannounced...")
                data["announced"] = None
                message = None
        else:
            message = None
        
        return Table(
            author             = self.guild.get_member(data["author_id"]),
            title              = data["title"],
            description        = data["description"],
            player_role        = self.guild.get_role(data["player_role_id"]),
            gm_role            = self.guild.get_role(data["gm_role_id"]),
            inscription_time   = data["inscription_time"],
            creation_time      = data["creation_time"],
            announced          = data["announced"],
            announcement_msg   = message
        )
    
    def set_table_announcement_listeners(self, table: Table):
        message: discord.Message = table.get_annoucement_message()
        #* Callbacks (async lambdas don't exist :< )
        async def acb(mid, emoji, member):
            if member.bot:
                return
            
            await member.add_roles(
                table.get_player_role(),
                reason='A réagi pour être joueur de la table'
            )
        
        async def rmcb(mid, emoji, member):
            if member.bot:
                return
            
            await member.remove_roles(
                table.get_player_role(),
                reason='A enlevé sa réaction pour être joueur'
            )
        
        self.reaction_listener.add_callbacks(
            message.channel.id,
            message.id,
            "✅",
            add_callbacks= [acb],
            rm_callbacks= [rmcb]
        )

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