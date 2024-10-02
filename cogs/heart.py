import discord
import time
import datetime
import asyncio
import json
from discord import app_commands
from discord.ext import commands, tasks
from discord.interactions import Interaction
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from discord import ui
import os
import requests

load_dotenv()
Mongo = os.getenv("mongo")
# ______________________________


class heart(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cluster = AsyncIOMotorClient(Mongo)
        self.db = self.cluster["PRIME"]
        self.mainsub = self.db["MainServer/Subserver"]
        self.BOT_TOKEN = os.getenv("DISCORD_TOKEN")

        self.tax_collection = self.db["Tax"]

    async def is_site_admin(self, user_id: str):
        user = await self.db.sitea.find_one({"user_id": user_id, "site_admin": True})
        return bool(user)

    async def is_superadmin(self, user_id: str):
        # The primary Superadmin is user 786788350160797706
        if user_id == "786788350160797706":
            return True

        # Check if the user is stored as a Superadmin in the DB
        user = await self.db.superadmins.find_one({"user_id": user_id})
        return bool(user)

    @app_commands.command(description="Adds a sub Server to the Main server list")
    async def addsubserver(
        self,
        interaction: discord.Interaction,
        main_server_id: str,
        sub_server_id: str,
        name: str,
    ):
        if not (
            await self.is_site_admin(str(interaction.user.id))
            or await self.is_superadmin(str(interaction.user.id))
        ):
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return

        main_server = await self.db.servers.find_one(
            {"server_id": main_server_id, "type": "main"}
        )
        if not main_server:
            await interaction.response.send_message(
                f"Main server with ID {main_server_id} not found."
            )
        else:
            await self.db.servers.insert_one(
                {
                    "server_id": sub_server_id,
                    "name": name,
                    "type": "sub",
                    "linked_servers": [],
                }
            )
            await self.db.servers.update_one(
                {"server_id": main_server_id},
                {"$push": {"linked_servers": sub_server_id}},
            )
            await interaction.response.send_message(
                f"Sub-server {name} added under main server {main_server_id}."
            )

    @app_commands.command(description="views sub servers in a main server")
    async def viewsubservers(
        self, interaction: discord.Interaction, main_server_id: str
    ):
        if not (
            await self.is_site_admin(str(interaction.user.id))
            or await self.is_superadmin(str(interaction.user.id))
        ):
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return

        main_server = await self.db.servers.find_one(
            {"server_id": main_server_id, "type": "main"}
        )
        if not main_server:
            await interaction.response.send_message(
                f"No main server found with ID {main_server_id}."
            )
        else:
            sub_servers = await self.db.servers.find(
                {"server_id": {"$in": main_server["linked_servers"]}}
            ).to_list(length=100)
            sub_server_names = [server["name"] for server in sub_servers]
            await interaction.response.send_message(
                f"Sub-servers linked to {main_server['name']}: {', '.join(sub_server_names)}"
            )

    @app_commands.command(description="Views main servers")
    async def viewmainservers(self, interaction: discord.Interaction):
        if not (
            await self.is_site_admin(str(interaction.user.id))
            or await self.is_superadmin(str(interaction.user.id))
        ):
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return

        main_servers = await self.db.servers.find({"type": "main"}).to_list(length=100)
        main_server_names = [server["name"] for server in main_servers]
        await interaction.response.send_message(
            f"Main servers: {', '.join(main_server_names)}"
        )

    @app_commands.command(description="Attempt to give some news to another channel")
    async def autofollow(self, interaction: discord.Interaction):
        if not (
            await self.is_site_admin(str(interaction.user.id))
            or await self.is_superadmin(str(interaction.user.id))
        ):
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return
        guild = interaction.guild
        newsletter_channel = await guild.create_text_channel("bfi-news")
        bot_logs_channel = await guild.create_text_channel("P.R.I.M.E.-logs")

        await interaction.send(
            f"Newsletter and bot logs channels created: {newsletter_channel.mention}, {bot_logs_channel.mention}"
        )
        # Ensure the bot has necessary permissions in the target channel
        if not interaction.channel.permissions_for(
            interaction.guild.me
        ).manage_webhooks:
            await interaction.response.send_message(
                "I need the 'Manage Webhooks' permission to follow the news channel."
            )
            return

        # URL to follow the channel
        NEWS_CHANNEL_ID = 1253742466725580921
        LOGS_CHANNEL_ID = 1252513098057912441
        url = f"https://discord.com/api/v10/channels/{NEWS_CHANNEL_ID}/followers"
        urla = f"https://discord.com/api/v10/channels/{LOGS_CHANNEL_ID}/followers"

        # Data to send with the follow request
        data = {
            # The ID of the target channel in the current server
            "webhook_channel_id": newsletter_channel
        }
        dataa = {
            # The ID of the target channel in the current server
            "webhook_channel_id": bot_logs_channel
        }

        # Headers including bot token for authentication
        headers = {
            "Authorization": f"Bot {self.BOT_TOKEN}",
            "Content-Type": "application/json",
        }

        # Make the request
        response = requests.post(url, json=data, headers=headers)
        responses = requests.post(urla, json=dataa, headers=headers)

        if response.status_code == 200 and responses.status_code == 200:
            await interaction.response.send_message(
                "Successfully followed the news channel! "
            )
        else:
            await interaction.response.send_message(
                f"Failed to follow the channel: {response.status_code} - {response.text}"
            )

    @app_commands.command(description="Adds a main server to the list")
    async def addmainserver(
        self, interaction: discord.Interaction, server_id: str, name: str
    ):
        if not await self.is_superadmin(str(interaction.user.id)):
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return
        server = await self.db.servers.find_one({"server_id": server_id})
        if server:
            await interaction.response.send_message("Main server already exists.")
        else:
            await self.db.servers.insert_one(
                {
                    "server_id": server_id,
                    "name": name,
                    "type": "main",
                    "linked_servers": [],
                }
            )
            await interaction.response.send_message(
                f"Main server {name} added with ID {server_id}."
            )

    @app_commands.command(description="Adds a Site Admin")
    async def siteadmin(self, interaction: discord.Interaction, user_id: str):
        if not await self.is_superadmin(str(interaction.user.id)):
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return

        user = await self.db.sitea.find_one({"user_id": user_id})
        if not user:
            await self.db.sitea.insert_one({"user_id": user_id, "site_admin": True})
        else:
            await self.db.sitea.update_one(
                {"user_id": user_id}, {"$set": {"site_admin": True}}
            )
        await interaction.response.send_message(f"User {user_id} is now a site admin.")

    @app_commands.command(description="Removes a Site Admin")
    async def rsiteadmin(self, interaction: discord.Interaction, user_id: str):
        if not await self.is_superadmin(str(interaction.user.id)):
            await interaction.response.send_message(
                "You do not have permission to use this command."
            )
            return

        result = await self.db.sitea.update_one(
            {"user_id": user_id}, {"$set": {"site_admin": False}}
        )
        if result.matched_count == 0:
            await interaction.response.send_message(f"User {user_id} not found.")
        else:
            await interaction.response.send_message(
                f"Site admin privileges removed from user {user_id}."
            )

    @app_commands.command(description="Adds a SUP")
    async def addsuperadmin(self, interaction: discord.Interaction, user_id: str):
        if str(interaction.user.id) != "786788350160797706":
            await interaction.response.send_message(
                "Only the root Superadmin can use this command."
            )
            return

        user = await self.db.superadmins.find_one({"user_id": user_id})
        if user:
            await interaction.response.send_message("User is already a Superadmin.")
        else:
            await self.db.superadmins.insert_one({"user_id": user_id})
            await interaction.response.send_message(
                f"User {user_id} has been added as a Superadmin."
            )

    @app_commands.command(description="Removes a super admin")
    async def removesuperadmin(self, interaction: discord.Interaction, user_id: str):
        if str(interaction.user.id) != "786788350160797706":
            await interaction.response.send_message(
                "Only the root Superadmin can use this command."
            )
            return

        result = await self.db.superadmins.delete_one({"user_id": user_id})
        if result.deleted_count == 0:
            await interaction.response.send_message(
                f"User {user_id} is not a Superadmin."
            )
        else:
            await interaction.response.send_message(
                f"Superadmin privileges removed from user {user_id}."
            )

    @app_commands.command(description="Check your balance in a server.")
    async def bal(self, interaction: discord.Interaction, member: discord.Member):
        interaction.response.send_message("This is a filler text.")

    @app_commands.command(description="Create a bug report")
    async def report(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReportModal(self.client))


class ReportModal(ui.Modal, title="Report"):
    def __init__(self, client):
        super().__init__()
        self.client = client

    reason = ui.TextInput(
        label="Reason",
        style=discord.TextStyle.short,
        placeholder="Why you are reporting the bug",
        required=True,
    )
    bug = ui.TextInput(
        label="Bug Description",
        style=discord.TextStyle.paragraph,
        placeholder="Describe what the bot did that it shouldn't have",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        dev = self.client.get_user(786788350160797706)
        em = discord.Embed(
            title="**Bug Report**",
            description=f"**Who Reported** \n {interaction.user.name} aka {interaction.user.id} \n **Why** \n {self.reason.value} \n **Report of action of bug** \n {self.bug.value} \n **Bot** \n BlackForge Industries",
            timestamp=datetime.datetime.now(),
        )
        await dev.send(embed=em)
        await interaction.channel.send(
            "Bug reported! \n **NOTE: ANY REPORTS NOT ABOUT THE BOT WILL RESULT IN MODERATOR ACTION!!!**"
        )


async def setup(client):
    await client.add_cog(heart(client))
