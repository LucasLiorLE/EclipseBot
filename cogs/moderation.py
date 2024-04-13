from discord.ext import commands
import discord
import asyncio
import datetime
import re

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int, member: discord.Member = None):
        def check(msg):
            return msg.author == member if member else True

        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f'Deleted {len(deleted)} message(s).', delete_after=3)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = None):
        if amount is None:
            await ctx.send("Please specify how many messages you want to delete.", delete_after=3)
        else:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(f'Deleted {len(deleted)} message(s).', delete_after=3)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, delete_message_days: int = 0, *, reason=None):
        try:
            await member.ban(delete_message_days=delete_message_days, reason=reason)
            await ctx.send(f"{member.mention} has been banned.")
        except Exception as e:
            await ctx.send(f"An error occurred while trying to ban the member: {str(e)}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.unban(reason=reason)
            await ctx.send(f"{member.mention} has been unbanned.")
        except Exception as e:
            await ctx.send(f"An error occurred while trying to unban the member: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role, *, reason=None):
        try:
            if role in member.roles:
                await member.remove_roles(role, reason=reason)
                await ctx.send(f"Removed {role.name} from {member.mention}.")
            else:
                await ctx.send(f"{member.mention} does not have the {role.name} role.")
        except Exception as e:
            await ctx.send(f"An error occurred while trying to remove the role: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def give_role(self, ctx, member: discord.Member, role: discord.Role):
        try:
            if role not in member.roles:
                await member.add_roles(role)
                await ctx.send(f"Gave {role.name} to {member.mention}.")
            else:
                await ctx.send(f"{member.mention} already has the {role.name} role.")
        except Exception as e:
            await ctx.send(f"An error occurred while trying to give the role: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason: str = None):
        if duration is None:
            await ctx.send("Please specify a duration in the format `1s`, `1m`, `1h`, or `1d`.")
            return

        match = re.match(r'(\d+)([smhd])', duration)
        if not match:
            await ctx.send("Invalid duration format. Please use `1s`, `1m`, `1h`, or `1d`.")
            return

        amount = int(match.group(1))
        unit = match.group(2)

        if unit == 's':
            delta = datetime.timedelta(seconds=amount)
        elif unit == 'm':
            delta = datetime.timedelta(minutes=amount)
        elif unit == 'h':
            delta = datetime.timedelta(hours=amount)
        elif unit == 'd':
            delta = datetime.timedelta(days=amount)
        else:
            await ctx.send("Invalid duration format. Please use `1s`, `1m`, `1h`, or `1d`.")
            return

        await member.timeout(delta, reason=reason)
        await ctx.send(f"{member.mention} has been muted for {duration}.", delete_after=delta.total_seconds())

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        await member.timeout(None, reason=reason)
        await ctx.send(f"{member.mention} has been unmuted.")

def setup(bot):
    bot.add_cog(Moderation(bot))
