import discord
import time
import datetime
import asyncio
import random
import json
from discord import app_commands
from discord.ext import commands, tasks
from discord.interactions import Interaction
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from discord import ui
load_dotenv()
#______________________________

class heart(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cluster = AsyncIOMotorClient("mongodb+srv://Banker:l3BY9knLXptBbDS1@cluster0.qnihg.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.cluster["Banker"]
        self.collection = self.db["UserData"]
        self.shop_collection = self.db['Shops']
        self.shopa_collection = self.db['Shops2']
        self.tax_collection = self.db["Tax"]
        
        
    def cog_unload(self):
        self.update_stats.cancel()

    def format_user_data(self, user_id):
        return {
            "_id": str(user_id),
            "wallet": 0,
            "bag": [
            ],
        }
        
    @commands.Cog.listener()
    async def on_message(self, message):
    # Ignore bot's own messages
        if message.author == self.client.user:
            return

    # Forward messages only from the specified source channel
        if message.channel.id == 1236185230424014950:
            if "Revive" in message.content:
                modified_content = message.content.replace("@everyone", "[everyone]").replace("@here", "[here]")
            else:
                modified_content = message.content.replace("@everyone", "<@&1287592885423706264>").replace("@here", "<@&1287592885423706264>")
            destination_channel = self.client.get_channel(1287304228217552977)
            await destination_channel.send(modified_content)
        if message.channel.id == 1182575798662738040:
            if "Revive" in message.content:
                modified_content = message.content.replace("@everyone", "[everyone]").replace("@here", "[here]")
            else:
                modified_content = message.content.replace("@everyone", "<@&1287691246734807054>").replace("@here", "<@&1287691246734807054>")
            destination_channel = self.client.get_channel(1287088077252333608)
            await destination_channel.send(modified_content)



    @app_commands.command(description="Check how much you have in your wallet and bank")
    @app_commands.describe(member="Who to check the balance of")
    async def bal(self, interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        user = member
        users_data = await self.open_account(user)
        wallet_amt = users_data["wallet"]

        embed = discord.Embed(title=f"{user.name}'s Balance", color=discord.Color.green())
        embed.add_field(name="BFD", value=f"{wallet_amt}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(description= "Give BFD to a user")
    @app_commands.describe(member= "The member you want to give BFD to")
    @app_commands.describe(amount= "The amount you want to give")
    @app_commands.describe(reason= "The Reason your giving amount to that person")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: float, reason: str = None):
        if interaction.user.id == member.id:
            await interaction.response.send_message(f"You can't give your self BFD!!")
            return
        
        if member.bot:
            await interaction.response.send_message("You can't give a bot BFD")
            return
        result = await self.tax_collection.find_one({"_id": "tax"})
        if result:
            tax = result["tax"]["tax_amount"]
        else:
            tax = 7.25

        giver_data = await self.open_account(interaction.user)  # Use interaction.user directly
        receiver_data = await self.open_account(member)
        total_gift = amount + amount * (tax / 100)
        if total_gift <= 0:
            await interaction.response.send_message("Amount must be greater than zero!")
            return

        if total_gift > giver_data["wallet"]:
            await interaction.response.send_message(f"You don't have enough BFD to give {amount} to {member.name}")
            return

        giver_data["wallet"] -= total_gift
        receiver_data["wallet"] += amount

        await self.save_bank_data(interaction.user.id, giver_data)
        await self.save_bank_data(member.id, receiver_data)
        channel = self.client.get_channel(1252513098057912441)
        em = discord.Embed(title="Given", description=f"**Giver** \n {interaction.user.mention} \n \n **Receiver** \n {member.mention} \n \n **Amount Given** \n {amount} BFD \n \n **Reason** \n {reason}", color=discord.Color.from_rgb(0, 255, 0), timestamp=datetime.datetime.now())
        em1 = discord.Embed(title="Given", description=f"**Giver** \n {interaction.user.mention} \n \n **Receiver** \n {member.mention} \n \n **Amount Given** \n {amount} BFD \n \n **Reason** \n {reason} \n \n **Receipt Of Transfer** \n Attempted to dm you a receipt of this transaction!", color=discord.Color.from_rgb(0, 255, 0), timestamp=datetime.datetime.now())
        em2 = discord.Embed(title="Receipt of transaction", description=f"**Giver** \n {interaction.user.mention} \n \n **Receiver** \n {member.mention} \n \n **Amount Given** \n {amount} BFD \n \n **Reason** \n {reason} \n \n **Receipt Of Transaction** \n This is an official receipt of this transaction!", color=discord.Color.from_rgb(0, 255, 0), timestamp=datetime.datetime.now())
        await interaction.response.send_message(embed=em1)
        await interaction.user.send(embed=em1)
        await member.send(embed=em2)
        await channel.send(embed=em)
        
    @app_commands.command(description= "Take BFD from a user")
    @app_commands.describe(member= "The member you want to take BFD from")
    @app_commands.describe(amount= "The amount you want to take")
    async def take(self, interaction: discord.Interaction, member: discord.Member, amount: float):
        allowed_users = [438537782542073878, 309973826459009024, 786788350160797706]
    
        if interaction.user.id not in allowed_users:
            await interaction.response.send_message("You can't use this Command!!")
            return
        if member.id != 1190416273411158056:
            giver_data = await self.open_account(interaction.user)  # Use interaction.user directly
            receiver_data = await self.open_account(member)
            if amount <= 0:
                await interaction.response.send_message("Amount must be greater than zero!")
                return
            if amount > receiver_data["wallet"]:
                await interaction.response.send_message(f"They don't have enough to take that much BFD")
                return
            giver_data["wallet"] += amount
            receiver_data["wallet"] -= amount
            await self.save_bank_data(interaction.user.id, giver_data)
            await self.save_bank_data(member.id, receiver_data)
            channel = self.client.get_channel(1252513098057912441)
            em = discord.Embed(title="Took", description=f"**Taker** \n {interaction.user.mention} \n \n **Taken from** \n {member.mention} \n \n **Amount Taken** \n {amount}", color=discord.Color.from_rgb(255, 0, 0), timestamp=datetime.datetime.now())
            await interaction.response.send_message(embed=em)
            await channel.send(embed=em)
        else:
            receiver_data = await self.open_account(interaction.user)
            # Open accounts for both the giver and the receiver
            if amount is None:
                await interaction.response.send_message("Please enter the amount to take!")
                return
            if amount <= 0:
                await interaction.response.send_message("Amount must be greater than zero!")
                return
            if amount > 999999:
                await interaction.response.send_message("You don't need that many BFD!")
                return
            receiver_data["wallet"] += amount
            await self.save_bank_data(interaction.user.id, receiver_data)
            channel = self.client.get_channel(1252513098057912441)
            Embed = discord.Embed(title="Took", description=f"**Taker** \n {interaction.user.mention} \n \n **Taken from** \n {member.mention} \n \n **Amount Taken** \n {amount}", color=discord.Color.from_rgb(255, 0, 0), timestamp=datetime.datetime.now())
            await interaction.response.send_message(embed=Embed)
            await channel.send(embed=Embed)



        
    @app_commands.command(description="Set the tax for players")
    @app_commands.describe(amount="The amount of tax you want out of 100")
    async def settax(self, interaction: discord.Interaction, amount: float):
        allowed_users = [438537782542073878, 309973826459009024, 786788350160797706]
    
        if interaction.user.id not in allowed_users:
            await interaction.response.send_message("You can't use this Command!!")
            return
        tax_document = await self.tax_collection.find_one({"_id": "tax"})

        if tax_document:
            await self.tax_collection.update_one({"_id": "tax"}, {"$set": {"tax": {"tax_amount": amount}}})
            await interaction.response.send_message("Tax Updated!")

            em = discord.Embed(
                title="**Tax Change!**",
                description=f"**Tax Changed by** \n {interaction.user} \n \n **New Tax Amount** \n {amount}%",
                color=discord.Color.from_rgb(77, 6, 0),
                timestamp=datetime.datetime.now(),
            )
            channel = self.client.get_channel(1252513098057912441)
            await channel.send(embed=em)
        else:
            new_tax_document = {"_id": "tax", "tax": {"tax_amount": amount}}
            self.tax_collection.insert_one(new_tax_document)
            await interaction.response.send_message("Tax Document Created!")

        

            
    @app_commands.command(description="tells you the current tax amount")
    async def tax(self, interaction: discord.Interaction):
        result = await self.tax_collection.find_one({"_id": "tax"})
        if result:
            tax = result["tax"]["tax_amount"]
            em = discord.Embed(
                title="Tax Amount",
                description=f"**Current Tax Amount** \n {tax}% \n \n **Disclaimer** \n Any amount you put into the give command is pre tax! \n Please use your calculator to calculate tax so you don't overdraw!",
                color=discord.Color.from_rgb(221, 185, 104),
                timestamp=datetime.datetime.now(),
            )
            await interaction.response.send_message(embed=em)
        else:
            await interaction.response.send_message("Error: Could not find tax data in the database.")
 
    @app_commands.command(description="Shows the contents of your bag")
    async def inventory(self, interaction: discord.Interaction):
        user = interaction.user

        # Call open_account to ensure the user has an account
        users_data = await self.open_account(user)

        try:
            bag = users_data["bag"]
        except KeyError:
            bag = []

        em = discord.Embed(title="Inventory")
        for item in bag:
            name = item["item"]
            amount = item["amount"]
            em.add_field(name=name, value=amount)
        await interaction.response.send_message(embed=em)
    

    @app_commands.command(description="Create a bug report")
    async def report(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReportModal(self.client))
        
    @app_commands.command(name="add_item", description="Adds an item to the shop.")
    @app_commands.describe(name="Name of the item", price="Price of the item")
    async def add_item(self, interaction: discord.Interaction, name: str, price: int):
        guild_id = int(interaction.guild.id)
        shop_item = {
            "name": name,
            "price": price
        }
        
        await self.shop_collection.update_one(
            {"guild_id": guild_id},
            {"$push": {"items": shop_item}},
            upsert=True
        )
        await interaction.response.send_message(f"Item {name} has been added to the shop for {price} BFD")
      
    @app_commands.command(name="shop", description="Displays the shop items")
    async def shop(self, interaction: discord.Interaction):
        guild_id = int(interaction.guild.id)
        shop = await self.shop_collection.find_one({"guild_id": guild_id})
        
        if not shop or not shop.get('items'):
            await interaction.response.send_message("The shop is empty")
            return

        # Prepare the embed
        sorted_items = sorted(shop['items'], key=lambda x: x['price'])

        # Prepare the embed
        embed = discord.Embed(title="Shop Items", description="Here are the items available in the shop:")

        # Add each sorted item as a field in the embed
        for item in sorted_items:
            embed.add_field(name=item['name'], value=f"{item['price']} coins", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
        
    @app_commands.command(name="rankshop", description="Displays the shop items")
    async def rankshop(self, interaction: discord.Interaction):
        guild_id = int(interaction.guild.id)
        
        if guild_id == 1182237471195545630:
            embed = discord.Embed(title="Rank Shop", description="Available ranks and departments", color=0x00ff00)
            embed.add_field(name="Finance / Analysis Department", value="Junior Finance Analyst (0 coins)\nFinance Analyst (20 coins)\nSenior Finance Analyst (50 coins)\nSenior Finance Specialist (115 coins)", inline=False)
            embed.add_field(name="Human Resources Department", value="Junior HR Agent (0 coins)\nHR Agent (60 coins)\nSenior HR Agent (135 coins)", inline=False)
            embed.add_field(name="Crisis Department", value="Junior Crisis Officer (0 coins)\nCrisis Officer (125 coins)\nSenior Crisis Officer (200 coins)", inline=False)
        elif guild_id == 1181099675701493821:
            embed = discord.Embed(title="Rank Shop", description="Available ranks", color=0x00ff00)
            embed.add_field(name="Research Department", value="Junior Researcher (0 coins)\nResearcher (45 coins)\nAdvanced Researcher (100 coins)\nSenior Researcher (135 coins)", inline=False)
        else:
            embed = discord.Embed(title="Rank Shop", description="The rank shop is not available for this server.", color=0xff0000)
        
        await interaction.response.send_message(embed=embed)

    



   
#__________________________________________________________________


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

        # Round the wallet amount to the nearest 0.00
        wallet = users_data.get("wallet", 0)
        users_data["wallet"] = round(wallet, 2)

        # If the wallet is below 0.01, set it to 0
        if users_data["wallet"] < 0.01:
            users_data["wallet"] = 0

        # Save the updated user data back to the database
        await self.collection.update_one({"_id": user_id}, {"$set": users_data}, upsert=True)


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        person = self.client.get_user(438537782542073878)
    
        # Ensure both accounts are open
        await self.open_account(member)
        await self.open_account(person)
    
        # Get user data from the bank
        users_data, tax_data = await self.get_bank_data()

        # Check if users_data is in the correct format
        user_id_str = str(member.id)
        if user_id_str not in users_data:
            return  # Handle if the user is not found in the bank data

        wallet_amt = users_data.get(user_id_str, {}).get("wallet", 0)
    
        if wallet_amt > 0:
            await self.update_bank(person, wallet_amt)
            await self.update_bank(member, -1 * wallet_amt)
        
            channel = self.client.get_channel(1252513098057912441)
            em = discord.Embed(
                title="User Vanished",
                description=f"**User that vanished from reality** \n {member.name} with the id of {member.id} \n **Amount Reclaimed before vanish** \n {wallet_amt} BFD",
                color=discord.Color.from_rgb(37, 41, 80),
                timestamp=datetime.datetime.now(),
            )
            await channel.send(embed=em)
                

    @app_commands.command(name="buy")
    @app_commands.describe(item_name="The item you want to buy")
    @app_commands.describe(amount="The amount you want to buy")
    async def buy(self, interaction: discord.Interaction, item_name: str, amount: int = 1):
        user = interaction.user
        guild_id = int(interaction.guild.id)
        result = await self.tax_collection.find_one({"_id": "tax"})
        tax = result["tax"]["tax_amount"] if result else 7.25

        shop = await self.shop_collection.find_one({"guild_id": guild_id})
        if not shop or not shop.get('items'):
            await interaction.response.send_message("The shop is empty")
            return

        item_name = item_name.lower()
        item_found = next((item for item in shop['items'] if item["name"].lower() == item_name), None)

        if not item_found:
            await interaction.response.send_message(f"Item {item_name} not found in the shop")
            return

        price = item_found["price"]
        total_cost = price * amount
        total_cost_with_tax = total_cost + total_cost * (tax / 100)
        user_id = str(user.id)

        users_data = await self.collection.find_one({"_id": user_id})
        if not users_data:
            await self.create_account(user.id)
            users_data = await self.collection.find_one({"_id": user_id})

        if users_data is None:
            await interaction.response.send_message("User data could not be retrieved.")
            return

        if users_data["wallet"] < total_cost_with_tax:
            await interaction.response.send_message(f"You don't have enough funds to buy {amount} {item_name}(s)")
            return

        userr_data = await self.collection.find_one({"_id": "438537782542073878"})
        if userr_data is None:
            await interaction.response.send_message("Tax collection data could not be retrieved.")
            return

        try:
            for thing in users_data["bag"]:
                if thing["item"] == item_name:
                    await interaction.response.send_message(f"You already bought {item_name}! You can't buy it again.")
                    return

            users_data["bag"].append({"item": item_name, "amount": amount})
            users_data["wallet"] -= total_cost_with_tax
            userr_data["wallet"] += (total_cost * (tax / 100))

            await self.collection.update_one({"_id": user_id}, {"$set": users_data})
            await self.collection.update_one({"_id": "438537782542073878"}, {"$set": userr_data})
            
            await interaction.response.send_message(f"You bought {amount} {item_name}(s) for {total_cost_with_tax} coins (including tax).")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}")

    @app_commands.command(name="buyrank", description="Buy a rank from the shop")
    @app_commands.describe(item_name="The item you want to buy")
    async def buyrank(self, interaction: discord.Interaction, item_name: str):
        user = interaction.user
        guild_id = int(interaction.guild.id)
        
        if guild_id == 1182237471195545630:
            role_ids = {
                "junior finance analyst": 1254765364156436543,
                "finance analyst": 1254765361455300619,
                "senior finance analyst": 1254765358804373524,
                "senior finance specialist": 1254566832510074914,
                "junior hr agent": 1254566830643744789,
                "hr agent": 1254566830631293018,
                "senior hr agent": 1254566830572568759,
                "junior crisis officer": 1254566827250548887,
                "crisis officer": 1254566826705420368,
                "senior crisis officer": 1253393115885342751
            }
            roles_hierarchy = {
                "junior finance analyst": [],
                "finance analyst": ["junior finance analyst"],
                "senior finance analyst": ["finance analyst"],
                "senior finance specialist": ["senior finance analyst"],
                "junior hr agent": [],
                "hr agent": ["junior hr agent"],
                "senior hr agent": ["hr agent"],
                "junior crisis officer": [],
                "crisis officer": ["junior crisis officer"],
                "senior crisis officer": ["crisis officer"]
            }
            role_prices = {
                "junior finance analyst": 0,
                "finance analyst": 20,
                "senior finance analyst": 50,
                "senior finance specialist": 115,
                "junior hr agent": 0,
                "hr agent": 60,
                "senior hr agent": 135,
                "junior crisis officer": 0,
                "crisis officer": 125,
                "senior crisis officer": 200
            }
        elif guild_id == 1181099675701493821:
            role_ids = {
                "junior researcher": 1182249356351516684,
                "researcher": 1182249397724135504,
                "advanced researcher": 1257190365082025996,
                "senior researcher": 1182262270231842867
            }
            roles_hierarchy = {
                "junior researcher": [],
                "researcher": ["junior researcher"],
                "advanced researcher": ["researcher"],
                "senior researcher": ["advanced researcher"]
            }
            role_prices = {
                "junior researcher": 0,
                "researcher": 45,
                "advanced researcher": 100,
                "senior researcher": 135
            }
        else:
            await interaction.response.send_message("The rank shop is not available for this server.")
            return

        result = await self.tax_collection.find_one({"_id": "tax"})
        tax = result["tax"]["tax_amount"] if result else 7.25

        item_name = item_name.lower()
        if item_name not in role_ids:
            await interaction.response.send_message(f"Item {item_name} not found in the shop.")
            return

        # Check if the user already has the role
        if any(role.id == role_ids.get(item_name) for role in user.roles):
            await interaction.response.send_message(f"You already have the role {item_name}.")
            return

        # Check if the user has the necessary roles to buy the item
        required_roles = roles_hierarchy.get(item_name, [])
        if any(role_ids.get(role) not in [role.id for role in user.roles] for role in required_roles):
            missing_roles = ', '.join(required_roles)
            await interaction.response.send_message(f"You need to have the following role(s) before buying {item_name}: {missing_roles}.")
            return

        price = role_prices[item_name]
        total_cost_with_tax = price + price * (tax / 100)
        user_id = str(user.id)
        users_data = await self.collection.find_one({"_id": user_id})

        if not users_data:
            await self.create_account(user.id)
            users_data = await self.collection.find_one({"_id": user_id})

        if not users_data:
            await interaction.response.send_message("Failed to create or retrieve your account data.")
            return

        if users_data["wallet"] < total_cost_with_tax:
            await interaction.response.send_message(f"You don't have enough funds to buy {item_name}.")
            return

        userr_data = await self.collection.find_one({"_id": "438537782542073878"})
        if not userr_data:
            await interaction.response.send_message("Failed to retrieve tax collection data.")
            return

        try:
            total = price * (tax/100)
            print(userr_data)
            users_data["wallet"] -= total_cost_with_tax
            userr_data["wallet"] += total
            await self.collection.update_one({"_id": user_id}, {"$set": users_data})
            await self.collection.update_one({"_id": "438537782542073878"}, {"$set": userr_data})
            # Add the role to the user if the guild matches
            role = discord.utils.get(interaction.guild.roles, id=role_ids[item_name])
            if role:
                await user.add_roles(role)
                await interaction.response.send_message(f"You bought {item_name} for {total_cost_with_tax} coins (including tax). You have been given the role.")
            else:
                await interaction.response.send_message(f"Role {item_name} could not be found in this server.")
        except Exception as e:
            print(e)
            await interaction.response.send_message(f"An error occurred: {str(e)}")
            


    
    


    async def get_all_users_data(self):
        all_users = {}
        async for document in self.collection.find():
            user_id = str(document["_id"])  # Assuming user IDs are stored as strings in the database
            wallet_balance = document["wallet"]
            all_users[user_id] = {"wallet": wallet_balance}

        return all_users
    

class ReportModal(ui.Modal, title='Report'):      
    def __init__(self, client):
        super().__init__()
        self.client = client

    reason = ui.TextInput(label='Reason', style=discord.TextStyle.short, placeholder="Why you are reporting the bug", required=True)
    bug = ui.TextInput(label='Bug Description', style=discord.TextStyle.paragraph, placeholder="Describe what the bot did that it shouldn't have", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        dev = self.client.get_user(786788350160797706)
        em = discord.Embed(
            title="**Bug Report**",
            description=f"**Who Reported** \n {interaction.user.name} aka {interaction.user.id} \n **Why** \n {self.reason.value} \n **Report of action of bug** \n {self.bug.value} \n **Bot** \n BlackForge Industries",
            timestamp=datetime.datetime.now()
        )
        await dev.send(embed=em)
        await interaction.channel.send("Bug reported! \n **NOTE: ANY REPORTS NOT ABOUT THE BOT WILL RESULT IN MODERATOR ACTION!!!**")



async def setup(client):
     await client.add_cog(heart(client)) 