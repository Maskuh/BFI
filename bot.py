# bot.py
#Import list
import os
import discord
import time
import datetime
import asyncio
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
#________________________________________________
#File Configs
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#TOKEN = os.getenv('Testing_bot')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents, owner_id=os.getenv("Owner"), case_insensitive=True)
bot.help_command = None
#______________________________________________________________________________________________
@bot.event
async def on_ready():
  try:
    await bot.load_extension("cogs.heart")
    await bot.tree.sync()
  except Exception as e:
    print(f"The bot has reported the error \n ({e})")
  await bot.change_presence(status= discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="How To Trade BFD"))
  print(f"I'm in as {bot.user}")
  
  
@app_commands.command(description="Reloads a cog")
@app_commands.describe(extension="The File you want to reload")
async def reload(interaction: discord.Interaction, extension: str):
  if interaction.user.id != 786788350160797706:
    await interaction.response.send_message("You can't use this command only <@786788350160797706> Can!")
  else:
    try:
      await bot.reload_extension(f'main_cogs.{extension}')
      await interaction.response.send_message("Cog reloaded!")
    except Exception as e:
      await interaction.response.send_message(f"The bot reported this error \n {e}")
      
@app_commands.command(description="Reloads a cog")
@app_commands.describe(extension="The File you want to reload")
async def unload(interaction: discord.Interaction, extension: str):
  if interaction.user.id != 786788350160797706:
    await interaction.response.send_message("You can't use this command only <@786788350160797706> Can!")
  else:
    try:
      await bot.unload_extension(f'main_cogs.{extension}')
      await interaction.response.send_message("Cog unloaded!")
    except Exception as e:
      await interaction.response.send_message(f"The bot reported this error \n {e}")
bot.run(TOKEN)