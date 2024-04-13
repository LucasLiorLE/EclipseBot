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
            "I'm so skibidi",
            "Technoblade never dies.",
            "I should've played hypixel instead...",
            "BRR SKIBIDI DOP DOP YES YES",
            "This took so long to make...",
            "I got a headache...",
            "pls free nitro :pray:", 
            "pls free robux :pray:",
            "Wait when was it 3 am",
            "STOP STARING AND GO STUDY!!!",
        ]

    async def change_status(self):
        while True:
            await self.bot.wait_until_ready()
            current_status = random.choice(self.status_messages)
            await self.bot.change_presence(
                status=discord.Status.dnd, 
                activity=discord.Game(name=current_status)
            )
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
            await ctx.send(f":x: You don't have permission to use this command. Required permissions: {error.required_permissions}", delete_after=3)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(":x: The username you provided was not found. (Case sensitive)", delete_after=3)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(":x: Invalid arguments provided", delete_after=3)
        elif isinstance(error, TypeError):
            await ctx.send(":x: Invalid time format. Use 'h' for hours or 'd' for days.", delete_after=3)
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(":x: Command not found.", delete_after=3)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f":x: This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.", delete_after=3)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(":x: This command cannot be used in private messages.", delete_after=3)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(":x: You do not have the necessary permissions to use this command.", delete_after=3)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(":x: Missing required argument.", delete_after=3)
        elif isinstance(error, commands.CommandError):
            await ctx.send(f":x: An error occurred while processing your command: {error}", delete_after=3)
        else:
            await ctx.send(":x: An unknown error occurred while processing your command. Please try again later.", delete_after=3)


    async def on_command_completion(self, ctx):
        log_channel = self.get_channel(1227752190765039717)
    
        embed = discord.Embed(title=f"Command: {ctx.command}", color=0x7289da)
        embed.add_field(name="User", value=ctx.author.mention, inline=False)
        embed.add_field(name="Server", value=ctx.guild.name, inline=False)
        embed.add_field(name="Command Message", value=f"[Click here]({ctx.message.jump_url})", inline=False)
        embed.add_field(name="Time", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)
        embed.set_footer(text=f"Used by {ctx.author}", icon_url=ctx.author.avatar.url)
    
        await log_channel.send(embed=embed)

    async def on_message_edit(self, before, after):
        log_channel = self.get_channel(1228755328405995530)

        embed = discord.Embed(title="Message Edited", color=0xffa500)
        embed.add_field(name="User", value=before.author.mention, inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Original Message", value=before.content[:1024], inline=False)
        embed.add_field(name="Edited Message", value=after.content[:1024], inline=False)
        embed.add_field(name="Message Link", value=f"[Click here]({before.jump_url})", inline=False)
        embed.add_field(name="Time", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)
        embed.set_footer(text=f"Edited by {before.author}", icon_url=before.author.avatar.url)

        await log_channel.send(embed=embed)

    async def on_message_delete(self, message):
        log_channel = self.get_channel(1228755328405995530)

        embed = discord.Embed(title="Message Deleted", color=0xff0000)
        embed.add_field(name="User", value=message.author.mention, inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Message Content", value=message.content[:1024], inline=False)
        embed.add_field(name="Message Link", value="Unavailable in deleted messages", inline=False)
        embed.add_field(name="Time", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)
        embed.set_footer(text=f"Deleted by {message.author}", icon_url=message.author.avatar.url)

        await log_channel.send(embed=embed)


    async def process_commands(self, message):
        content = message.content.lower()  
        if content.startswith(self.secrets.prefix.lower()):  
            ctx = await self.get_context(message, cls=commands.Context)
            await self.invoke(ctx)


secrets = Secrets()
bot = Bot(secrets)
asyncio.run(bot.start(secrets.token))
