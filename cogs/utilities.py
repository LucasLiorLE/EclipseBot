import os
import json
from discord.ext import commands, tasks
import discord
import datetime
import aiohttp
import re
import humanize
import asyncio
from googletrans import Translator, LANGUAGES

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []


    @commands.command()
    async def cgloves(self, ctx, roblox_username: str):
        a = await ctx.reply("Fetching user gloves. This might take a while...")
        async with aiohttp.ClientSession() as session:
            response = await session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [roblox_username], "excludeBannedUsers": True})
            if response.status != 200:
                await a.edit("An error occurred while fetching the user's Roblox ID.")
                return
            data = await response.json()
            if not data["data"]:
                await a.edit(f"No data found for the username: {roblox_username}")
                return
            roblox_id = data["data"][0]["id"]

            file_path = os.path.join(os.path.dirname(__file__), '..', 'Storage', 'gloves.json')

            with open(file_path, 'r') as f:
                gloves = json.load(f)

            all_badge_ids = [badge_id for badge_ids in gloves.values() for badge_id in badge_ids]
            url = f"https://badges.roblox.com/v1/users/{roblox_id}/badges/awarded-dates?badgeIds={','.join(map(str, all_badge_ids))}"
            response = await session.get(url)

            if response.status == 200:
                data = await response.json()
                if not data['data']:
                    await a.edit(f"No badges found for the user: {roblox_username}")
                    return

                owned = [glove for glove, badge_ids in gloves.items() if all(any(badge.get('badgeId') == badge_id for badge in data['data']) for badge_id in badge_ids)]
                not_owned = [glove for glove in gloves.keys() if glove not in owned]

                additional_owned = {}
                for badge_name, badge_id in {"Welcome": 2124743766, "Met Owner": 2124760252, "Met Snow": 2124760875, "Clipped Wings": 2147535393}.items():
                    url = f"https://badges.roblox.com/v1/users/{roblox_id}/badges/awarded-dates?badgeIds={badge_id}"
                    response = await session.get(url)
                    if response.status == 200:
                        data = await response.json()
                        if data['data']:
                            additional_owned[badge_name] = data['data'][0]['awardedDate']

                embed = discord.Embed(title=f"SB Data for {roblox_username}:{roblox_id}:", description=f"Badge gloves:\n{len(owned)}/{len(gloves)} badge gloves owned.", color=0xFFA500)
                embed.add_field(name="OWNED", value=', '.join(owned) if owned else 'None', inline=False)
                embed.add_field(name="NOT OWNED", value=', '.join(not_owned) if not_owned else 'None', inline=False)

                for badge_name, awarded_date in additional_owned.items():
                    date, time, fraction = awarded_date.replace('Z', '+0000').partition('.')
                    fraction = fraction[:fraction.index('+')][:6] + '+0000'
                    awarded_date = f"{date}.{fraction}"
                    awarded_date = datetime.datetime.strptime(awarded_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                    epoch_time = int(awarded_date.timestamp())
                    embed.add_field(name=badge_name, value=f"Obtained on <t:{epoch_time}:F>", inline=False)

                await a.edit(embed=embed)
            else:
                await a.edit("An error occurred while fetching the user's badges.")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def convert(self, ctx, value: float, unit_from: str, unit_to: str):
        
        length_factors = {'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'km': 1000.0}
        weight_factors = {'mg': 0.001, 'g': 1.0, 'kg': 1000.0, 't': 1000000.0}
        volume_factors = {'ml': 0.001, 'l': 1.0, 'kl': 1000.0}
        
        temperature_factors = {
            'C': {'F': lambda c: c * 9/5 + 32, 'K': lambda c: c + 273.15},
            'F': {'C': lambda f: (f - 32) * 5/9, 'K': lambda f: (f - 32) * 5/9 + 273.15},
            'K': {'C': lambda k: k - 273.15, 'F': lambda k: (k - 273.15) * 9/5 + 32}
        }

        if unit_from in length_factors and unit_to in length_factors:
            converted_value = value * length_factors[unit_from] / length_factors[unit_to]
            await ctx.reply(f"{value} {unit_from} is {converted_value} {unit_to}.")
        
        elif unit_from in weight_factors and unit_to in weight_factors:
            converted_value = value * weight_factors[unit_from] / weight_factors[unit_to]
            await ctx.reply(f"{value} {unit_from} is {converted_value} {unit_to}.")
        
        elif unit_from in volume_factors and unit_to in volume_factors:
            converted_value = value * volume_factors[unit_from] / volume_factors[unit_to]
            await ctx.reply(f"{value} {unit_from} is {converted_value} {unit_to}.")
        
        elif unit_from in temperature_factors and unit_to in temperature_factors[unit_from]:
            converted_value = temperature_factors[unit_from][unit_to](value)
            await ctx.reply(f"{value}°{unit_from} is {converted_value}°{unit_to}.")
        
        else:
            await ctx.reply("Invalid units or incompatible unit types. Please check your units and try again.")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remind(self, ctx, duration, *, reason=None):
        time = self.parse_duration(duration)
        
        if time is None:
            await ctx.reply("Invalid duration format. Use `1h`, `1m`, `1s`, or `1d`.")
            return
        
        if reason is None:
            reason = "No reason provided"

        reminder = {
            "user": ctx.author.id,
            "channel": ctx.channel.id,
            "reason": reason,
            "end_time": ctx.message.created_at + time
        }
        
        self.reminders.append(reminder)
        
        await ctx.reply(f"Reminder set for {humanize.naturaldelta(time.total_seconds())} from now.", delete_after=3)
        
        await asyncio.sleep(time.total_seconds())
        await ctx.reply(f"{ctx.author.mention}, your reminder for '{reason}' is due!", delete_after=10)
        self.reminders.remove(reminder)
        
    def parse_duration(self, duration):
        match = re.match(r"(\d+)([hmsd])", duration)
        if match:
            amount, unit = match.groups()
            amount = int(amount)
            
            if unit == "h":
                return datetime.timedelta(hours=amount)
            elif unit == "m":
                return datetime.timedelta(minutes=amount)
            elif unit == "s":
                return datetime.timedelta(seconds=amount)
            elif unit == "d":
                return datetime.timedelta(days=amount)
        
        return None

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        now = datetime.datetime.utcnow()
        for reminder in self.reminders:
            if now >= reminder["end_time"]:
                channel = self.bot.get_channel(reminder["channel"])
                user = self.bot.get_user(reminder["user"])
                await channel.reply(f"Hey {user.mention}, reminder for {reminder['reason']}!")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def translate(self, ctx, *, input_str: str = None):        
        translator = Translator()
        
        if not input_str:
            await ctx.reply("Please provide a target language and text to translate separated by '|'.")
            return
        
        parts = input_str.split('|')
        
        if len(parts) != 2:
            await ctx.reply("Invalid format. Please use 'target_lang | text' format.")
            return
        
        target_lang = parts[0].strip().lower()
        text = parts[1].strip()
        
        if target_lang == 'chineses':
            target_lang = 'chinese (simplified)'
        elif target_lang == 'chineset':
            target_lang = 'chinese (traditional)'
        elif target_lang == 'chinese':
            await ctx.reply('Please enter chineset or chineses next time.\nI believe you want simplified')
            target_lang = 'chinese (simplified)'
        
        if target_lang in LANGUAGES:
            target_lang_code = target_lang
        elif target_lang.lower() in [v.lower() for v in LANGUAGES.values()]:
            target_lang_code = next(k for k, v in LANGUAGES.items() if v.lower() == target_lang.lower())
        else:
            await ctx.reply("Invalid language. Please use a valid language name or language code.")
            return


        try:
            translated = translator.translate(text, dest=target_lang_code)
            translated_text = translated.text
            detected_lang = translated.src
            
            embed = discord.Embed(title="Translation", color=discord.Color.gold())
            embed.add_field(name="Original Text", value=f"`{text}`", inline=False)
            embed.add_field(name="Detected Language", value=detected_lang, inline=False)
            embed.add_field(name="Translated Text", value=f"`{translated_text}`", inline=False)
            embed.set_footer(text=f"Translated to {LANGUAGES[target_lang_code].capitalize()}")
            
            await ctx.reply(embed=embed)
            
        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, prefix: str):
        file_path = os.path.join(os.path.dirname(__file__), '..', 'Storage', 'preferences.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        guild_id = str(ctx.guild.id)  # Convert guild ID to string
        data[guild_id] = {"prefix": prefix}  # Set prefix for the guild
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        self.bot.command_prefix = commands.when_mentioned_or(prefix)
        
        await ctx.reply(f"Bot prefix updated to `{prefix}`.")


def setup(bot):
    bot.add_cog(Utilities(bot))
