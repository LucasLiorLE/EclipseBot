import os
import random
import json
import asyncio
from datetime import datetime, timedelta
from urllib.parse import quote
import requests  # type: ignore
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from itertools import cycle

# Import cogs
from cogs import info
from cogs import moderation
from cogs import fun
from cogs import utilities


class Secrets:
    def __init__(self):
        with open("secrets.json") as f:
            self.data = json.load(f)
        self.token = self.data["token"]
        self.prefix = self.data["prefix"]


class StatusManager:
    def __init__(self, bot):
        self.bot = bot
        self.status_messages = [
            "INF SUCKS",
        ]
        self.status_cycle = cycle(self.status_messages)

    async def change_status(self):
        while True:
            await self.bot.wait_until_ready()
            current_status = next(self.status_cycle)
            await self.bot.change_presence(activity=discord.Game(name=current_status))
            await asyncio.sleep(600)


class Bot(commands.Bot):
    def __init__(self, secrets):
        super().__init__(command_prefix=secrets.prefix, intents=discord.Intents.all(), help_command=None)
        self.secrets = secrets
        self.status_manager = StatusManager(self)

    async def load_cogs(self):
        await self.wait_until_ready()
        await self.add_cog(info.Info(self))
        await self.add_cog(moderation.Moderation(self))
        await self.add_cog(fun.Fun(self))
        await self.add_cog(utilities.Utilities(self))

    async def on_ready(self):
        print(f"Bot is online as {self.user} (ID: {self.user.id})")
        print(f'Currently in {len(self.guilds)} server(s)!')
    
        self.loop.create_task(self.status_manager.change_status())
        self.loop.create_task(self.load_cogs())  

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"You don't have permission to use this command. Required permissions: {error.required_permissions}")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("The username you provided was not found. (Case sensitive)")
        elif isinstance(error, commands.CommandError):
            await ctx.send(f"An error occurred while processing your command: {error}")
        else:
            await ctx.send("An unknown error occurred while processing your command. Please try again later.")

    async def on_command_completion(self, ctx):
        log_channel = self.get_channel(1227752190765039717)

        embed = discord.Embed(title=f"Command: {ctx.command}", color=0x7289da)
        embed.add_field(name="User", value=ctx.author.mention, inline=False)
        embed.add_field(name="Command Message", value=ctx.message.content, inline=False)
        embed.add_field(name="Time", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)
        embed.set_footer(text=f"Used by {ctx.author}", icon_url=ctx.author.avatar.url)
        await log_channel.send(embed=embed)

    async def process_commands(self, message):
        content = message.content.lower()  # Convert message content to lowercase
        if content.startswith(self.secrets.prefix.lower()):  # Check if message starts with prefix
            ctx = await self.get_context(message, cls=commands.Context)
            await self.invoke(ctx)


secrets = Secrets()
bot = Bot(secrets)
asyncio.run(bot.start(secrets.token))
