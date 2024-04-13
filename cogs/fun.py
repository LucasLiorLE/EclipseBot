from discord.ext import commands
import discord
import random
import requests # type: ignore
from urllib.parse import quote


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, channel_id: int, *, message: str = None):
        await ctx.message.delete()
        if message is not None:
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(message)
                else:
                    await ctx.send(f"Could not find channel with ID: {channel_id}")
            except discord.HTTPException as e:
                await ctx.send(f"An error occurred: {str(e)}")
        else:
            sent_message = await ctx.send(f"{ctx.author.mention} forgot to add a message! Laugh at him!!!")
            await sent_message.add_reaction("😄")  


    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def DM(self, ctx, user: discord.User, *, message):
        await ctx.message.delete()
        if message:
            try:
                await user.send(message)
                await ctx.author.send(f"Successfully sent \'{message}\' to {user}!")
            except discord.HTTPException as e:
                await ctx.send(f"An error occurred: {str(e)}")
        else:
            await ctx.send(f"No message to send :(")

    @commands.command()
    async def solve(self, ctx, *, equation):
        equation = quote(equation, safe='')
        url = f"http://api.mathjs.org/v4/?expr={equation}"
        response = requests.get(url)
        if response.status_code == 200:
            await ctx.reply(f"The answer is: {response.text}")
        else:
            await ctx.reply(f"An error occurred: {response.text}")

    @commands.command()
    async def ship(self, ctx, arg1: str = None, arg2: str = None):
        if arg1 is None:
            arg1 = ctx.author.name
        if arg2 is None:
            arg2 = random.choice([member.name for member in ctx.guild.members])
        
        com = random.randint(1, 100)
        thresholds = [(100, "Perfect! "), (90, "Amazing "), (75, "Great "), (50, "Not Bad "), (25, "Bad "), (0, "Awful ☹️")]
        description = next(desc for score, desc in thresholds if com >= score)
        progress = '▓' * round(com / 10) + '░' * (10 - round(com / 10))
        
        embed = discord.Embed(title=f" {arg1[:4]}{arg2[-4:]}", color=0xFF0000)
        embed.add_field(name="Compatibility Score", value=f"{progress} {com}%")
        embed.add_field(name="Match", value=f"{description}")
        
        await ctx.send(embed=embed)

    @commands.command()
    async def fact(self, ctx, num: int = 1):
        num = max(1, min(num, 30))
        url = f"https://api.api-ninjas.com/v1/facts?limit={num}"
        headers = {"X-Api-Key": "FIubP4YVbTuT7nDi2AaXCQ==kVS3Wsxw2OmScElt"}  
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            facts = [fact['fact'] for fact in data]
            await ctx.reply("\n".join(facts))
        else:
            await ctx.reply("An error occurred while fetching the facts.")

def setup(bot):
    bot.add_cog(Fun(bot))
