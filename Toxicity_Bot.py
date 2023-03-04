import discord
import os
from dotenv import load_dotenv
from discord.ext import tasks, commands
load_dotenv('.env')

intents = discord.Intents.default()
intents.messages = True

TOKEN = os.getenv('TOKEN')

# intents = discord.Intents.default()
# intents.message_content = True

bot = commands.Bot(command_prefix = '!', intents=intents)
# client = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord! :)')

@bot.command()
async def ping(ctx):
  await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        print("hello was said")
        await message.channel.send('Hello!')

bot.run(TOKEN)
