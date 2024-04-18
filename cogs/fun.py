import discord
from discord.ext import commands
import random
import asyncpraw
import requests
from urllib.parse import quote

class BlackjackView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.green)
    async def hit(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = 'hit'
        self.stop()

    @discord.ui.button(label='Stand', style=discord.ButtonStyle.red)
    async def stand(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = 'stand'
        self.stop()

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reddit = asyncpraw.Reddit(client_id='Enl7jFbBrOoQTjoEfTMmDQ',
                               client_secret='1H5GBR3N3RsoBWYKMizp0nta-66FYQ',
                               user_agent='discord-bot:Enl7jFbBrOoQTjoEfTMmDQ:v1.0 (by /u/LucasLiorLEE)')
        
    @commands.command(aliases=['bj'])
    async def blackjack(self, ctx):
        deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        random.shuffle(deck)

        player = []
        dealer = []

        player.append(deck.pop())
        dealer.append(deck.pop())
        player.append(deck.pop())
        dealer.append(deck.pop())

        view = BlackjackView()
        game_message = await ctx.reply(f"Your cards: {player}, total: {sum(player)}\nDealer's first card: {dealer[0]}\nWould you like to draw another card? Hit or Stand?", view=view)
        
        while sum(player) < 21:
            view = BlackjackView()  
            await game_message.edit(content=f"Your cards: {player}, total: {sum(player)}\nDealer's first card: {dealer[0]}\nWould you like to draw another card? Hit or Stand?", view=view)
            await view.wait()
            if view.value == 'hit':
                player.append(deck.pop())
            else:
                break

        if sum(player) > 21:
            await game_message.edit(content=f"You busted! You lose.\nYour cards: {player}, total: {sum(player)}\nDealer's cards: {dealer}, total: {sum(dealer)}")
        elif sum(player) == 21:
            await game_message.edit(content=f"Blackjack! You win!\nYour cards: {player}, total: {sum(player)}\nDealer's cards: {dealer}, total: {sum(dealer)}")
        else:
            while sum(dealer) < 17:
                dealer.append(deck.pop())
            await game_message.edit(content=f"Your cards: {player}, total: {sum(player)}\nDealer's cards: {dealer}, total: {sum(dealer)}")

            if sum(dealer) > 21:
                await game_message.edit(content=f"Dealer busts! You win!\nYour cards: {player}, total: {sum(player)}\nDealer's cards: {dealer}, total: {sum(dealer)}")
            elif sum(dealer) < sum(player):
                await game_message.edit(content=f"You win!\nYour cards: {player}, total: {sum(player)}\nDealer's cards: {dealer}, total: {sum(dealer)}")
            elif sum(dealer) > sum(player):
                await game_message.edit(content=f"You lose!\nYour cards: {player}, total: {sum(player)}\nDealer's cards: {dealer}, total: {sum(dealer)}")
            else:
                await game_message.edit(content=f"It's a draw!\nYour cards: {player}, total: {sum(player)}\nDealer's cards: {dealer}, total: {sum(dealer)}")


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
                    await ctx.reply(f"Could not find channel with ID: {channel_id}")
            except discord.HTTPException as e:
                await ctx.reply(f"An error occurred: {str(e)}")
        else:
            sent_message = await channel.send(f"{ctx.author.mention} forgot to add a message! Laugh at him!!!")
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
                await ctx.reply(f"An error occurred: {str(e)}")
        else:
            await ctx.reply(f"No message to send :(")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def solve(self, ctx, *, equation):
        equation = quote(equation, safe='')
        url = f"http://api.mathjs.org/v4/?expr={equation}"
        response = requests.get(url)
        if response.status_code == 200:
            await ctx.reply(f"The answer is: {response.text}")
        else:
            await ctx.reply(f"An error occurred: {response.text}")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
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
        
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fact(self, ctx):
        try:
            a = await ctx.reply("Fetching a random fact... This might take a moment!")
            url = "https://uselessfacts.jsph.pl/random.json?language=en"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                embed = discord.Embed(title="Random Fact 🤓", description=data['text'], color=0x9370DB)
                await a.edit(content=None, embed=embed)
            else:
                await a.edit(content="An error occurred while fetching the fact.")
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joke(self, ctx):
        try:
            a = await ctx.reply("Fetching a joke... This might take a moment.")
            url = "https://official-joke-api.appspot.com/jokes/random"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if 'setup' in data and 'punchline' in data:
                    joke_setup = data['setup']
                    joke_punchline = data['punchline']
                    await a.edit(content=f"**{joke_setup}**\n\n*{joke_punchline}*")
                else:
                    await a.edit(content="Sorry, I couldn't fetch a joke right now. Try again later!")
            else:
                await a.edit(content="An error occurred while fetching the joke.")
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cat(self, ctx):
        try:
            a = await ctx.reply("Fetching a cute cat picture... Hold on!")
            url = "https://api.thecatapi.com/v1/images/search"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                cat_image_url = data[0]['url']
                
                embed = discord.Embed(title="Here's a cute cat for you!", color=0xFFA07A)
                embed.set_image(url=cat_image_url)
                await a.edit(content=None, embed=embed)
            else:
                await a.edit(content="An error occurred while fetching the cat picture.")
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dog(self, ctx):
        try:
            a = await ctx.reply("Fetching an adorable dog picture... One moment!")
            url = "https://dog.ceo/api/breeds/image/random"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                dog_image_url = data['message']
                
                embed = discord.Embed(title="Here's a cute dog for you!", color=0xADD8E6)
                embed.set_image(url=dog_image_url)
                await a.edit(content=None, embed=embed)
            else:
                await a.edit(content="An error occurred while fetching the dog picture.")
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def quote(self, ctx):
        try:
            a = await ctx.reply("Fetching an inspirational quote... Hold tight!")
            url = "https://zenquotes.io/api/random"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()[0]
                
                embed = discord.Embed(title=data['q'], description=f"- {data['a']}", color=0x66CDAA)
                await a.edit(content=None, embed=embed)
            else:
                await a.edit(content="An error occurred while fetching the quote.")
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def meme(self, ctx):
        try:
            subreddit_names = [
                "4chan", "greentext", "shitposting", "196", "blursedimages",
                "comedyhomicide", "holesome", "TrueReddit", "ihaveihaveihavereddit",
                "Angryupvote", "artmemes", "cursedcomments", "depression_memes",
                "linuxmemes", "ProgrammerHumor", "maybemaybemaybe", "MEOW_IRL",
                "PrequelMemes", "SequelMemes", "SesameStreetMemes", "TheRealJoke",
                "Unexpected", "YouSeeComrade"
            ]
            
            subreddit_name = random.choice(subreddit_names)
            subreddit = await self.reddit.subreddit(subreddit_name)
            
            post = await subreddit.random()
            
            if post and hasattr(post, 'title') and hasattr(post, 'permalink'):
                embed = discord.Embed(title=post.title, color=0xFF4500, url=f"https://reddit.com{post.permalink}")
                embed.set_image(url=post.url)
                embed.set_footer(text=f"Subreddit: {subreddit_name}")
                
                await ctx.reply(embed=embed)
            else:
                await ctx.reply("Could not fetch a post from Reddit. Please try again later.")
            
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}")


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rps(self, ctx, choice: str):
        choices = ['rock', 'paper', 'scissors']
        
        if choice.lower() not in choices:
            await ctx.reply("Invalid choice. Please choose 'rock', 'paper', or 'scissors'.")
            return
        
        bot_choice = random.choice(choices)
        
        if choice.lower() == bot_choice:
            result = "It's a tie!"
        elif (choice.lower() == 'rock' and bot_choice == 'scissors') or \
             (choice.lower() == 'paper' and bot_choice == 'rock') or \
             (choice.lower() == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
        else:
            result = "You lose!"
        
        await ctx.reply(f"You chose **{choice.capitalize()}** and the bot chose **{bot_choice.capitalize()}**. {result}")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dice(self, ctx, amt: int = 6):
        await ctx.reply(f"Dice roll: {random.randint(1,amt)}")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def coinflip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        await ctx.reply(f"The coin landed on **{result}**!")

def setup(bot):
    bot.add_cog(Fun(bot))
