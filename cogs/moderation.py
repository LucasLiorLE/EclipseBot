from discord.ext import commands
import discord
import datetime
from typing import Optional
import re
import json

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.modstats_file = "Storage/Logs/modstats.json"
        self.warns_file = "Storage/Logs/warns.json"
        self.load_modstats()
        self.load_warns()

    def load_warns(self):
        try:
            with open(self.warns_file, 'r') as f:
                self.warns = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.warns = {}

    def save_warns(self):
        with open(self.warns_file, 'w') as f:
            json.dump(self.warns, f, indent=4)

    def load_modstats(self):
        try:
            with open(self.modstats_file, 'r') as f:
                self.modstats = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.modstats = {}

    def save_modstats(self):
        with open(self.modstats_file, 'w') as f:
            json.dump(self.modstats, f, indent=4)

    def get_user_stats(self, user_id):
        user_key = str(user_id)
        if user_key not in self.modstats:
            self.modstats[user_key] = {
                "bans": 0,
                "warns": 0,
                "mutes": 0,
                "total": 0,
            }
        return self.modstats[user_key]

    async def send_embed(self, ctx, title, description, color=0xFF5733):
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send(embed=embed)

    async def update_modstats(self, author_id, action):
        stats = self.get_user_stats(author_id)
        if action == "ban":
            stats["bans"] += 1
        elif action == "mute":
            stats["mutes"] += 1
        elif action == "warn":
            stats["warns"] += 1
        stats["total"] += 1
        self.save_modstats()

    @commands.command(aliases=['ms'])
    async def modstats(self, ctx, user: Optional[discord.User] = None):
        user = user or ctx.author
        stats = self.get_user_stats(user.id)
        embed = discord.Embed(title=f"Moderation Stats for {user.display_name}", color=0x7289da)
        embed.add_field(name="Bans", value=stats.get("bans", 0))
        embed.add_field(name="Warns", value=stats.get("warns", 0))
        embed.add_field(name="Mutes", value=stats.get("mutes", 0))
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int, member: discord.Member = None):
        def check(msg):
            return msg.author == member if member else True
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await self.send_embed(ctx, "Clear Messages", f'Deleted {len(deleted)} message(s).', delete_after=3)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = None):
        if amount is None:
            await self.send_embed(ctx, "Purge Messages", "Please specify how many messages you want to delete.", delete_after=3)
        else:
            deleted = await ctx.channel.purge(limit=amount)
            await self.send_embed(ctx, "Purge Messages", f'Deleted {len(deleted)} message(s).', delete_after=3)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, duration: Optional[str] = None, *, reason=None):
        try:
            ban_duration = None
            if duration:
                match = re.match(r'(\d+)([dhm])', duration)
                if match:
                    amount, unit = match.groups()
                    if unit == 'd':
                        ban_duration = datetime.timedelta(days=int(amount))
                    elif unit == 'h':
                        ban_duration = datetime.timedelta(hours=int(amount))
                    elif unit == 'm':
                        ban_duration = datetime.timedelta(minutes=int(amount))
            
            if ban_duration:
                await member.ban(delete_message_days=0, reason=reason)
                unban_time = (ctx.message.created_at + ban_duration).strftime('%Y-%m-%d %H:%M:%S')
                await self.send_embed(ctx, "Ban Member", f"{member.mention} has been banned for {duration} ({unban_time}).")
            else:
                await member.ban(delete_message_days=0, reason=reason)
                await self.send_embed(ctx, "Ban Member", f"{member.mention} has been banned indefinitely.")
            
            await self.update_modstats(ctx.author.id, "ban")

        except Exception as e:
            await self.send_embed(ctx, "Ban Member Error", f"An error occurred while trying to ban the member: {str(e)}")

    @commands.command(aliases=['timeout'])
    @commands.has_permissions(kick_members=True)
    async def mute(self, ctx, member: discord.Member, time: str, *, reason: str = None):
        try:
            duration = None
            if time.endswith("s"):
                duration = datetime.timedelta(seconds=int(time[:-1]))
            elif time.endswith("h"):
                duration = datetime.timedelta(hours=int(time[:-1]))
            elif time.endswith("d"):
                duration = datetime.timedelta(days=int(time[:-1]))

            if duration:
                await member.timeout(duration, reason=reason)
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                human_readable_time = f"{int(hours)} hour(s) {int(minutes)} minute(s) {int(seconds)} second(s)"
                await self.send_embed(ctx, "Mute Member", f"{member.mention} has been muted for {human_readable_time}. Reason: {reason or 'Reason not provided.'}")
            else:
                await member.timeout(10000000000000, reason=reason)
                await self.send_embed(ctx, "Mute Member", f"{member.mention} has been muted indefinitely. Reason: {reason or 'Reason not provided.'}")

            await self.update_modstats(ctx.author.id, "mute")

        except Exception as e:
            await self.send_embed(ctx, "Mute Member Error", f"An error occurred while trying to mute the member: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        try:
            user_key = str(member.id)
            if user_key not in self.warns:
                self.warns[user_key] = []
                
            self.warns[user_key].append({
                "moderator": str(ctx.author),
                "reason": reason or "Reason not provided."
            })
            
            self.save_warns()
            await self.send_embed(ctx, "Warn Member", f"{member.mention} has been warned. Reason: {reason or 'Reason not provided.'}")

            await self.update_modstats(ctx.author.id, "warn")

        except Exception as e:
            await self.send_embed(ctx, "Warn Member Error", f"An error occurred while trying to warn the member: {str(e)}")

    @commands.command()
    async def warns(self, ctx, user: Optional[discord.User] = None):
        user = user or ctx.author
        user_key = str(user.id)
        user_warns = self.warns.get(user_key, [])

        if not user_warns:
            await ctx.send(f"No warnings found for <@{user.id}>.")
            return

        embed = discord.Embed(title=f"Warnings for {user.display_name}", color=0x7289da)
        
        for i, warn in enumerate(user_warns, 1):
            moderator = warn["moderator"]
            reason = warn["reason"]
            embed.add_field(name=f"Warning {i} by {moderator}", value=f"Reason: {reason}", inline=False)
            embed.add_footer(text="Use delwarn or delete_warn to remove warns.")

        await ctx.send(embed=embed)

    @commands.command(aliases=['delwarn'])
    @commands.has_permissions(manage_messages=True)
    async def delete_warn(self, ctx, user: discord.Member, warn_index: int):
        user_key = str(user.id)
        user_warns = self.warns.get(user_key, [])

        if not user_warns:
            await ctx.send(f"No warnings found for {user.mention}.")
            return

        if warn_index <= 0 or warn_index > len(user_warns):
            await ctx.send(f"Invalid warning index. Please provide a valid warning index between 1 and {len(user_warns)}.")
            return

        removed_warn = user_warns.pop(warn_index - 1)
        self.save_warns()

        await ctx.send(f"Removed warning {warn_index} for {user.mention}. Reason: {removed_warn['reason']}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.timeout(None, reason=reason)
            await self.send_embed(ctx, "Unmute Member", f"{member.mention} has been unmuted.", color=0xffd700)  

        except Exception as e:
            await self.send_embed(ctx, "Unmute Member Error", f"An error occurred while trying to unmute the member: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, delay: Optional[int] = None):
        try:
            if delay is None:
                delay_seconds = 0
                await ctx.channel.edit(slowmode_delay=delay_seconds)
                await self.send_embed(ctx, "Slowmode", "Slowmode has been removed.")
            elif 0 <= delay <= 21600:  
                await ctx.channel.edit(slowmode_delay=delay)
                await self.send_embed(ctx, "Slowmode", f"Slowmode set to {delay} seconds.")
            else:
                await self.send_embed(ctx, "Slowmode Error", "Please provide a delay between 0 and 21600 seconds.")
        except Exception as e:
            await self.send_embed(ctx, "Slowmode Error", f"An error occurred while setting slowmode: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, new_nick: str):
        try:
            await member.edit(nick=new_nick)
            await self.send_embed(ctx, "Nickname Changed", f"Changed {member.mention}'s nickname to {new_nick}.", color=0x32a852)
        except Exception as e:
            await self.send_embed(ctx, "Nickname Change Error", f"An error occurred while changing the nickname: {str(e)}")

def setup(bot):
    bot.add_cog(Moderation(bot))
