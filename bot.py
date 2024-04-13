from discord.ext import commands
import discord
import json 
import os

def load_help_data():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    help_json_path = os.path.join(dir_path, '..', 'Storage', 'help.json')
    
    with open(help_json_path, 'r') as file:
        return json.load(file)

help_data = load_help_data()

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moderation", emoji="📋", description="Displays all the commands for moderation"),
            discord.SelectOption(label="Utilities", emoji="✨", description="Displays all the commands for utilities"),
            discord.SelectOption(label="Information", emoji="🗣️", description="Shows all the commands for information"),
            discord.SelectOption(label="Fun", emoji="😃", description="Shows all the commands for fun")
        ]
        super().__init__(placeholder="Select a category", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        commands = help_data.get(category, {})
        
        description = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in commands.items()])
        
        embed = discord.Embed(title=f"{category.capitalize()} Commands", description=description, color=discord.Color.blue())
        embed.set_footer(text="(optional args) {required args}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)



class SelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        if latency < 81:
            color = 0x00FF00  
        elif latency < 201:
            color = 0xFFFF00  
        else:
            color = 0xFF0000  
        embed = discord.Embed(title="Pong!", description=f"The latency is {latency}ms.", color=color)
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(title="Bot Info", description="This bot is developed by LucasLiorLE.", color=0x808080)
        embed.add_field(name="Version", value="1.9.8-a.9")
        embed.add_field(name="Source Code", value="[GitHub Repository](https://github.com/LucasLiorLE/EclipseBot)")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title="Server Info", color=0x808080)
        embed.add_field(name="Server Name", value=guild.name)
        embed.add_field(name="Server Owner", value=guild.owner.mention)
        embed.add_field(name="Server ID", value=guild.id)
        embed.add_field(name="Members", value=guild.member_count)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roles = [role.name for role in member.roles]
        embed = discord.Embed(title="User Info", color=0x808080)
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Username", value=member.display_name)
        embed.add_field(name="User ID", value=member.id)
        embed.add_field(name="Joined Discord", value=member.created_at.strftime("%b %d, %Y"))
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"))
        embed.add_field(name="Roles", value=', '.join(roles))
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=0x808080)
        embed.set_image(url=member.avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def help(self, ctx, *, command_name: str = None):
        if command_name:
            command_info = search_command(command_name.lower())
            if not command_info:
                await ctx.send(f"No such command named `{command_name}`.")
                return
            category = list(command_info.keys())[0]
            matched_cmd = list(command_info[category].keys())[0]  
            command_description = command_info[category][matched_cmd]
            
            embed = discord.Embed(title=f"Help for `{matched_cmd}`", color=discord.Color.blue())
            embed.add_field(name="Description", value=command_description)
            embed.add_field(name="Category", value=category)
            embed.set_footer(text="(optional args) {required args}")
            await ctx.send(embed=embed)
            return

        view = SelectView()
        await ctx.send("Please select a category:", view=view)

# END

def search_command(command_name):
    for category, commands in help_data.items():
        for cmd, description in commands.items():
            if cmd.startswith(command_name):
                return {category: {cmd: description}}
    return None

def setup(bot):
    bot.add_cog(Info(bot))
