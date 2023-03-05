import discord
import os
from dotenv import load_dotenv
import requests
import json
from discord.ext import commands
import nltk
nltk.download('averaged_perceptron_tagger')
from nltk import pos_tag
from nltk.tokenize import word_tokenize 
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import itertools
import tracemalloc
import text2emotion as te
from textblob import TextBlob
from collections import Counter
import random


load_dotenv('.env')
tracemalloc.start()

intents = discord.Intents.default()
intents.message_content = True
# client = discord.Client(intents=intents)

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

def filter_tokens(token_list,user):
    prepositions = ["wordcloud","on", "in", "at", "of", "to", "with", "by", "for", "from", "about", "as", "among", "between", "within", "without", "through", "toward", "during", "under", "until", "that", "be", "is"]

    passed_tokens = []
    for token in token_list[user]:
        for word in token:
            if(word == "I" or ((len(word)>=2) and (not "_" in word))):
                pos = nltk.pos_tag([word])
                
                if(pos[0][1] != "DT" and pos[0][1] != "PRP"):
                    if(word.isalpha()):
                        if(word.lower() not in prepositions):
                            passed_tokens.append(word)
    
    return passed_tokens
                   

def tokenize(msg,target_user):
    token_list = dict()
    for user in msg.keys():
        token_list[user] = []
        for (text,time) in msg[user]:
            token_list[user].append(word_tokenize(text))
        token_list[user] = filter_tokens(token_list,user)
    return token_list[target_user]
    

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

    toxicity_scores['CONTENT'] = message
    
    return toxicity_scores

@bot.command()
async def do_they_like_me(ctx):
    messages = await get_messages(ctx)
    return messages

# ----------------- Wordcloud -----------------
@bot.command()
async def wordcloud(ctx, arg):
    print("In wordcloud")
    messages = await do_they_like_me(ctx)
    await ctx.send(f'Mkaing wordcloud for {arg}')
    generate_wordcloud(messages=messages, arg = arg)
    await ctx.send(f'{arg} uses these words most: ')
    await print_wordcloud()

def generate_wordcloud(messages, arg):
    tokenized_msgs = tokenize(messages,arg)
    joined_list = tokenized_msgs
    word_dict_list = {word: joined_list.count(word) for word in set(joined_list)}
    
    sentiment_scores = {}
    for word in joined_list:
        blob = TextBlob(word)
        sentiment_scores[word] = blob.sentiment.polarity

    full_dict  = {}
    # Print the sentiment scores for each word
    for word, score in sentiment_scores.items():
        color = 'red' if score < 0.2 else 'green'
        full_dict[word] = (word_dict_list[word], score, color)

    def get_word_color(word, **kwargs):
        # Generate a random RGB color tuple
        r,g,b = 155,155,155
        if word in full_dict.keys():
            if full_dict[word][1] < 0:
                r,g,b = 150,8,5
                # r = int((1 - abs(full_dict[word][1])) * 255)
                # g = 0
                # b = 0
            elif full_dict[word][1] > 0:
                r,g,b = 0,150,10
                # r = 0
                # g = int(abs(full_dict[word][1]) * 255)
                # b = int(abs(1 - abs(full_dict[word][1]) * 255))
    
        return f"rgb({r}, {g}, {b})"
    
    # create the word cloud
    wc = WordCloud(background_color='white', max_words=200, color_func=get_word_color, height=1500, width=1500)

    # generate the word cloud
    wc.generate_from_frequencies(word_dict_list)

    # display the word cloud
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    # plt.show()

    # save the WordCloud image as a file
    wc.to_file("wordcloud.png")


async def print_wordcloud(): 
    # find the channel you want to send a message to channel_name = 'general'
    channel = discord.utils.get(bot.get_all_channels(), name='committee-chat')
    # send a message to the channel
    with open('wordcloud.png', 'rb') as f:
        file = discord.File(f)
    # send the file to the channel
    await channel.send(file=file)
    
# ------------------------------------

def calculate_user_profile(msg_profiles):
    print("in calculate_user_profiles")
    # Initialize an empty dictionary to hold the averaged values
    user_profile = {}

    # Get the number of dictionaries in the list
    num_dicts = len(msg_profiles)

    # Iterate over each key in the dictionaries
    for key in msg_profiles[0]:
        if key != 'CONTENT':
            # Initialize variables to hold the sum and maximum values for this key
            key_sum = 0.0
            max_msg = ''
            max_score = float('-inf')

            # Iterate over each dictionary in the list and add up the values for this key
            for msg_profile in msg_profiles:
                key_value = msg_profile.get(key, 0)
                key_sum += key_value
                if key_value > max_score: 
                    max_msg = msg_profile.get('CONTENT', '') 
                    max_score = key_value

            # Calculate the average for this key
            key_avg = key_sum / num_dicts

            # Add the average and maximum values to the new dictionary
            user_profile[key] = key_avg
            user_profile[key+'_max'] = max_msg
    return user_profile

def format_msg(user_profile):
    print(user_profile)
    msg = f'''Here is the likelihood that you are:
    **Severely toxic:** {user_profile.get('SEVERE_TOXICITY', '')},
    **Toxic:** {user_profile.get('TOXICITY', '')},
    **Insulting:** {user_profile.get('INSULT', '')}
    **Attacking someone's identity:** {user_profile.get('IDENTITY_ATTACK', '')},
    **Threatening:** {user_profile.get('THREAT', '')}
    **Your most toxic comment was:** {user_profile.get('SEVERE_TOXICITY_max', '')}.
    **Your most insulting comment was:** {user_profile.get('INSULT_max', '')}.
    **Your most offensive comment was:** {user_profile.get('IDENTITY_ATTACK_max', '')}.
'''
    return msg

@bot.command()
async def toxicity_check(ctx):
    print("in toxicity_check")
    recent_msg = await get_messages(ctx,limit=1)
    for id_user in recent_msg.keys():
        user = id_user
    msgs = await get_messages_from_user(ctx, user, check_no=100)
    msg_profs = [judge_toxicity(m) for m in msgs]
    user_profile = calculate_user_profile(msg_profs)
    msg_to_send = format_msg(user_profile)
    await ctx.send(msg_to_send)

@bot.command()
async def what_are_my_emotions(ctx):
    print("in what_is_my_emotions")
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
    sender = message.author.mention
    for measure in tox.keys():
        if measure != 'CONTENT':
            if(tox[measure]>0.45):
                toxic_reasons.append(measure)
    if(len(toxic_reasons)>0):
        if message.author.id in warnings.keys():
            warnings[message.author.id]+=1
        else:
            warnings[message.author.id] = 1
        ending = "th"
        if(str(warnings[message.author.id])[-1] == "1"):
            ending = "st"
        elif(str(warnings[message.author.id])[-1] == "2"):
            ending = "nd"
        elif(str(warnings[message.author.id])[-1] == "3"):
            ending = "rd"
        await message.channel.send(f"<@{sender}> This message is not appropriate because of {toxic_reasons}, please be nice :)\n This is your {warnings[message.author.id]}{ending} warning")
    await bot.process_commands(message)

bot.run(TOKEN)
