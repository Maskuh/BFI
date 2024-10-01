import discord
import time
import datetime
import asyncio
import random
import json
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
load_dotenv()
#______________________________

class gang(commands.GroupCog):
    
    def __init__(self, client):
        self.client = client
        self.invites = {}
        self.cluster = AsyncIOMotorClient("mongodb+srv://Banker:l3BY9knLXptBbDS1@cluster0.qnihg.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.cluster["Banker"]
        self.collection = self.db["UserData"]
        self.tax_collection = self.db["Tax"]
        self.gang_collection = self.db["Gang"]
    def format_user_data(self, user_id):
        return {
            "_id": str(user_id),
            "wallet": 0,
            "bank": 0,
            "bag": [
            ],
        }
        
    
    async def create_account(self, user_id):
        user_data = self.format_user_data(user_id)
        await self.collection.insert_one(user_data)

    async def open_account(self, user):
        user_id = str(user.id)
        user_data = await self.collection.find_one({"_id": user_id})

        if not user_data:
            await self.create_account(user_id)
            user_data = await self.collection.find_one({"_id": user_id})

        return user_data

    async def get_bank_data(self):
        result = await self.tax_collection.find_one({"_id": "tax"})
        if result:
            return result.get("data", {}), result.get("tax", 7.25)
        else:
            return {}, 7.25

    async def save_bank_data(self, user_id, users_data):
        # Convert the user_id to string if it's an integer
        user_id = str(user_id)

        # Get the user data from the database
        user_data = await self.collection.find_one({"_id": user_id})

        # If the user data doesn't exist in the database, create a new document
        if not user_data:
            await self.open_account(user_id)

        # Save the updated user data back to the database
        await self.collection.update_one({"_id": user_id}, {"$set": users_data}, upsert=True)



    def get_gang_size_limit(self, size):
        size_limits = {
            "tiny": 3,
            "small": 4,
            "medium": 6,
            "large": 10
        }
        return size_limits.get(size.lower(), 0)

    @app_commands.command(description="Create a gang")
    @app_commands.describe(name="The Name of your gang")
    @app_commands.describe(size="The size of your gang options: tiny, small, medium, large")
    async def create(self, interaction: discord.Interaction, name: str, size: str):
        # Check if the user has enough balance to create a gang
        tax_result = await self.tax_collection.find_one({"_id": "tax"})
        tax = tax_result["tax"]["tax_amount"] if tax_result else 7.25
        
        cost = 0
        if size.lower() == "tiny":
            cost = 0
        elif size.lower() == "small":
            cost = 10
        elif size.lower() == "medium":
            cost = 30
        elif size.lower() == "large":
            cost = 60
        else:
            await interaction.response.send_message("Invalid gang size specified.")
            return
        
        total_cost = cost + cost * (tax / 100)

        users_data = await self.open_account(interaction.user)

        # Check if the user is already in a gang
        existing_gang_data = await self.gang_collection.find_one({"members": interaction.user.id})
        if existing_gang_data:
            await interaction.response.send_message("You are already in a gang; you can't create another.")
            return

        # Check if the user has enough money
        if users_data["wallet"] < total_cost:
            await interaction.response.send_message(f"You don't have enough money to create a gang. The total cost with tax is {total_cost} money.")
            return

        # Deduct the cost from the user's wallet
        users_data["wallet"] -= total_cost
        await self.save_bank_data(interaction.user.id, users_data)

        existing_role = discord.utils.get(interaction.guild.roles, name=f"[G]{name}")
        if existing_role:
            await interaction.response.send_message("A gang with that name already exists.")
            return

        # Create the role for the gang with a random color
        random_color = discord.Colour(random.randint(0, 0xFFFFFF))
        gang_role = await interaction.guild.create_role(name=f"[G]{name}", colour=random_color)

        # Add the role to the user who created the gang
        await interaction.user.add_roles(gang_role)

        # Create the category "gangs" if it doesn't exist
        category_name = "[GANGS]"
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        if not category:
            category = await interaction.guild.create_category(category_name)

        # Create the channel for the gang in the "gangs" category
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            gang_role: discord.PermissionOverwrite(read_messages=True)
        }
        await category.create_text_channel(name, overwrites=overwrites)

        # Insert the gang data into the database
        await self.gang_collection.insert_one({
            "user_id": interaction.user.id,
            "gang_name": name,
            "gang_size": size,
            "members": [interaction.user.id]
        })

        await interaction.response.send_message(f"Congratulations! You have created the gang '{name}' with a total cost of {total_cost} money.")

    @app_commands.command(description="Remove your gang")
    async def remove(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        # Find the user's gang in the database
        gang_data = await self.gang_collection.find_one({"user_id": user_id})
        if not gang_data:
            await interaction.response.send_message("You don't have a gang to remove.")
            return

        gang_name = gang_data["gang_name"]

        # Find and delete the gang role
        gang_role = discord.utils.get(interaction.guild.roles, name=f"[G]{gang_name}")
        if gang_role:
            await gang_role.delete()

        # Find and delete the gang channel
        category_name = "[GANGS]"
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        if category:
            gang_channel = discord.utils.get(category.channels, name=gang_name)
            if gang_channel:
                await gang_channel.delete()

        # Remove the gang data from the database
        await self.gang_collection.delete_one({"user_id": user_id})

        # Update the user's bag
        users_data = await self.open_account(interaction.user)
        new_bag = []
        for item in users_data["bag"]:
            if item["item"] not in ["Gang", "Gang-size", "Gang-members-amount"]:
                new_bag.append(item)
        users_data["bag"] = new_bag

        await self.save_bank_data(interaction.user.id, users_data)

        await interaction.response.send_message(f"Your gang '{gang_name}' has been removed successfully.")

    @app_commands.command(description="Invite a member to your gang")
    @app_commands.describe(member="The member to invite to your gang")
    async def invite(self, interaction: discord.Interaction, member: discord.Member):
        user_id = interaction.user.id

        # Find the user's gang in the database
        gang_data = await self.gang_collection.find_one({"user_id": user_id})
        if not gang_data:
            await interaction.response.send_message("You don't have a gang to invite members to.")
            return

        # Check if the member already belongs to a gang
        member_gang_data = await self.gang_collection.find_one({"members": member.id})
        if member_gang_data:
            await interaction.response.send_message(f"{member.display_name} is already a member of another gang.")
            return

        gang_size_limit = self.get_gang_size_limit(gang_data["gang_size"])
        if len(gang_data["members"]) >= gang_size_limit:
            await interaction.response.send_message(f"Your gang is already at the maximum size of {gang_size_limit} members.")
            return

        gang_name = gang_data["gang_name"]

        # Send the invitation to the member
        self.invites[member.id] = user_id
        await member.send(f"You have been invited to join the gang '{gang_name}'. Use the `/accept` command to join the gang.")

        await interaction.response.send_message(f"{member.display_name} has been invited to the gang '{gang_name}'.")

    @app_commands.command(description="Accept a gang invitation")
    async def accept(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        # Check if the user has an invitation
        if user_id not in self.invites:
            await interaction.response.send_message("You don't have any gang invitations.")
            return

        inviter_id = self.invites.pop(user_id)

        # Find the inviter's gang in the database
        gang_data = await self.gang_collection.find_one({"user_id": inviter_id})
        if not gang_data:
            await interaction.response.send_message("The gang you were invited to no longer exists.")
            return

        gang_name = gang_data["gang_name"]

        # Add the member to the gang role
        gang_role = discord.utils.get(interaction.guild.roles, name=f"[G]{gang_name}")
        if gang_role:
            await interaction.user.add_roles(gang_role)

        # Update the gang data in the database
        await self.gang_collection.update_one(
            {"user_id": inviter_id},
            {"$push": {"members": user_id}}
        )

        await interaction.response.send_message(f"You have joined the gang '{gang_name}'.")
    @app_commands.command(description="Remove a member from your gang")
    @app_commands.describe(member="The member to remove from your gang")
    async def remove_member(self, interaction: discord.Interaction, member: discord.Member):
        user_id = interaction.user.id

        # Find the user's gang in the database
        gang_data = await self.gang_collection.find_one({"user_id": user_id})
        if not gang_data:
            await interaction.response.send_message("You don't have a gang to remove members from.")
            return

        gang_name = gang_data["gang_name"]

        # Check if the member is in the gang
        if member.id not in gang_data["members"]:
            await interaction.response.send_message(f"{member.display_name} is not a member of your gang.")
            return

        # Remove the member from the gang role
        gang_role = discord.utils.get(interaction.guild.roles, name=f"[G]{gang_name}")
        if gang_role:
            await member.remove_roles(gang_role)

        # Update the gang data in the database
        await self.gang_collection.update_one(
            {"user_id": user_id},
            {"$pull": {"members": member.id}}
        )

        await interaction.response.send_message(f"{member.display_name} has been removed from the gang '{gang_name}'.")

    @app_commands.command(description="Upgrade your gang size")
    @app_commands.describe(new_size="The new size of your gang options: small, medium, large")
    async def upgrade(self, interaction: discord.Interaction, new_size: str):
        user_id = interaction.user.id

        # Define upgrade costs
        upgrade_costs = {
            ("tiny", "small"): 10,
            ("small", "medium"): 20,
            ("medium", "large"): 30
        }

        # Get the user's current gang data
        gang_data = await self.gang_collection.find_one({"user_id": user_id})
        if not gang_data:
            await interaction.response.send_message("You don't have a gang to upgrade.")
            return

        current_size = gang_data["gang_size"]
        if current_size == "large":
            await interaction.response.send_message("Your gang is already at the maximum size.")
            return

        valid_upgrade = (current_size, new_size.lower()) in upgrade_costs
        if not valid_upgrade:
            await interaction.response.send_message(f"Invalid upgrade path from {current_size} to {new_size}.")
            return

        # Calculate the upgrade cost
        upgrade_cost = upgrade_costs[(current_size, new_size.lower())]

        # Check if the user has enough money for the upgrade
        users_data = await self.open_account(interaction.user)
        if users_data["wallet"] < upgrade_cost:
            await interaction.response.send_message(f"You don't have enough money to upgrade your gang. The upgrade cost is {upgrade_cost} money.")
            return

        # Deduct the cost from the user's wallet
        users_data["wallet"] -= upgrade_cost
        await self.save_bank_data(interaction.user.id, users_data)

        # Update the gang size in the database
        await self.gang_collection.update_one(
            {"user_id": user_id},
            {"$set": {"gang_size": new_size.lower()}}
        )

        await interaction.response.send_message(f"Congratulations! Your gang has been upgraded to '{new_size}' size for {upgrade_cost} money.")
            

async def setup(client):
     await client.add_cog(gang(client)) 
