import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
load_dotenv('.env')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

TOKEN = os.getenv('TOKEN')

permissions = discord.Permissions(send_messages=True, read_messages=True)
bot = commands.Bot(command_prefix = '!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord! :)')

@bot.command()
async def ping(ctx):
  await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

async def get_messages(ctx, limit=10):
    """Get the last `limit` messages in the channel."""
    messages = dict()
    async for m in ctx.channel.history(limit=limit):
        if m.author.name not in messages.keys():
            messages[m.author.name] = [m.content]
        else:
            user_messages = messages[m.author.name]
            user_messages.append((m.content, m.created_at))
    return messages

@bot.command()
async def do_they_like_me(ctx):
    messages = await get_messages(ctx)
    print(messages)

bot.run(TOKEN)
