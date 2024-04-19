import random
import json
import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from cogs import info, moderation, fun, utilities


class Preferences:
    def __init__(self):
        with open("Storage/preferences.json", "r") as f:
            self.data = json.load(f)
        
    def get_prefix(self, guild):
        guild_id = str(guild.id)
        return self.data.get(guild_id, {}).get("prefix", ".")

    def get_logs(self, guild):
        guild_id = str(guild.id)
        return self.data.get(guild_id, {}).get("logs", None)

    def set_logs(self, guild, channel_id):
        guild_id = str(guild.id)
        self.data[guild_id]["logs"] = channel_id

    def save_preferences(self):
        with open("Storage/preferences.json", "w") as f:
            json.dump(self.data, f, indent=4)


class Secrets:
    def __init__(self):
        with open("secrets.json") as f:
            self.data = json.load(f)
        self.token = self.data["token"]


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
            "Big update soon?",
            "I'm literally making this bot for fun.",
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
        super().__init__(command_prefix=self.get_prefix, intents=discord.Intents.all(), help_command=None)
        self.secrets = secrets
        self.preferences = Preferences()
        self.status_manager = StatusManager(self)

    async def get_prefix(self, message):
        if message.guild is None:
            return '.'
        return self.preferences.get_prefix(message.guild)

    async def load_cogs(self):
        await self.wait_until_ready()
        await self.add_cog(info.Info(self))
        await self.add_cog(moderation.Moderation(self))
        await self.add_cog(fun.Fun(self))
        await self.add_cog(utilities.Utilities(self))

    async def on_ready(self):
        print(f"Bot is online as {self.user} (ID: {self.user.id})")
        
        print("Currently in the following servers:")
        for guild in self.guilds:
            print(f"- {guild.name} (ID: {guild.id})")
        
        print(f'Currently in {len(self.guilds)} server(s)!')
        self.loop.create_task(self.status_manager.change_status())
        self.loop.create_task(self.load_cogs())

    async def on_guild_join(self, guild: discord.Guild):
        self.preferences.data[str(guild.id)] = {
            "prefix": ".",
            "logs": None
        }
        self.preferences.save_preferences()

    async def on_message_edit(self, before, after):
        log_channel = self.get_channel(self.preferences.get_logs(before.guild))
        
        if log_channel is None:
            return

        await log_channel.send(embed=self.create_edit_embed(before, after))

    async def on_message_delete(self, message):
        log_channel = self.get_channel(self.preferences.get_logs(message.guild))
        
        if log_channel is None:
            return

        await log_channel.send(embed=self.create_delete_embed(message))

    def create_edit_embed(self, before, after):
        embed = discord.Embed(title="Message Edited", color=discord.Color.gold())
        embed.add_field(name="User", value=before.author.mention, inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Original Message", value=before.content[:1024], inline=False)
        embed.add_field(name="Edited Message", value=after.content[:1024], inline=False)
        embed.add_field(name="Message Link", value=f"[Click here]({before.jump_url})", inline=False)
        embed.add_field(name="Time", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)
        
        if before.author.avatar:
            embed.set_footer(text=f"Edited by {before.author}", icon_url=before.author.avatar.url)
        else:
            embed.set_footer(text=f"Edited by {before.author}")

        return embed

    def create_delete_embed(self, message):
        embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
        embed.add_field(name="User", value=message.author.mention, inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Message Content", value=message.content[:1024], inline=False)
        embed.add_field(name="Time", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)
        
        if message.author.avatar:
            embed.set_footer(text=f"Deleted by {message.author}", icon_url=message.author.avatar.url)
        else:
            embed.set_footer(text=f"Deleted by {message.author}")

        return embed

    async def process_commands(self, message):
        content = message.content.lower().strip()

        if not content:
            return

        command = content.split()[0]

        if message.guild is None:
            return

        prefix = await self.get_prefix(message)
        if command.startswith(prefix):
            ctx = await self.get_context(message, cls=commands.Context)
            
            if command == f"{prefix}prefix":
                new_prefix = message.content.split()[1]
                self.preferences.data[str(ctx.guild.id)]["prefix"] = new_prefix
                self.preferences.save_preferences()

            await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(f"⚠️ You don't have permission to use this command. Required permissions: {error.missing_permissions} ⚠️", delete_after=3)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.reply("⚠️ The username you provided was not found. (Case sensitive) ⚠️", delete_after=3)
        elif isinstance(error, commands.BadArgument):
            await ctx.reply("⚠️ Invalid arguments provided ⚠️", delete_after=3)
        elif isinstance(error, TypeError):
            await ctx.reply("⚠️ Invalid time format. Use 'h' for hours or 'd' for days. ⚠️", delete_after=3)
        elif isinstance(error, commands.CommandNotFound):
            await ctx.reply("⚠️ Command not found. ⚠️", delete_after=3)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"⚠️ This command is on cooldown. Please try again in {error.retry_after:.2f} seconds. ⚠️", delete_after=3)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.reply("⚠️ This command cannot be used in private messages. ⚠️", delete_after=3)
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply("⚠️ You do not have the necessary permissions to use this command. ⚠️", delete_after=3)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Missing required argument. ⚠️", delete_after=3)
        elif isinstance(error, commands.CommandError):
            await ctx.reply(f"⚠️ An error occurred while processing your command: {error} ⚠️", delete_after=3)
        else:
            await ctx.reply("⚠️ An unknown error occurred while processing your command. Please try again later. ⚠️", delete_after=3)

if __name__ == "__main__":
    secrets = Secrets()
    bot = Bot(secrets)
    bot.run(secrets.token)
