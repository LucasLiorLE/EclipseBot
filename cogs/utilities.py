from discord.ext import commands
import discord
import aiohttp
import json
from datetime import datetime
import os


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cgloves(self, ctx, roblox_username: str):
        async with aiohttp.ClientSession() as session:
            response = await session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [roblox_username], "excludeBannedUsers": True})
            if response.status != 200:
                await ctx.send("An error occurred while fetching the user's Roblox ID.")
                return
            data = await response.json()
            if not data["data"]:
                await ctx.send(f"No data found for the username: {roblox_username}")
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
                    await ctx.send(f"No badges found for the user: {roblox_username}")
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
                    awarded_date = datetime.strptime(awarded_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                    epoch_time = int(awarded_date.timestamp())
                    embed.add_field(name=badge_name, value=f"Obtained on <t:{epoch_time}:F>", inline=False)

                await ctx.send(embed=embed)
            else:
                await ctx.send("An error occurred while fetching the user's badges.")

def setup(bot):
    bot.add_cog(Utilities(bot))
