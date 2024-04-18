from discord.ext import commands
import discord
import datetime
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
        await ctx.send(embed=embed, delete_after=delete_after)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def note(self, ctx, member: discord.Member, *, note: str = None):
        try:
            guild_id = ctx.guild.id
            notes = self.get_guild_notes(guild_id)
            user_key = str(member.id)
            
            if user_key not in notes:
                notes[user_key] = []
            
            notes[user_key].append({
                "Moderator": str(ctx.author),
                "Note": note 
            })
            
            self.save_notes()
            await self.send_embed(ctx, f"Added note: {note} to {member}")
        except Exception as e:
            await self.send_embed(ctx, "Note Member Error", f"An error occurred while trying to note the member: {str(e)}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def notes(self, ctx, user: Optional[discord.User] = None):
        user = user or ctx.author
        user_key = str(user.id)
        user_notes = self.notes.get(user_key, [])

        if not user_notes:
            await ctx.send(f"No notes found for <@{user.id}>.")
            return

        embed = discord.Embed(title=f"Warnings for {user.display_name}", color=0x7289da)
        
        for i, note in enumerate(user_notes, 1):
            moderator = ctx.guild.get_member(int(note["moderator"])) or note["moderator"]
            notes = note["note"]
            embed.add_field(name=f"Note {i} by {moderator}", value=f"Note: {notes}", inline=False)
            embed.add_footer(text="Use delnote or delete_ntoe to remove notes.")

        await ctx.send(embed=embed)

    @commands.command(aliases=['delnote'])
    @commands.has_permissions(manage_messages=True)
    async def delete_note(self, ctx, user: discord.Member, note_index: int):
        user_key = str(user.id)
        user_notes = self.warns.get(user_key, [])

        if not user_notes:
            await ctx.send(f"No notes found for {user.mention}.")
            return

        if note_index <= 0 or note_index > len(user_notes):
            await ctx.send(f"Invalid note index. Please provide a valid note index between 1 and {len(user_notes)}.")
            return

        removed_note = user_notes.pop(note_index - 1)
        self.save_notes()

        await ctx.send(f"Removed note {note_index} for {user.mention}. Reason: {removed_note['reason']}")

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
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("User has no moderation stats.")

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

    @commands.command()
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
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        try:
            guild_id = ctx.guild.id
            warns = self.get_guild_warns(guild_id)
            user_key = str(member.id)
            
            if user_key not in warns:
                warns[user_key] = []
            
            warns[user_key].append({
                "moderator": str(ctx.author),
                "reason": reason or "Reason not provided."
            })
            
            self.save_warns()
            await self.send_embed(ctx, "Warn Member", f"{member.mention} has been warned. Reason: {reason or 'Reason not provided.'}")

            await self.update_modstats(ctx, ctx.author.id, "warn")

        except Exception as e:
            await self.send_embed(ctx, "Warn Member Error", f"An error occurred while trying to warn the member: {str(e)}")


    @commands.command(aliases=['warns'])
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, user: Optional[discord.User] = None):
        user = user or ctx.author
        user_key = str(user.id)
        user_warns = self.warns.get(user_key, [])

        if not user_warns:
            await ctx.send(f"No warnings found for <@{user.id}>.")
            return

        embed = discord.Embed(title=f"Warnings for {user.display_name}", color=0x7289da)
        
        for i, warn in enumerate(user_warns, 1):
            moderator = ctx.guild.get_member(int(warn["moderator"])) or warn["moderator"]
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
