from discord.ext import commands
import discord
import datetime
import time
from typing import Optional
import re
import json
import os


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.modstats_file = "Storage/Logs/modstats.json"
        self.warns_file = "Storage/Logs/warns.json"
        self.preferences_file = "Storage/Logs/preferences.json"
        self.notes_file = "Storage/Logs/notes.json"
        self.load_modstats()
        self.load_warns()
        self.load_preferences()
        self.load_notes()

    def load_preferences(self):
        try:
            with open(self.preferences_file, 'r') as f:
                self.preferences = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.preferences = {}

    def load_warns(self):
        try:
            with open(self.warns_file, 'r') as f:
                self.warns = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.warns = {}
    
    def load_notes(self):
        try:
            with open(self.notes_file, 'r') as f:
                self.notes = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.notes = {}

    def load_modstats(self):
        try:
            with open(self.modstats_file, 'r') as f:
                self.modstats = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.modstats = {}

    def save_preferences(self):
        with open(self.preferences_file, 'w') as f:
            json.dump(self.preferences, f, indent=4)

    def save_warns(self):
        with open(self.warns_file, 'w') as f:
            json.dump(self.warns, f, indent=4)

    def save_notes(self):
        with open(self.notes_file, 'w') as f:
            json.dump(self.notes, f, indent=4)

    def save_modstats(self):
        with open(self.modstats_file, 'w') as f:
            json.dump(self.modstats, f, indent=4)

    def get_guild_modstats(self, guild_id):
        if str(guild_id) not in self.modstats:
            self.modstats[str(guild_id)] = {}
        return self.modstats[str(guild_id)]

    def get_guild_warns(self, guild_id):
        if str(guild_id) not in self.warns:
            self.warns[str(guild_id)] = {}
        return self.warns[str(guild_id)]

    def get_guild_notes(self, guild_id):
        if str(guild_id) not in self.notes:
            self.notes[str(guild_id)] = {}
        return self.notes[str(guild_id)]

    async def update_modstats(self, ctx, author_id, action):
        guild_id = ctx.guild.id
        stats = self.get_guild_modstats(guild_id)
        if str(author_id) not in stats:
            stats[str(author_id)] = {
                "bans": 0,
                "warns": 0,
                "mutes": 0,
                "total": 0,
            }
        if action == "ban":
            stats[str(author_id)]["bans"] += 1
        elif action == "mute":
            stats[str(author_id)]["mutes"] += 1
        elif action == "warn":
            stats[str(author_id)]["warns"] += 1
        stats[str(author_id)]["total"] += 1
        self.save_modstats()

    def get_user_stats(self, guild_id, author_id):
        stats = self.get_guild_modstats(guild_id)
        if str(author_id) in stats:
            return stats[str(author_id)]
        return None
    
    async def send_embed(self, ctx, title, description, color=0xFF5733, delete_after=None):
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.reply(embed=embed, delete_after=delete_after)

    @commands.command(aliases=['delete_note', 'deletenote', 'removenote', 'remove_note'])
    @commands.has_permissions(kick_members=True)
    async def delnote(self, ctx, member: discord.Member, note_id: int):
        guild_id = ctx.guild.id
        notes = self.get_guild_notes(guild_id)
        if str(member.id) in notes and note_id < len(notes[str(member.id)]):
            del notes[str(member.id)][note_id]
            self.save_notes()
            await self.send_embed(ctx, "Note Deleted", f"Note {note_id} has been deleted from {member.name}.", color=0xFF0000)
        else:
            await self.send_embed(ctx, "Error", "Invalid note ID.", color=0xFF0000)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        guild_id = ctx.guild.id
        warns = self.get_guild_warns(guild_id)
        if str(member.id) not in warns:
            warns[str(member.id)] = []
        warn = {
            "Moderator": ctx.author.id,
            "Reason": reason,
            "Date": int(time.time())
        }
        warns[str(member.id)].append(warn)
        self.save_warns()
        await self.update_modstats(ctx, ctx.author.id, "warn")
        await self.send_embed(ctx, "Warned", f"{member.name} has been warned.", color=0xFFA500)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def note(self, ctx, member: discord.Member, *, reason=None):
        guild_id = ctx.guild.id
        notes = self.get_guild_notes(guild_id)
        if str(member.id) not in notes:
            notes[str(member.id)] = []
        note = {
            "Moderator": ctx.author.id,
            "Reason": reason,
            "Date": int(time.time())
        }
        notes[str(member.id)].append(note)
        self.save_notes()
        await self.send_embed(ctx, "Note Added", f"A note has been added to {member.name}.", color=0x00FF00)


    @commands.command(aliases=['delete_warn', 'deletewarn', 'removewarn', 'remove_warn'])
    @commands.has_permissions(kick_members=True)
    async def delwarn(self, ctx, member: discord.Member, warn_id: int):
        guild_id = ctx.guild.id
        warns = self.get_guild_warns(guild_id)
        if str(member.id) in warns and warn_id < len(warns[str(member.id)]):
            del warns[str(member.id)][warn_id]
            self.save_warns()
            await self.send_embed(ctx, "Warn Deleted", f"Warn {warn_id} has been deleted from {member.name}.", color=0xFF0000)
        else:
            await self.send_embed(ctx, "Error", "Invalid warn ID.", color=0xFF0000)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warns(self, ctx, member: discord.Member):
        guild_id = ctx.guild.id
        warns = self.get_guild_warns(guild_id)
        if str(member.id) in warns and warns[str(member.id)]:
            embed = discord.Embed(title=f"Warns for {member.name}", color=0xFFA500)
            for i, warn in enumerate(warns[str(member.id)]):
                if "Moderator" in warn and "Reason" in warn and "Date" in warn:
                    moderator = self.bot.get_user(warn["Moderator"])
                    date = int(warn["Date"])
                    embed.add_field(name=f"Warn {i+1}", value=f"Moderator: {moderator}\nReason: {warn['Reason']}\nDate: <t:{date}:R>", inline=False)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"{member.name} has no warns.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def notes(self, ctx, member: discord.Member):
        guild_id = ctx.guild.id
        notes = self.get_guild_notes(guild_id)
        if str(member.id) in notes and notes[str(member.id)]:
            embed = discord.Embed(title=f"Notes for {member.name}", color=0x00FF00)
            for i, note in enumerate(notes[str(member.id)]):
                if "Moderator" in note and "Reason" in note and "Date" in note:
                    moderator = self.bot.get_user(note["Moderator"])
                    date = int(note["Date"])
                    embed.add_field(name=f"Note {i+1}", value=f"Moderator: {moderator}\nReason: {note['Reason']}\nDate: <t:{date}:R>", inline=False)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"{member.name} has no notes.")



    @commands.command(aliases=['ms'])
    @commands.has_permissions(manage_messages=True)
    async def modstats(self, ctx, user: Optional[discord.User] = None):
        user = user or ctx.author
        guild_id = ctx.guild.id
        author_id = user.id
        user_stats = self.get_user_stats(guild_id, author_id)
        
        if user_stats:
            embed = discord.Embed(title=f"Moderation Stats for {user.name}#{user.discriminator}", color=discord.Color.green())
            embed.add_field(name="Bans", value=user_stats["bans"])
            embed.add_field(name="Mutes", value=user_stats["mutes"])
            embed.add_field(name="Warns", value=user_stats["warns"])
            embed.add_field(name="Total Actions", value=user_stats["total"])
            
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("User has no moderation stats.")

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
            
            await self.update_modstats(ctx, ctx.author.id, "ban") 

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

            await self.update_modstats(ctx, ctx.author.id, "mute") 

        except Exception as e:
            await self.send_embed(ctx, "Mute Member Error", f"An error occurred while trying to mute the member: {str(e)}")

    @commands.command(aliases=['log'])
    @commands.has_permissions(manage_messages=True)
    async def logs(self, ctx, channel: discord.TextChannel):
        try:
            file_path = os.path.join(os.path.dirname(__file__), '..', 'Storage', 'preferences.json')
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            guild_id = str(ctx.guild.id)
            if guild_id not in data:
                data[guild_id] = {}
            data[guild_id]["logs"] = channel.id
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            await self.send_embed(ctx, "Logging Channel Updated", f"Logging channel has been set to {channel.mention}.")
        except Exception as e:
            await self.send_embed(ctx, "Logs Error", f"An error occurred while setting the logging channel: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.timeout(None, reason=reason)
            await self.send_embed(ctx, "Unmute Member", f"{member.mention} has been unmuted.", color=0xffd700)  

        except Exception as e:
            await self.send_embed(ctx, "Unmute Member Error", f"An error occurred while trying to unmute the member: {str(e)}")

    @commands.command(aliases=['sm'])
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
