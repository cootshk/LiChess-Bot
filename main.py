import asyncio
import os
import discord
import lichessapi
from discord.ext import commands

client = commands.Bot(command_prefix=".", intents=discord.Intents.all(), help_command=None)
slash = client.tree

@client.event
async def on_ready():
    print("Bot is ready")
    print(f"Logged in as {os.getenv('discord'['username'][0])}#{os.getenv('discord'['username'][1])}")

@slash.command(name="findgame",description="start playing a new game on Lichess")
async def findgame(interaction: discord.Interaction):
    pass

lichessapi.lichessAccount

client.run(os.getenv("discord"["token"]))