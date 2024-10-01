import discord
import time
import datetime
import asyncio
import random
import json
import os
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
load_dotenv()
Mongo = os.getenv('mongo')
class Gamble(commands.GroupCog):

    def __init__(self, client):
        self.client = client
        self.invites = {}
        self.cluster = AsyncIOMotorClient(Mongo)
        self.db = self.cluster["Banker"]
        self.collection = self.db["UserData"]
        self.tax_collection = self.db["Tax"]
        self.bets = []
        self.roulette_message_id = 1263297467328364707
        self.roulette_task.start()
        self.human_count_channel_id = 1282885000970108948
        self.money_channel_id = 1282885042170757242
        self.update_stats.start()

    def format_user_data(self, user_id):
        return {
            "_id": str(user_id),
            "wallet": 0,  # Starting amount for demonstration
            "bank": 0,
            "bag": [],
        }
        
    @tasks.loop(minutes=10)  # Update every 10 minutes (adjust as needed)
    async def update_stats(self):
        # Update human member count
        await self.update_human_member_count()

        # Update total BFD in circulation
        await self.update_total_money_in_circulation()

    async def update_human_member_count(self):
        guild = self.client.get_guild(1145625417898803232)  # Replace with your guild ID
        human_count = sum(1 for member in guild.members if not member.bot)

        # Get the voice channel for human member count
        channel = guild.get_channel(self.human_count_channel_id)
        if channel:
            await channel.edit(name=f"Human Members: {human_count}")

    async def update_total_money_in_circulation(self):
        # Sum all wallet amounts
        total_money = 0
        async for document in self.collection.find():
            total_money += document.get("wallet", 0)
        total_money = round(total_money)
        formatted_total_money = f"{total_money:,}"
        # Get the voice channel for total money
        guild = self.client.get_guild(1145625417898803232)  # Replace with your guild ID
        channel = guild.get_channel(self.money_channel_id)
        if channel:
            await channel.edit(name=f"Total BFD: {formatted_total_money}")

    async def get_user_data(self, user_id):
        user = await self.collection.find_one({"_id": str(user_id)})
        if user is None:
            user = self.format_user_data(user_id)
            await self.collection.insert_one(user)
        return user

    async def update_user_wallet(self, user_id, amount):
        await self.collection.update_one({"_id": str(user_id)}, {"$inc": {"wallet": amount}})

    @app_commands.command(name="bet", description="Place a bet on the roulette table")
    @app_commands.describe(amount="Amount you want to bet")
    @app_commands.describe(bet_type = "The type of thing you want to bet either enter Color or Number.")
    @app_commands.describe(value = "Either be red, black or a number between 1 and 36")
    async def bet(self, interaction: discord.Interaction, amount: int, bet_type: str, value: str):
        user = interaction.user
        user_data = await self.get_user_data(user.id)

        if amount <= 0:
            await interaction.response.send_message("Bet amount must be greater than zero.", ephemeral=True)
            return

        if user_data["wallet"] < amount:
            await interaction.response.send_message("You don't have enough money to place this bet.", ephemeral=True)
            return

        if bet_type.lower() not in ["number", "color"]:
            await interaction.response.send_message("Invalid bet type. Choose 'number' or 'color'.", ephemeral=True)
            return

        if bet_type.lower() == "number":
            try:
                value_int = int(value)
                if not (0 <= value_int <= 36):
                    raise ValueError
            except ValueError:
                await interaction.response.send_message("For a number bet, the value must be an integer between 0 and 36.", ephemeral=True)
                return

        if bet_type.lower() == "color" and value.lower() not in ["red", "black"]:
            await interaction.response.send_message("For a color bet, the value must be 'red' or 'black'.", ephemeral=True)
            return

        self.bets.append({"user": user, "type": bet_type.lower(), "value": value.lower(), "amount": amount})
        await self.update_user_wallet(user.id, -amount)
        await interaction.response.send_message(f"{user.mention} placed a bet of {amount} on {bet_type} {value}.")

    @tasks.loop(minutes=2)
    async def roulette_task(self):
        sec = 438537782542073878

        result = random.randint(0, 36)
        color = "red" if result % 2 == 0 else "black"
        
        current_time = datetime.datetime.now()
        future_time = current_time + datetime.timedelta(minutes=2)

        embed = discord.Embed(
            title="Roulette Result",
            description=f"The ball landed on {color} {result}",
            timestamp=current_time
        )
        embed.add_field(name="Next Game", value=f"<t:{int(future_time.timestamp())}:R>")


        if self.roulette_message_id is None:
            message = await self.client.get_channel(1258663171032481793).send(embed=embed)
            self.roulette_message_id = message.id
        else:
            channel = self.client.get_channel(1258663171032481793)
            message = await channel.fetch_message(self.roulette_message_id)
            await message.edit(embed=embed)

        winners = []
        for bet in self.bets:
            user = bet["user"]
            amount = bet["amount"]
            win = False

            if bet["type"] == "number" and int(bet["value"]) == result:
                winnings = amount * 4
                await self.update_user_wallet(user.id, winnings)
                await self.update_user_wallet(sec, -winnings)
                win = True
            elif bet["type"] == "color" and bet["value"] == color:
                winnings = amount * 2
                await self.update_user_wallet(user.id, winnings)
                await self.update_user_wallet(sec, -winnings)
                win = True
            else:
                sec = 438537782542073878
                await self.update_user_wallet(sec, amount)

            if win:
                winners.append((user, winnings))

        if winners:
            channel2 = self.client.get_channel(1252513098057912441)
            await channel2.send(content=f"Congratulations to the winners: {', '.join([winner[0].mention for winner in winners])}!")
            await message.edit(content=f"Congratulations to the winners: {', '.join([winner[0].mention for winner in winners])}!")
            for winner, winnings in winners:
                await winner.send(f"Congratulations! You won {winnings} in the roulette game!")
        else:
            
            await message.edit(content="No winners this time.")

        self.bets = []

    @app_commands.command(name="slots", description="Play the slots game")
    async def slots(self, interaction: discord.Interaction, amount: int):
        user = interaction.user
        user_data = await self.get_user_data(user.id)

        if amount <= 0:
            await interaction.response.send_message("Bet amount must be greater than zero.", ephemeral=True)
            return

        if user_data["wallet"] < amount:
            await interaction.response.send_message("You don't have enough money to play.", ephemeral=True)
            return

        emojis = ["🍒", "🍋", "🔔", "🍀", "💎"]
        result = random.choices(emojis, k=3)

        if result[0] == result[1] == result[2]:
            winnings = amount * 10
            await self.update_user_wallet(user.id, winnings)
            await interaction.response.send_message(f"Congratulations {user.mention}, you won {winnings}! {' '.join(result)}", ephemeral=True)
        else:
            sec = 438537782542073878
            await self.update_user_wallet(user.id, -amount)
            await self.update_user_wallet(sec, +amount)
            await interaction.response.send_message(f"Sorry {user.mention}, you lost your bet of {amount}. {' '.join(result)}", ephemeral=True)


async def setup(client):
    await client.add_cog(Gamble(client))
