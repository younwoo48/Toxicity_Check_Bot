import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize 
load_dotenv('.env')
import text2emotion as te
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

TOKEN = os.getenv('TOKEN')

permissions = discord.Permissions(send_messages=True, read_messages=True)
bot = commands.Bot(command_prefix = '!', intents=intents)


async def detect_emotion(ctx, msgs ,user):
    anger = 0
    fear = 0
    happy = 0
    sad = 0
    surprise = 0
    n = 0
    for (text,time) in msgs[user]:
        emotion = te.get_emotion(text)
        n+=1
        anger += emotion['Angry']
        fear += emotion['Fear']
        happy += emotion['Happy']
        sad += emotion['Sad']
        surprise + emotion['Surprise']
    await ctx.send(f'{user}\'s recent emotions:\n')    
    await ctx.send(f'Anger: {anger/n}\nFear: {fear/n}\nHappy: {happy/n}\nSad: {sad/n}\nSurprise: {surprise/n}')    

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

async def get_messages(ctx, limit=10):
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
    print(tokenize(messages))

@bot.command()
async def what_are_my_emotions(ctx):
    recent_msg = await get_messages(ctx,limit=1)
    for id_user in recent_msg.keys():
        user = id_user
    messages = await get_messages(ctx,limit=100)
    await detect_emotion(ctx,messages,user)
    
        


bot.run(TOKEN)
