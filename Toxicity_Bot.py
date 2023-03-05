import discord
import os
from dotenv import load_dotenv
import requests
import json
from discord.ext import commands
import nltk
from nltk.tokenize import word_tokenize 
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import itertools
import tracemalloc
import text2emotion as te


load_dotenv('.env')
tracemalloc.start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

load_dotenv('.env')
nltk.download('punkt')
TOKEN = os.getenv('TOKEN')

permissions = discord.Permissions(send_messages=True, read_messages=True)
bot = commands.Bot(command_prefix = ';;', intents=intents)
warnings = dict()

async def detect_emotion(ctx, msgs ,user):
    anger = 0
    fear = 0
    happy = 0
    sad = 0
    surprise = 0
    n = 0
    for text in msgs:
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

async def get_messages_from_user(ctx, user, check_no=10):
    """Get the last `limit` messages in the channel."""
    messages = list()
    async for m in ctx.channel.history(limit=1000):
        if (m.author.name == user and not ";;" in m.content):
            messages.append(m.content)
            check_no-=1
        if(check_no == 0):
            break
    return messages


def judge_toxicity(message):
    API_KEY = 'AIzaSyDJfvvVgP4BQyhmFwlojakTTj7oJ5SJkJs'
    url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=" + API_KEY
    headers = {'content-type': 'application/json'}
    data = {
        'comment': {
            'text': '\n'.join(message)
        },
        'requestedAttributes': {
            'TOXICITY': {},
            'SEVERE_TOXICITY': {},
            'IDENTITY_ATTACK': {},
            'INSULT': {},
            'THREAT': {}
        },
        'languages': ['en']
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    toxicity_scores = {}
    try:
        attribute_scores = response.json()['attributeScores']
        toxicity_scores = {attr: score['summaryScore']['value'] for attr, score in attribute_scores.items()}
    except:
        toxicity_scores = dict()
        toxicity_scores['TOXICITY'] = 0
    
    return toxicity_scores

@bot.command()
async def do_they_like_me(ctx):
    messages = await get_messages(ctx)
    return messages

# ----------------- Wordcloud -----------------
@bot.command()
async def wordcloud(ctx, arg):
    messages = await do_they_like_me(ctx)
    await ctx.send(f'I did it!')
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

def calculate_user_profile(msg_profiles):
    # Initialize an empty dictionary to hold the averaged values
    user_profile = {}

    # Get the number of dictionaries in the list
    num_dicts = len(msg_profiles)

    # Iterate over each key in the dictionaries
    for key in msg_profiles[0].keys():
        # Initialize a variable to hold the sum of the values for this key
        key_sum = 0.0

        # Iterate over each dictionary in the list and add up the values for this key
        for d in msg_profiles:
            key_sum += d.get(key, 0)

        # Calculate the average for this key
        key_avg = key_sum / num_dicts

        # Add the average value to the new dictionary
        user_profile[key] = key_avg
    return user_profile


@bot.command()
async def toxicity_check(ctx):
    recent_msg = await get_messages(ctx,limit=1)
    for id_user in recent_msg.keys():
        user = id_user
    msgs = await get_messages_from_user(ctx, user, check_no=100)
    msg_profs = [judge_toxicity(m) for m in msgs]
    print('calculating user prof...')
    user_profile = calculate_user_profile(msg_profs)
    print(user_profile)
    #     tox += judge_toxicity(msg)['T
    # tox = (tox/len(msgs))*100
    # await ctx.send(f'{user}\'s recent toxicness: {tox}%')    

@bot.command()
async def what_are_my_emotions(ctx):
    recent_msg = await get_messages(ctx,limit=1)
    for id_user in recent_msg.keys():
        user = id_user
    messages = await get_messages_from_user(ctx,user,limit=100)
    await detect_emotion(ctx,messages,user)

    # for user, messages in messages.items():
    #     for message in messages:
    #         print(user)
    #         print(message)
    #         print(judge_toxicity(message))
@bot.event
async def on_message(message):
    tox = judge_toxicity([message.content])
    toxic_reasons = []
    for measure in tox.keys():
        if(tox[measure]>0.45):
            toxic_reasons.append(measure)
    if(len(toxic_reasons)>0):
        if message.author.id in warnings.keys():
            warnings[message.author.id]+=1
        else:
            warnings[message.author.id] = 1
        ending = "th"
        if(str(warnings[message.author.id])[-1] is "1"):
            ending = "st"
        elif(str(warnings[message.author.id])[-1] is "2"):
            ending = "nd"
        elif(str(warnings[message.author.id])[-1] is "3"):
            ending = "rd"
        await message.channel.send(f"<@{message.author.id}> Message is not appropriate because of {toxic_reasons}, please be nice :)\n This is your {warnings[message.author.id]}{ending} warning")


bot.run(TOKEN)
