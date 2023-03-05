import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize 
load_dotenv('.env')
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import itertools
import tracemalloc


tracemalloc.start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

TOKEN = os.getenv('TOKEN')

permissions = discord.Permissions(send_messages=True, read_messages=True)
bot = commands.Bot(command_prefix = '!', intents=intents)

def tokenize(msg):
    token_list = dict()
    for user in msg.keys():
        token_list[user] = []
        for (text,time) in msg[user]:
            token_list[user].append(word_tokenize(text))
    return token_list
    

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord! :)')

@bot.command()
async def ping(ctx):
  await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

async def get_messages(ctx, limit=1000):
    """Get the last `limit` messages in the channel."""
    messages = dict()
    async for m in ctx.channel.history(limit=limit):
        if m.author.name not in messages.keys():
            messages[m.author.name] = [(m.content, m.created_at)]
        else:
            user_messages = messages[m.author.name]
            user_messages.append((m.content, m.created_at))
    return messages

@bot.command()
async def do_they_like_me(ctx):
    messages = await get_messages(ctx)
    return messages

# ----------------- Wordcloud -----------------
@bot.command()
async def greet(ctx, arg):
    messages = await do_they_like_me(ctx)
    await ctx.send(f'Hello')
    await generate_wordcloud(messages=messages, arg = arg)
    await print_wordcloud()

def generate_wordcloud(messages, arg):
    tokenized_msgs = tokenize(messages)
    words = tokenized_msgs[arg]
    joined_list = list(itertools.chain(*words))

    wordcloud = WordCloud(width=800, height=800, background_color='white', min_font_size=10).generate(' '.join(joined_list))

    # plot the WordCloud image
    plt.figure(figsize=(8,8), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.show()

    # save the WordCloud image as a file
    wordcloud.to_file("wordcloud.png")

async def print_wordcloud(): 
    # find the channel you want to send a message to channel_name = 'general'
    channel = discord.utils.get(bot.get_all_channels(), name='general')
    # send a message to the channel
    with open('wordcloud.png', 'rb') as f:
        file = discord.File(f)
    # send the file to the channel
    await channel.send(file=file)



bot.run(TOKEN)
