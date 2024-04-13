from discord.ext import commands
import discord
import datetime
from typing import Optional
import re

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_embed(self, ctx, title, description, color=0xFF5733):
        embed = discord.Embed(title=title, description=description, color=color)
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
            await self.send_embed(ctx, "Purge Messages", "Please specify how many messages you want to delete.")
        else:
            deleted = await ctx.channel.purge(limit=amount)
            await self.send_embed(ctx, "Purge Messages", f'Deleted {len(deleted)} message(s).')

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
        except Exception as e:
            await self.send_embed(ctx, "Ban Member Error", f"An error occurred while trying to ban the member: {str(e)}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User):
        try:
            await ctx.guild.unban(user)
            await self.send_embed(ctx, "Unban Member", f"{user.mention} has been unbanned.", color=0xffa500)  
        except Exception as e:
            await self.send_embed(ctx, "Unban Member Error", f"An error occurred while trying to unban the member: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role, *, reason=None):
        try:
            if role in member.roles:
                await member.remove_roles(role, reason=reason)
                await self.send_embed(ctx, "Remove Role", f"Removed {role.name} from {member.mention}.")
            else:
                await self.send_embed(ctx, "Remove Role", f"{member.mention} does not have the {role.name} role.")
        except Exception as e:
            await self.send_embed(ctx, "Remove Role Error", f"An error occurred while trying to remove the role: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def give_role(self, ctx, member: discord.Member, role: discord.Role):
        try:
            if role not in member.roles:
                await member.add_roles(role)
                await self.send_embed(ctx, "Give Role", f"Gave {role.name} to {member.mention}.", color=0x32a852)  
            else:
                await self.send_embed(ctx, "Give Role", f"{member.mention} already has the {role.name} role.")
        except Exception as e:
            await self.send_embed(ctx, "Give Role Error", f"An error occurred while trying to give the role: {str(e)}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def mute(self, ctx, member: discord.Member, time: str, *, reason: str = None):
        try:
            if ctx.author.id == member.id:
                await self.send_embed(ctx, "Mute Member Error", ":x: You can't mute yourself!")
                return

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
                await self.send_embed(ctx, "Mute Member", f"{member.mention} has been muted for {human_readable_time}. Reason: {reason or 'Reason not provided.'}", color=0xffd700)  
            else:
                await member.timeout(10000000000000, reason=reason)  
                await self.send_embed(ctx, "Mute Member", f"{member.mention} has been muted indefinitely. Reason: {reason or 'Reason not provided.'}", color=0xffd700)  

        except Exception as e:
            await self.send_embed(ctx, "Mute Member Error", f"An error occurred while trying to mute the member: {str(e)}")


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
