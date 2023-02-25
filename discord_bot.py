#!/usr/bin/python3

from discord import Client, Game, File, PermissionOverwrite, FFmpegPCMAudio, Intents, Embed, PCMVolumeTransformer
from discord.ext.tasks import loop
from discord.utils import get
from asyncio import sleep, TimeoutError, get_event_loop
from queue import Queue
from random import randint
from sqlite3 import connect
from re import search
from datetime import date, timedelta, datetime
from time import localtime, strftime
from client import start, get_msg, send
from os.path import isfile
from os import remove, environ, listdir, rename, getcwd
import ffmpeg
import youtube_dl
from youtube_dl import YoutubeDL
import yt_dlp
from dotenv import load_dotenv
from sys import platform
from pytube import YouTube
import json
from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse
from threading import Thread
import time

load_dotenv()
TOKEN = environ.get('TOKEN')
AUDIO_PATH = environ.get('AUDIO_PATH')
DATABASE_PATH = environ.get('DATABASE_PATH')
FFMPEG_PATH = environ.get('FFMPEG_PATH')
IP_ADDRESS = environ.get('IP_ADDRESS')

InQueue = Queue()
OutQueue = Queue()

intents = Intents.default()
intents.members = True
#intents.message_content = True ## For newer versions of discord.py and python

DISCONNECT_MESSAGE = "#DISCONNECT#"
CONNECT_UI_MESSAGE = "#UICONNECTED#"
REQUEST_MESSAGE = "#REQUEST#"
VOICE_REQUEST_MESSAGE = "#VOICEREQUEST#"
VOICE_SEND_MESSAGE = "#VOICESEND#"
#tables:
#commands (command_name, output, author)
#play_requests (game text UNIQUE, time text, yes text, no text, requestor text)
#braincell_points (name text UNIQUE, points integer)
#calendar (event_name text, year integer, month integer, day integer, time text, gang text)
#emojis (emoji text UNIQUE)
#counters (counter text UNIQUE, count integer)
#casino (outcome string UNIQUE, bets string)
#music (userid text, song text, liked integer (0 or 1))
#nfts (id integer UNIQUE, url text, userid text, price integer)

#REST SECTION
# app = Flask(__name__)
# api = Api(app)

# parser = reqparse.RequestParser()
# parser.add_argument('message')

# class ChannelMessage(Resource):
#     def get(self, channel):
#         InQueue.put((REQUEST_MESSAGE, channel))
#         while True:
#             if not OutQueue.empty():
#                 messages = OutQueue.get()
#                 dictionary = {"messages": []}
#                 for message in messages:
#                     temp = {message[0]: [message[1], message[2]]}
#                     dictionary["messages"].append(temp)
#                 break
#             else:
#                 time.sleep(0.1)
#         return jsonify(dictionary)  #most recent 10 messages

#     def post(self, channel):
#         args = parser.parse_args()
#         message = args['message']
#         InQueue.put((channel, message))
#         return {"data": message}


# class ChannelSing(Resource):
#     def get(self):
#         InQueue.put((VOICE_REQUEST_MESSAGE))
#         while True:
#             if not OutQueue.empty():
#                 messages = OutQueue.get()
#                 dictionary = {"messages": []}
#                 position = 0
#                 for message in messages:
#                     position += 1
#                     temp = {str(position): [message[0], message[1]]}
#                     dictionary["messages"].append(temp)
#                 break
#             else:
#                 time.sleep(0.1)
#         return jsonify(dictionary)

#     def post(self):
#         args = parser.parse_args()
#         message = args['message']
#         InQueue.put((VOICE_SEND, message))
#         return {"data": message}

# api.add_resource(ChannelSing, "/robin/sing")
# api.add_resource(ChannelMessage, "/robin/message/<string:channel>")


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': IP_ADDRESS # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

#!radio
class Bandit():
    def __init__(self, data):    #TODO: preload data
        self.data = data    # A dictionary of songs and people who've liked them
        self.played = []    # A list of songs already played so far

    def nn(self):
        pass

    def popularity(self):
        temp_data = self.data.copy()
        for song in self.played:
            del temp_data[song]
        best_song = max(temp_data, key=temp_data.get)   #get the song in the dict with the largest value
        return best_song

    def get_song(self):
        song = self.popularity()
        self.played.append(song)
        return song


class YTDLSource(PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        #print(data)

        if 'entries' in data:
            if data['entries'] != []:
                # take first item from a playlist
                data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



class MyClient(Client):
    def __init__(self, inqueue, outqueue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Client
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.voice_queue = Queue()
        self.song_queue = []
        self.next_song = None
        self.playing = None
        self.looping = False
        self.voice_block = False
        self.db = connect(DATABASE_PATH)
        self.c = None
        self.vc = {}
        self.connected = False
        self.play_text = " is anyone interested in playing"
        self.yes_role_id = 757388821540372561
        self.no_role_id = 757389176449531954
        self.maybe_role_id = 967147708131475496
        self.initiate_role_id = 759600936435449896
        self.jeopardy = False
        self.jeopardy_host = ""
        self.answered = False
        self.think_lock = False
        self.waiting_channels = []
        self.waitlists = {"overwatch gang": [],
                            "civ gang": [],
                            "among us gang": [],
                            "league gang": [],
                            "tft gang": [],
                            "warcraft gang": [],
                            "minecraft gang": []}

        # create the background task and run it in the background
        # self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        await self.change_presence(activity = Game(name='!help'))
        print('Logged on as', self.user)

        # dojo = self.get_guild(578065102310342677)
        # general = self.get_channel(578065102310342679)
        self.channels = self.get_all_channels()
        self.text_channels = {}
        self.voice_channels = {}
        for channel in self.channels:
            if str(channel.type) == 'text':
                for member in channel.members:
                    if member.id == 662839781092491284: #662839781092491284
                        if channel.permissions_for(member).send_messages:
                            self.text_channels[channel.name] = channel.id
            elif str(channel.type) == 'voice':
                for member in channel.members:
                    if member.id == 662839781092491284: #662839781092491284
                        if channel.permissions_for(member).send_messages:
                            fixed_name = channel.name.replace(" ", '').strip().lower()
                            self.voice_channels[fixed_name] = channel.id
        self.c = self.db.cursor()
        try:
            self.conn, self.addr = start()
            send(self.conn, "Client:discord")
            self.connected = True
        except:
            pass
        try:
            self.jukebox.start()
            self.robin_STT.start()
            self.braincell_swap.start()
            self.posture_check.start()
            self.check_datetime.start()
        except:
            self.jukebox.restart()
            self.robin_STT.restart()
            self.braincell_swap.restart()
            self.posture_check.restart()
            self.check_datetime.restart()
        await self.debug("Robin has restarted!")


    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return


        elif message.content.startswith('!execute'):
            if str(message.author) == 'nickeick#9008':
                self.c.execute("DELETE FROM music WHERE song LIKE ? AND song LIKE ?",('%minutes%', '%seconds%'))
                #self.db.commit()
                #com_message = message.content.replace('!execute', '').strip()
                #self.c.execute("SELECT * from commands WHERE output = ?" (com_message,))
                #commands (command_name, output, author)
                #self.c.execute("CREATE TABLE nfts (id integer UNIQUE, url text, userid text, price integer)")
                #self.db.commit()
                # execute1 = ("MeltingSnowman#1699", 9)
                # c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", execute1)
                # db.commit()
                # c.execute("SELECT * FROM braincell_points")
                # items = c.fetchall()
                # for item in items:
                #     print(item[0] + ": " + str(item[1]))
                # _select = ("Jax#6424",)
                # c.execute("SELECT points FROM braincell_points WHERE name=? ", _select)
                # jax_cents = c.fetchone()
                # _insert = ("Jaxington#6424", jax_cents[0])
                # c.execute("INSERT into braincell_points VALUES (?,?)", _insert)
                # _delete = ("Jax#6424",)
                # c.execute("DELETE FROM braincell_points WHERE name=?", _delete)
                # db.commit()
                print("done")



        elif message.content.startswith('!help'):
            help_message = message.content.replace('!help', '').strip()
            if help_message == "gangs":
                await message.channel.send('''!join - Type !join followed by a role to join that role
!leave - Type !leave followed by a role to leave that role
!gangs - Type !gangs to get a complete list of the gang roles in the server''')
            elif help_message == "braincell":
                await message.channel.send('''!braincell - Type !braincell to see who has the server brain cell role
!think - Type !think when you have the braincell role to gain a common cent
!leaderboard - Type !leaderboard to see who has the most common cents
!give - Type !give [username/nickname] [number] to give your Common Cents to another member''')
            elif help_message == "play requests":
                await message.channel.send('''!play - Type !play in any gang related chat to see if anyone is interested in playing the game. People can react with their availability
!replay - Type !replay to replay the last !play request
!yes - Type !yes to see who responded "Yes" to your !play request
!no - Type !no to see who responded "No" to your !play request
!reset - Type !reset to reset the yesses and nos to your !play request''')
            elif help_message == "calendar":
                await message.channel.send('''!addevent - Type !addevent *event name* mm/dd/yyyy *time* to add an event to the calendar
!events - Type !events to get a list of outstanding events in the server
!delevent - Type !delevent to delete an event from the calendar
!today - Type !today to get the today's events from the calendar (Central Time)
!calendar - Type !calendar to use the Dojo's calendar''')
            elif help_message == "misc":
                await message.channel.send('''!robin - A description of Robin
!addwaitlist - Type !addwaitlist followed by the name of a role and @ing someone to add them to the waitlist for that game
!waitlist - Type !waitlist and a role to see who is on that waitlist
!icon - Type !icon to get the server icon image''')
            elif help_message == "singing":
                await message.channel.send('''!sing - A url or description of a song to have Robin play a song in a voice channel
!skip - To skip to the next song in the queue or to stop the current song
!pause - To pause the currently playing song
!resume - To continue a paused song
!upnext - To see which song is next in the queue''')
            else:
                await message.channel.send('''Send !help <category> to see the commands pertaining to the category.
Categories: gangs, braincell, play requests, calendar, singing, misc''')


        elif message.content == '!robin':
            await message.channel.send('Hello! I am a bot created by Nick who can speak on behalf of Nick.')

#---------------- Make Commands -----------------------------

        elif message.content.startswith('!addcom'):
            for role in message.author.roles:
                if role.name == "Server Admin":
                    await self.tutorial(message, [('command name', 'text'), ('output', 'text')])
                    try:
                        com_message = message.content.replace('!addcom', '').strip().split(' ', 1)
                        if com_message[0][0] != '!' or com_message[0] == None or com_message[1] == None:
                            break
                        addcom_insert = (com_message[0], com_message[1], str(message.author))
                        self.c.execute("INSERT INTO commands VALUES (?,?,?)", addcom_insert)
                        self.db.commit()
                        await message.channel.send('Made command ' + com_message[0] + ' to send ' + com_message[1])
                    except:
                        await message.channel.send('Invalid command')


        elif message.content.startswith('!delcom'):
            for role in message.author.roles:
                if role.name == "Server Admin":
                    await self.tutorial(message, [('command name', 'text')])
                    com_message = message.content.replace('!delcom', '').strip()
                    delcom_delete = (com_message,)
                    self.c.execute("DELETE from commands WHERE command_name=?", delcom_delete)
                    self.db.commit()
                    await message.channel.send("Deleted " + com_message)

        elif message.content.startswith('!editcom'):
            for role in message.author.roles:
                if role.name == "Server Admin":
                    await self.tutorial(message, [('command name', 'text'), ('existing output', 'text')])
                    try:
                        com_message = message.content.replace('!editcom', '').strip().strip().split(' ', 1)
                        assert com_message[0] != "", "You need to include a command name after !editcom"
                        assert com_message[0][0] == '!', "Be sure to add ! to the beginning of your command"
                        assert com_message[1] != "", "You need to include an output for the command you are editing. If you want to delete a command, use !delcom [command_name]"
                        self.c.execute("SELECT * from commands WHERE command_name=? AND output=?", (com_message[0], com_message[1]))
                        item = self.c.fetchone()
                        assert item != None, "Command or output not found"
                        author = message.author
                        channel = message.channel
                        def check(msg):
                            return msg.author == author and msg.channel == channel
                        await message.channel.send("What do you want to change it to?")
                        response = await self.wait_for('message', check=check, timeout=30)
                        self.c.execute("DELETE from commands WHERE command_name=? AND output=?", (com_message[0], com_message[1]))
                        editcom_insert = (com_message[0], response.content, str(message.author))
                        self.c.execute("INSERT INTO commands VALUES (?,?,?)", editcom_insert)
                        self.db.commit()
                        await message.channel.send(com_message[0] + " has been updated")
                    except IndexError:
                        await message.channel.send("You did not provide enough information. You need to include a command and an output to be edited")
                    except TimeoutError:
                        await message.channel.send("Command not edited (You took too long)")
                    except AssertionError as err:
                        await message.channel.send(err)


        elif message.content.startswith('!commands'):
            if str(message.author) == 'nickeick#9008':
                self.c.execute("SELECT command_name from commands")
                items = list(set(self.c.fetchall()))
                self.db.commit()
                for item in items:
                    await message.channel.send(item[0].strip("('), "))

#-------------------------Play Requests------------------------------------

        elif message.content.startswith('!join'):
            role_message = message.content.replace('!join', '').strip().lower()
            if role_message == '':
                sent = await message.channel.send('''__**React to Join a Role:**__
Join the Minecraft Gang: <:minecraft:586388193860124673>
Join the Overwatch Gang: <:overwatch:804144662372810763>
Join the TFT Gang: <:tft:804146585998065675>
Join the Civ Gang: <:civ:804144489349251123>
Join the Party Game Gang: <:jackbox:804146850104999946>
Join the League Gang: <:leagueoflegends:804146402258714634>
Join the Movie Night Gang: 🎥
Join the DND Gang: <:dnd:804147593768206378>
Join the Chess Gang: <:bishop:804145901630128128>
Join the Presentation Gang: 🧑‍💼
Join the Stardew Gang: <:chicken:804147857719951431>''')
                await sent.add_reaction("<:minecraft:586388193860124673>")
                await sent.add_reaction("<:overwatch:804144662372810763>")
                await sent.add_reaction("<:tft:804146585998065675>")
                await sent.add_reaction("<:civ:804144489349251123>")
                await sent.add_reaction("<:jackbox:804146850104999946>")
                await sent.add_reaction("<:leagueoflegends:804146402258714634>")
                await sent.add_reaction("🎥")
                await sent.add_reaction("<:dnd:804147593768206378>")
                await sent.add_reaction("<:bishop:804145901630128128>")
                await sent.add_reaction("🧑‍💼")
                await sent.add_reaction("<:chicken:804147857719951431>")
                return
            for role in message.guild.roles:
                if role.name.lower() in role_message:
                    if  ('gang' not in role.name.lower()) or role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy" or role.name == 'The Server Brain Cell' or role.name == 'Server Genius' or role.name == 'Pingcord':
                        await message.channel.send('You cannot join this role: ' + role.name)
                        return
                    else:
                        await message.author.add_roles(role)
                        if role.name == 'Movie Night Gang':
                            await message.channel.send('*This is an NSFW Gang*')
                        await message.channel.send('Added ' + message.author.display_name + ' to ' + role.name)


        elif message.content.startswith('!leave'):
            await self.tutorial(message, [('role', 'text')])
            role_message = message.content.replace('!leave', '').strip().lower()
            for role in message.guild.roles:
                if role.name.lower() in role_message:
                    if ('gang' not in role.name.lower()) or role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy":
                        await message.channel.send('You cannot leave this role: ' + role.name)
                        return
                    else:
                        await message.author.remove_roles(role)
                        await message.channel.send('Removed ' + message.author.display_name + ' from ' + role.name)


        elif message.content.startswith('!play'):
            for member in message.guild.get_role(self.yes_role_id).members:
                await member.remove_roles(message.guild.get_role(self.yes_role_id))
            for member in message.guild.get_role(self.no_role_id).members:
                await member.remove_roles(message.guild.get_role(self.no_role_id))
            time = message.content.replace('!play', '')
            mention = ""
            channel_name = message.channel.name
            for letter in channel_name:
                if letter == "-":
                    channel_name = channel_name.replace('-', ' ')
            for role in message.guild.roles:
                if role.name.lower() == channel_name:
                    mention = role.mention
            if mention != "":
                sent = await message.channel.send(mention + self.play_text + time + "?\n\nYesses:")
                await sent.add_reaction("✅")
                await sent.add_reaction("❌")
                await sent.add_reaction("❓")
                #self.play_messages.append(sent)
                if time == None:
                    time = ' '
                play_sql = (message.channel.name, time, '', '', str(message.author))
                # self.c.execute("REPLACE INTO play_requests (game, time, yes, no, requestor) VALUES (?,?,?,?,?)", play_sql)
                # self.db.commit()
            else:
                sent = await message.channel.send("Dojo," + self.play_text + time + "?\n\nYesses:")
                await sent.add_reaction("✅")
                await sent.add_reaction("❌")
                await sent.add_reaction("❓")


        elif message.content.startswith('!replay'):
            time = message.content.replace('!replay', '')
            mention = ""
            channel_name = message.channel.name
            for letter in channel_name:
                if letter == "-":
                    channel_name = channel_name.replace('-', ' ')
            for role in message.guild.roles:
                if role.name.lower() == channel_name:
                    mention = role.mention
            if mention != "":
                sent = await message.channel.send(mention + self.play_text + time + "?\n\nYesses:")
                await sent.add_reaction("✅")
                await sent.add_reaction("❌")
                replay_select = (message.channel.name,)
                self.c.execute("SELECT yes FROM play_requests WHERE game=?", replay_select)
                yes_list = self.c.fetchone()
                self.db.commit()
                for name in yes_list[0].split():
                    user = message.guild.get_member_named(name)
                    if user == None:
                        pass
                    else:
                        await user.add_roles(message.guild.get_role(self.yes_role_id))
                        await sent.edit(content=sent.content + '\n*' + user.display_name + '*')


        elif message.content.startswith('!reset'):
            for member in message.guild.get_role(self.yes_role_id).members:
                await member.remove_roles(message.guild.get_role(self.yes_role_id))
            for member in message.guild.get_role(self.no_role_id).members:
                await member.remove_roles(message.guild.get_role(self.no_role_id))
            await message.channel.send("Removed all YES and NO roles")


        elif message.content == '!yes':
            to_send = 'members said YES:'
            number = 0
            for member in message.guild.get_role(self.yes_role_id).members:
                number += 1
                to_send += '\n' + member.display_name
            await message.channel.send(str(number) + ' ' + to_send)


        elif message.content == '!no':
            to_send = 'members said NO:'
            number = 0
            for member in message.guild.get_role(self.no_role_id).members:
                number += 1
                to_send += '\n' + member.display_name
            await message.channel.send(str(number) + ' ' + to_send)


        elif message.content == '!maybe':
            to_send = 'members said MAYBE:'
            number = 0
            for member in message.guild.get_role(self.maybe_role_id).members:
                number += 1
                to_send += '\n' + member.display_name
            await message.channel.send(str(number) + ' ' + to_send)

#------------------------Waitlists----------------------------------

        elif message.content.startswith('!addwaitlist'):
            people = []
            waitlist_message = message.content.replace('!addwaitlist', '').strip().lower()
            for role in message.guild.roles:
                if role.name.lower() in waitlist_message:
                    waitlist_message = waitlist_message.replace(role.name.lower(), '').strip().lower()
                    waitlist = role.name.lower()
            for person in message.guild.members:
                if person.mentioned_in(message):
                    people.append(person)
            if people == []:
                people.append(message.author)
            to_send = 'These people have been added to the waitlist for ' + waitlist + ':'
            for person in people:
                to_send += '\n' + person.display_name
                try:
                    self.waitlists[waitlist].append(person)
                except:
                    self.waitlists[waitlist] = []
                    self.waitlists[waitlist].append(person)
            await message.channel.send(to_send)


        elif message.content.startswith('!waitlist'):
            waitlist = message.content.replace('!waitlist', '').strip().lower()
            to_send = 'These people are on the waitlist for ' + waitlist + ':'
            for person in self.waitlists[waitlist]:
                to_send += '\n' + person.display_name
            await message.channel.send(to_send)

#--------------------Jeopardy-----------------------------------------

        elif message.content.startswith('!jeopardy'):
            if message.content.replace('!jeopardy', '').strip().lower() == "start":
                self.jeopardy = True
                self.jeopardy_host = message.author.name
                await message.channel.send("A game of Jeopardy has started")
            elif message.content.replace('!jeopardy', '').strip().lower() == "stop":
                self.jeopardy = False
                self.jeopardy_host = ""
                await message.channel.send("Jeopardy has ended")


        elif message.content.startswith('buzz'):
            if self.jeopardy == True:
                if self.answered == False:
                    self.answered = True
                    await message.add_reaction("✅")
                    await message.add_reaction("❌")
                elif self.answered == True:
                    await message.delete()

#------------------------Gang Stuff-----------------------------

        elif message.content.startswith('!makegang'):
            for role in message.author.roles:
                if role.name == "Server Admin":
                    await self.tutorial(message, [('gang name', 'text')])
                    gang = message.content.replace('!makegang', '').strip().replace('gang', '')
                    new_role = await message.guild.create_role(name=gang + " Gang")
                    overwrites = {message.guild.default_role: PermissionOverwrite(read_messages=False),
                                    new_role: PermissionOverwrite(read_messages=True)}
                    await message.guild.create_text_channel(name=gang + "-gang", overwrites=overwrites, category=message.guild.get_channel(579796688420732949))
                    await message.channel.send(gang + ' Gang has been made! Type "!join ' + gang + ' Gang" to join')


        elif message.content.startswith('!gangs'):
            to_send = 'The Gangs:'
            for role in message.guild.roles:
                if "Gang" in role.name:
                    to_send += '\n' + role.name
            await message.channel.send(to_send)


        elif message.content.startswith('!roles'):
            sent = await message.channel.send('''__**React to Join a Role:**__
Join the Minecraft Gang: <:minecraft:586388193860124673>
Join the Overwatch Gang: <:overwatch:804144662372810763>
Join the TFT Gang: <:tft:804146585998065675>
Join the Civ Gang: <:civ:804144489349251123>
Join the Warcraft Gang: <:wow:804147220256915466>
Join the Jackbox Gang: <:jackbox:804146850104999946>
Join the League Gang: <:leagueoflegends:804146402258714634>
Join the Movie Night Gang: 🎥
Join the Among Us Gang: <:amongus:754595623415578665>
Join the RuneScape Gang: <:runescape:804148267327684648>
Join the DND Gang: <:dnd:804147593768206378>
Join the Chess Gang: <:bishop:804145901630128128>
Join the Presentation Gang: 🧑‍💼
Join the Stardew Gang: <:chicken:804147857719951431>
''')
            await sent.add_reaction("<:minecraft:586388193860124673>")
            await sent.add_reaction("<:overwatch:804144662372810763>")
            await sent.add_reaction("<:tft:804146585998065675>")
            await sent.add_reaction("<:civ:804144489349251123>")
            await sent.add_reaction("<:wow:804147220256915466>")
            await sent.add_reaction("<:jackbox:804146850104999946>")
            await sent.add_reaction("<:leagueoflegends:804146402258714634>")
            await sent.add_reaction("🎥")
            await sent.add_reaction("<:amongus:754595623415578665>")
            await sent.add_reaction("<:runescape:804148267327684648>")
            await sent.add_reaction("<:dnd:804147593768206378>")
            await sent.add_reaction("<:bishop:804145901630128128>")
            await sent.add_reaction("🧑‍💼")
            await sent.add_reaction("<:chicken:804147857719951431>")

#------------------------The Braincell-----------------------------

        elif message.content.startswith('!braincell'):
            for member in message.guild.members:
                if message.guild.get_role(771408034957623348) in member.roles:
                    await message.channel.send(member.display_name + ' is hogging the server brain cell')


        elif message.content.startswith('!think'):
            if message.guild.get_role(771408034957623348) in message.author.roles:
                if self.think_lock == False:
                    await message.channel.send("🧠 This makes cents 🪙")
                    think_select = (str(message.author),)
                    self.c.execute("SELECT points FROM braincell_points WHERE name=?", think_select)
                    points = self.c.fetchone()
                    if points == None:
                        think_replace = (str(message.author), 1)
                    else:
                        think_replace = (str(message.author), points[0]+1)
                    self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", think_replace)
                    for member in message.guild.members:        # Server Genius
                        if message.guild.get_role(779433226560864267) in member.roles:
                            await member.remove_roles(message.guild.get_role(779433226560864267))
                    self.c.execute("SELECT name FROM braincell_points ORDER BY points DESC")
                    genius_name = self.c.fetchone()
                    genius_member = message.guild.get_member_named(genius_name[0])
                    await genius_member.add_roles(message.guild.get_role(779433226560864267))
                    self.db.commit()
                    self.think_lock = True
                else:
                    await message.channel.send("You've already got your cent <:bonk:772161497031507968>")
            else:
                await message.channel.send("You don't have the brain cell <:bonk:772161497031507968>")

        elif message.content.startswith('!count'):
            think_select = (str(message.author),)
            self.c.execute("SELECT points FROM braincell_points WHERE name=?", think_select)
            points = self.c.fetchone()
            message.channel.send("You have " + str(points[0]) + " Common Cents")

        elif message.content.startswith('!leaderboard'):
            self.c.execute("SELECT * FROM braincell_points ORDER BY points DESC")
            items = self.c.fetchall()
            self.db.commit()
            to_send = '🪙  **Common Cents Leaderboard:**  🪙\n'
            j = 0
            for item in items:
                j+=1
                if j > 10:
                    break
                try:
                    name = message.guild.get_member_named(item[0]).display_name
                except AttributeError:
                    j-=1
                    continue
                to_send += str(j) + '. ' + name + ':'
                i = len(name)*2
                while i < 60:
                    to_send += ' '
                    i+=1
                cents = item[1]
                while cents > 0:
                    if (cents//100) > 0:
                        to_send += '💎'
                        cents -= 100
                    elif (cents//10) > 0:
                        to_send += '💵'
                        cents -= 10
                    else:
                        to_send += '🪙'
                        cents -= 1
                to_send += '|   ' + str(item[1]) + '\n'
            sent = await message.channel.send(to_send)
            await sent.add_reaction("⬅️")
            await sent.add_reaction("➡️")


        elif message.content.startswith('!give'):
            await self.tutorial(message, [('username', 'text'), ('amount', 'number')])
            give_message = message.content.replace('!give', '').strip()
            #print(give_message)
            try:
                give_re = search(r'(.+) (\d+)', give_message)
                assert give_re, give_message + ' has improper format'
                give = (give_re.group(1), give_re.group(2))
                assert message.guild.get_member_named(give[0]) != None, "Member does not exist"
                author_select = (str(message.author),)
                self.c.execute('SELECT points FROM braincell_points WHERE name=?', author_select)
                author_points = self.c.fetchone()
                receive_select = (str(message.guild.get_member_named(give[0])),)
                self.c.execute('SELECT points FROM braincell_points WHERE name=?', receive_select)
                receive_points = self.c.fetchone()
                assert author_points != None, "You have no Common Cents"
                assert author_points[0] >= int(give[1]), "You do not have enough Common Cents to give"
                assert int(give[1]) >= 0, "You cannot gift negative points"
                assert str(message.author) != str(message.guild.get_member_named(give[0])), "You cannot gift to yourself"
                author_replace = (str(message.author), author_points[0]-int(give[1]))
                self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", author_replace)
                if receive_points == None:
                    receive_replace = (str(message.guild.get_member_named(give[0])), int(give[1]))
                else:
                    receive_replace = (str(message.guild.get_member_named(give[0])), receive_points[0]+int(give[1]))
                self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", receive_replace)
                self.db.commit()
                await message.channel.send("You have given " + give[1] + " Common Cents to " + give[0])
            except TypeError:
                await message.channel.send("If you want to gift your Common Cents, be sure to type !give {nickname/username} {number}")
            except AssertionError as err:
                await message.channel.send(err)



#--------------------------Events Calendar-----------------------------

        elif message.content.startswith('!addevent'):
            await self.tutorial(message, [('event name', 'text'), ('date', 'mm/dd/yyyy'), ('time', '(H)H:MM*am/pm*'), ('optional gang name', 'text')])
            event_message = message.content.replace('!addevent', '').strip()
            try:
                assert event_message != '', "To make an event, type !addevent *event name* mm/dd/yyyy (H)H:MM*am/pm* *gang (optional)*"
                date_re = search(r'(.+) (\d\d)/(\d\d)/(\d\d\d\d) ((\d){1,2}:\d\d(am|pm))(.*)', event_message)
                assert date_re, event_message + ' does not have name, date, time'
                assert date_re.group(5)[0] != '0', event_message + ' Invalid format: includes 0 at beginning of hour'
                if date_re.group(8) == '':
                    gang_insert = 'none'
                else:
                    gang_insert = date_re.group(8).strip().lower()
                addevent_insert = (date_re.group(1).strip(), date_re.group(4), date_re.group(2), date_re.group(3), date_re.group(5), gang_insert)
                self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', addevent_insert)
                self.db.commit()
                await message.channel.send("You have added " + date_re.group(1).strip() +" on "+ date_re.group(2) +"/"+ date_re.group(3) +"/"+ date_re.group(4) +" at "+ date_re.group(5) + " to the Calendar")
            except AssertionError as err:
                await message.channel.send(err)


        elif message.content.startswith('!events'):
            self.c.execute("SELECT * FROM calendar ORDER BY year DESC, month DESC, day DESC")
            items = self.c.fetchall()
            to_send = ''
            for item in items:
                to_send += (item[0] +' on '+ str(item[2]) +'/'+ str(item[3]) +'/'+ str(item[1]) +' at '+ item[4])
                if item[5]:
                    to_send += (' in ' + item[5] + '\n')
                else:
                    to_send += '\n'
            if not to_send:
                await message.channel.send("There are no events on the calendar")
            else:
                await message.channel.send(to_send)


        elif message.content.startswith('!delevent'):
            await self.tutorial(message, [('event name', 'text')])
            event_message = message.content.replace('!delevent', '').strip()
            self.c.execute("SELECT * FROM calendar")
            before_num = len(self.c.fetchall())
            delevent_delete = (event_message,)
            self.c.execute("DELETE FROM calendar WHERE event_name=?", delevent_delete)
            self.db.commit()
            self.c.execute("SELECT * FROM calendar")
            after_num = len(self.c.fetchall())
            if before_num - after_num >= 1:
                await message.channel.send("Successfully deleted " + event_message + " event")
            else:
                await message.channel.send("No such event exists, be sure to type !delevent *event name*")


        elif message.content.startswith("!today"):
            await message.channel.send("Today's events are:")
            today = date.today()
            month = today.strftime("%m")
            day = today.strftime("%d")
            year = today.strftime("%Y")
            today_select = (month, day, year)
            self.c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", today_select)
            items = self.c.fetchall()
            to_send = ''
            for item in items:
                to_send += (item[0] + ' at ' + item[1])
                if item[2]:
                    to_send += (' in ' + item[2] + '\n')
                else:
                    to_send += '\n'
            if to_send:
                await message.channel.send(to_send)


        elif message.content.startswith("!tomorrow"):
            await message.channel.send("Tomorrow's events are:")
            tomorrow = date.today() + timedelta(days=1)
            month = tomorrow.strftime("%m")
            day = tomorrow.strftime("%d")
            year = tomorrow.strftime("%Y")
            tomorrow_select = (month, day, year)
            self.c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", tomorrow_select)
            items = self.c.fetchall()
            to_send = ''
            for item in items:
                to_send += (item[0] + ' at ' + item[1])
                if item[2]:
                    to_send += (' in ' + item[2] + '\n')
                else:
                    to_send += '\n'
            if to_send:
                await message.channel.send(to_send)


        elif message.content.startswith("!calendar"):
            today = date.today()
            to_send = "**The Dojo Calendar** on the week of *" + str(today) + "*\n"   #year - month - day
            day_num = today.isoweekday()
            counter = 0
            dailys = []
            self.c.execute("SELECT event_name, time, gang FROM calendar")
            items = self.c.fetchall()
            for item in items:
                if "daily" in item[0].lower():
                    dailys += (item[0], item[1], item[2])
            days_of_the_week = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
            for day in days_of_the_week:
                to_send += "__" + day + "__\n"
                dayofweek = today - timedelta(days=day_num) + timedelta(days=counter)
                month = dayofweek.strftime("%m")
                day = dayofweek.strftime("%d")
                year = dayofweek.strftime("%Y")
                calendar_select = (month, day, year)
                self.c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", calendar_select)
                get_items = self.c.fetchall()
                get_items.append(dailys)
                # items = [['None', 'None', 'None']]
                # for i in get_items:         #removes duplicates
                #     append_bool = True
                #     for item in items:
                #         print("i[0]:" + i[0])
                #         print("i[1]:" + i[1])
                #         print("i[2]:" + i[2])
                #         print("item[0]:" + item[0])
                #         print("item[1]:" + item[1])
                #         print("item[2]:" + item[2])
                #         if i[0] == item[0] and i[1] == item[1] and i[2] == item[2]:
                #             append_bool = False
                #     if append_bool == True:
                #         items.append(i)
                for item in get_items:
                    if item != []:
                        to_send += item[0] + ' at ' + item[1]
                        if item[2]:
                            to_send += ' (' + item[2] + ')'
                        to_send += '\n'
                counter += 1
                to_send += '\n'
            sent = await message.channel.send(to_send)
            await sent.add_reaction("⬅️")
            await sent.add_reaction("➡️")
            await sent.add_reaction("➕")
            await sent.add_reaction("➖")

#--------------------------Gambling-----------------------------------


        elif message.content.startswith("!casino"):
            self.c.execute('SELECT outcome, bets FROM casino')
            outcomes = self.c.fetchall()
            to_send = "🤑 **Common Cent Casino** 🤑\n\n"
            to_send += "__*Current Odds*__"
            for outcome in outcomes:
                out_cents = 0
                to_send += '\n' + str(outcome[0]) + ': '
                if outcome[1] != '':
                    to_parse = str(outcome[1])
                    to_parse = to_parse.split(',')     #parse the ledger
                    cents = 0
                    for item in to_parse:
                        if '#' not in item:
                            cents += int(item.strip('( )'))
                    out_cents = cents
                    while cents > 0:
                        if (cents//100) > 0:
                            to_send += '💎'
                            cents -= 100
                        elif (cents//10) > 0:
                            to_send += '💵'
                            cents -= 10
                        else:
                            to_send += '🪙'
                            cents -= 1
                to_send += '|   ' + str(out_cents)
            await message.channel.send(to_send)


        elif message.content.startswith("!gamble"):
            if str(message.author) == 'nickeick#9008':
                gamble_messages = message.content.replace('!gamble', '').strip().split(',')
                self.c.execute('DELETE FROM casino')
                for outcome in gamble_messages:
                    gamble_insert = (outcome.strip(), '')
                    self.c.execute('INSERT INTO casino VALUES (?,?)', gamble_insert)
                self.db.commit()
                await message.channel.send("Casino has set new bets!")


        elif message.content.startswith("!bet"):
            await self.tutorial(message, [('!casino bet name', 'text'), ('common cent amount', 'number')])
            bet_message = message.content.replace('!bet', '').strip()
            self.c.execute("SELECT outcome FROM casino")
            outcomes = self.c.fetchall()
            value_updated = False
            for outcome in outcomes:
                if str(outcome[0]) in bet_message:
                    value = outcome[0]
                    value_updated = True
                    pass
            try:
                assert value_updated == True, value + "is not a valid bet outcome"
                num = int(bet_message.replace(value, '').strip())
                bet_select = (value,)
                self.c.execute("SELECT bets FROM casino WHERE outcome=?", bet_select)
                ledger = self.c.fetchone()
                bet = (str(message.author), num)
                if ledger[0] == '':
                    bet_replace = (value, str(bet))
                else:
                    bet_replace = (value, ledger[0] + ',' + str(bet))         #add the bet to the end of the ledger
                author_select = (str(message.author),)
                self.c.execute("SELECT points FROM braincell_points WHERE name=?", author_select)
                author_points = self.c.fetchone()
                robin_select = ("Robin Otto#7657",)
                self.c.execute("SELECT points FROM braincell_points WHERE name=?", robin_select)
                robin_points = self.c.fetchone()
                assert author_points[0] >= num, "User bet more points than they had"
                subtract_replace = (str(message.author), author_points[0] - num)
                self.c.execute("REPLACE INTO braincell_points VALUES (?,?)", subtract_replace)
                robin_replace = ("Robin Otto#7657", robin_points[0] + num)
                self.c.execute("REPLACE INTO braincell_points VALUES (?,?)", robin_replace)
                self.c.execute("REPLACE INTO casino VALUES (?,?)", bet_replace)
                self.db.commit()
                await message.channel.send("Your bet has been placed")
            except AssertionError as err:
                await message.channel.send(err)


        elif message.content.startswith("!payout"):
            if str(message.author) == 'nickeick#9008':
                try:
                    payout_message = message.content.replace('!payout', '').strip()
                    self.c.execute('SELECT outcome, bets FROM casino')
                    outcomes = self.c.fetchall()
                    winners = {}
                    cents = 0
                    winner_bool = False
                    for outcome in outcomes:
                        ledger = str(outcome[1])
                        ledger = ledger.split(',')                  #parse the ledger
                        if outcome[0] != payout_message:            #losers
                            for item in ledger:
                                if '#' not in item:
                                    try:
                                        cents += int(item.strip('( )'))
                                    except:
                                        cents += 0
                        else:                                       #winners
                            while len(ledger) > 0:
                                item = ledger[0]
                                if '#' in item:
                                    if item.strip("( )''") in winners.keys():
                                        winners[item.strip("( )''")] += int(ledger[1].strip('( )'))
                                        ledger.pop(0)
                                        ledger.pop(0)
                                    else:
                                        winners[item.strip("( )''")] = int(ledger[1].strip('( )'))
                                        ledger.pop(0)
                                        ledger.pop(0)
                            winner_bool = True
                    if winner_bool == False:
                        raise ValueError(payout_message + " is not a valid input")
                    if winners == {}:                                   #if there are no winners
                        losers = {}
                        for outcome in outcomes:
                            ledger = str(outcome[1])
                            ledger = ledger.split(',')                  #parse the ledger
                            if outcome[0] != payout_message:            #losers
                                while len(ledger) > 0:
                                    item = ledger[0]
                                    if '#' in item:                     #if the item is a username
                                        if item.strip("( )''") in losers.keys():
                                            losers[item.strip("( )''")] += int(ledger[1].strip('( )'))
                                            ledger.pop(0)
                                            ledger.pop(0)
                                        else:
                                            losers[item.strip("( )''")] = int(ledger[1].strip('( )'))
                                            ledger.pop(0)
                                            ledger.pop(0)
                        for key in losers.keys():
                            robin_points_old_select = ("Robin Otto#7657",)
                            self.c.execute("SELECT points FROM braincell_points WHERE name=?", robin_points_old_select)
                            robin_points_old = self.c.fetchone()
                            robin_points_new = ("Robin Otto#7657", robin_points_old[0] - losers[key])
                            self.c.execute("REPLACE INTO braincell_points VALUES (?,?)", robin_points_new)           #take cents from Robin

                            loser_select = (key,)
                            self.c.execute("SELECT points FROM braincell_points WHERE name=?", loser_select)
                            loser_cents = self.c.fetchone()
                            new_loser_cents = (key, loser_cents[0] + losers[key])
                            self.c.execute("REPLACE INTO braincell_points VALUES (?,?)", new_loser_cents)
                            await message.channel.send(message.guild.get_member_named(key).display_name + " you were given your " + str(losers[key]) + " cents back")
                        await message.channel.send("Nobody wins, your cents have been returned.")
                    else:
                        winners_total = 0
                        winners_ratio = dict(reversed(sorted(winners.items(), key=lambda item: item[1])))         #sorts in value order
                        winners_payout = winners_ratio.copy()
                        for value in winners_ratio.values():
                            winners_total += int(value)
                        for key in winners_ratio.keys():
                            winners_ratio[key] = winners_ratio[key]/winners_total       #turn winners_ratio into a ratio of winner cents to total winner cents
                        old_cents = cents
                        while cents > 0:                                                #cents distribution algorithm
                            changed_bool = False
                            for key in winners_ratio.keys():
                                if cents <= 0:
                                    break
                                if winners_payout[key]/(winners_total + (old_cents - cents))  < winners_ratio[key]:
                                    winners_payout[key] += 1
                                    cents -= 1
                                    changed_bool = True
                            if changed_bool == False:
                                for key in winners_payout.keys():
                                    winners_payout[key] += 1
                                    cents -= 1
                                    break
                        for key in winners_payout.keys():
                            robin_points_old_select = ("Robin Otto#7657",)
                            self.c.execute("SELECT points FROM braincell_points WHERE name=?", robin_points_old_select)
                            robin_points_old = self.c.fetchone()
                            robin_points_new = ("Robin Otto#7657", robin_points_old[0] - winners_payout[key])
                            self.c.execute("REPLACE INTO braincell_points VALUES (?,?)", robin_points_new)           #remove points from Robin

                            winner_select = (key,)
                            self.c.execute("SELECT points FROM braincell_points WHERE name=?", winner_select)
                            winner_cents = self.c.fetchone()
                            new_winner_cents = (key, winner_cents[0] + winners_payout[key])
                            self.c.execute("REPLACE INTO braincell_points VALUES (?,?)", new_winner_cents)
                            await message.channel.send("Congrats " + message.guild.get_member_named(key).display_name + "! You won " + str(winners_payout[key] - winners[key]) + " Common Cents (plus your original bet of " + str(winners[key]) + ")")
                    self.c.execute("DELETE FROM casino")
                    self.db.commit()
                except Exception as error:
                    await message.channel.send('There was an error in paying out the bets: ' + str(error))


#---------------------------Presentation Gang-------------------------

        elif message.content.startswith("!presnight"):
            await message.channel.send('''What is Presentation night? Answer: It is a night where presenters show off presentations that they made themselves
How do I get added to the list? Answer: Just type !presenter in the #music-requests-and-bot-commands channel
What should my presentation be on? Answer: It can be on whatever you want, but there are optional themes every month
When is it? How often is it? Where can I learn more? Answer: Check #announcements for up to date information''')

#--------------------------Poll---------------------------------------

        elif message.content.startswith("!poll"):
            await self.tutorial(message, [('option name', 'text with :'), ('emoji', 'emoji')])
            try:
                poll_message = message.content.replace('!poll', '').strip()
                poll_re = search(r'((.+):(.+),)+((.+):(.+))', poll_message)
                to_send = message.author.display_name + " made a poll:"
                emojis = []
                for item in poll_re.groups():
                    if ':' in item:
                        pair = item.strip(',').split(':')
                        to_send += '\n' + pair[0] + ' (' + pair[1] + '):'
                        emojis.append(pair[1])
                sent = await message.channel.send(to_send)
                for emoji in emojis:
                    await sent.add_reaction(emoji)
                    self.c.execute("REPLACE INTO emojis (emoji) VALUES (?)", emoji)
            except ValueError:
                await message.channel.send("Be sure to type !poll {option}:{emoji}, {option}:{emoji}, etc. (Don't forget to remove spaces)")

#--------------------------Voice--------------------------------------

        elif message.content.startswith("!connect"):
            await self.vc_connect(message)

        elif message.content.startswith("!incall"):
            await message.channel.send(str(self.vc[str(message.author.voice.channel.id)].is_connected()))

        elif message.content.startswith("!disconnect"):
            await self.vc_disconnect(message)

        elif message.content.startswith("!say"):    #requires input
            await self.tutorial(message, [('speech content', 'text with no symbols')])
            say_content = message.content.replace("!say", '').strip()
            send(self.conn, "Send to:voice " + say_content)
            if self.voice_block == True:
                self.voice_queue.put(message)
            else:
                await self.vc_say(message)


        elif message.content.startswith("!sing"):
            #await self.debug("test1")
            await self.tutorial(message, [('song', 'text or URL')])
            url = message.content.replace("!sing", '').strip()
            #await self.debug("test2")
            try:
                assert message.author.voice != None, "You must be connected to a voice channel to use !sing"
                await self.vc_connect(message)
                #await self.debug("test2 and a half")
                title_url = await self.vc_play_song(url, message)
                #await self.debug("test3")
                if title_url != None:
                    #await self.debug("test4")
                    channel_id = str(message.author.voice.channel.id)
                    new_song = (url,channel_id,message)
                    self.song_queue.append(new_song)
                    #await self.debug("test5")
                    await message.channel.send("Your song has been queued")
            except AssertionError as err:
                await message.channel.send(err)
            except Exception as err:
                print(err)


        elif message.content.startswith("!stop"):
            #skip current song and dump all songs from queue
            voice = await self.vc_get_obj(message)
            voice.stop()
            self.song_queue = []
            self.next_song = None
            await message.channel.send("Robin's singing has stopped...")



        elif message.content.startswith('!skip'):
            voice = await self.vc_get_obj(message)
            voice.stop()
            await message.channel.send("Skipping song...")

        elif message.content.startswith('!pause'):
            voice = await self.vc_get_obj(message)
            if voice.is_playing():
                voice.pause()
            else:
                await message.channel.send("No audio is playing")

        elif message.content.startswith('!resume'):
            voice = await self.vc_get_obj(message)
            if voice.is_paused():
                voice.resume()
            else:
                await message.channel.send("No audio is paused")

        #jukebox
        elif message.content.startswith('!upnext'):
            if self.next_song == None:
                await message.channel.send("There is no queued song")
            else:
                await message.channel.send(self.next_song[0])

        elif message.content.startswith('!data'):
            if str(message.author) == 'nickeick#9008':
                self.c.execute("SELECT * FROM music")
                items = self.c.fetchall()
                for item in items:
                    print(item[0] + " | " + item[1] + " | " + str(item[2]))

        elif message.content.startswith('!radio'):
            if message.author.voice != None:
                try:
                    await self.vc_connect(message)
                except Exception as err:
                    print(err)
            voice = await self.vc_get_obj(message)
            songs = {}
            for member in voice.channel.members:
                statement = 'SELECT song, liked FROM music WHERE userid=?'
                input_tuple = (member.id,)
                self.c.execute(statement, input_tuple) #get every song
                items = self.c.fetchall()
                for item in items:
                    adding = item[1]*2 - 1
                    if item[0] in songs.keys():
                        songs[item[0]] += adding
                    else:
                        songs[item[0]] = adding
            recommender = Bandit(songs)
            await message.channel.send("Robin is now in Radio mode... (Use !stop to return to normal)")
            song_playing = False
            while True:
                if not song_playing:
                    best_song = recommender.get_song()
                    #self.song_queue = [(best_song, str(message.author.voice.channel.id), message)] + self.song_queue
                    await self.vc_play_song(best_song, message)   #Returns None if played, (title, url) if queued
                    song_playing = True
                    await sleep(1)
                else:
                    if voice.is_playing() or voice.is_paused():
                        async with message.channel.typing():
                            await sleep(1)
                    else:
                        song_playing = False
                    if not voice.is_connected():
                        break
            await message.channel.send("Robin has returned to Request mode")

        elif message.content.startswith('!queue'):
            if self.next_song != None:
                to_send = 'Up next: ' + self.next_song[0] + ' in ' + self.get_channel(int(self.next_song[1])).name
                item_num = 1
                for song in self.song_queue:
                    item_num += 1
                    to_send += '\n' + str(item_num) + '. '+ song[0] + ' in ' + self.get_channel(int(song[1])).name
                await message.channel.send(to_send)
            else:
                await message.channel.send('There are no songs in queue')

        elif message.content.startswith('!loop'):
            voice = await self.vc_get_obj(message)
            if not self.looping:
                if (voice.is_playing() or voice.is_paused()) and self.playing != None:
                    self.looping = True
                    await message.channel.send('Robin is looping the current song...')
                    while self.looping:
                        while voice.is_playing() or voice.is_paused():
                            async with message.channel.typing():
                                await sleep(1)
                        if self.looping:
                            await self.vc_play_song(self.playing, message)
                else:
                    await message.channel.send("Robin isn't singing a song right now")
            else:
                self.looping = False
                await message.channel.send('Robin has stopped looping')



#--------------------------NFTs--------------------------------------

        elif message.content.startswith('!sell'):
            await self.tutorial(message, [('price', 'number'), ('NFT image', 'attached picture or GIF')])
            message_content = message.content.replace("!sell", '').strip()
            try:
                price = int(message_content)
                assert price > 0, "Price listed was not positive"
                assert message.attachments != None, "NFT was not attached"
                url = message.attachments[0].url
                self.c.execute("SELECT COUNT(*) FROM nfts WHERE userid = ? AND price != ?", (str(message.author.id), 0))
                amount = self.c.fetchone()[0]
                assert amount < 3, "You already have the maximum amount of NFTs listed"
                self.c.execute("SELECT MAX(id) FROM nfts")
                id_max = self.c.fetchone()[0]
                if id_max == None:
                    id_max = 0
                values = (id_max + 1, url, str(message.author.id), message_content)
                self.c.execute("INSERT INTO nfts VALUES (?,?,?,?)", values)
                await message.channel.send("Your NFT (NFT #" + str(id_max + 1) + ")  has been listed for " + str(message_content) + " cents")
                self.db.commit()
            except AssertionError as err:
                await message.channel.send(err)
            except ValueError as err:
                await message.channel.send("A valid price was not listed")

        elif message.content.startswith("!resell"):
            await self.tutorial(message, [('NFT ID you own', 'number')])
            id_price = message.content.replace("!resell", '').strip().split()
            try:
                self.c.execute("SELECT url, userid, price FROM nfts WHERE id = ?", (int(id_price[0]),))
                nft_info = self.c.fetchone()
                assert nft_info != None, "An NFT with that ID does not exist"
                assert nft_info[1] == str(message.author.id), "You cannot sell someone else's NFT"
                assert int(id_price[1]) > 0, "NFT price must be a positive number"
                self.c.execute("SELECT COUNT(*) FROM nfts WHERE userid = ? AND price != ?", (str(message.author.id), 0))
                amount = self.c.fetchone()[0]
                assert amount < 3, "You already have the maximum amount of NFTs listed"
                self.c.execute("REPLACE INTO nfts (id, url, userid, price) VALUES (?,?,?,?)", (id_price[0], nft_info[0], nft_info[1], id_price[1]))
                self.db.commit()
                await message.channel.send("You have relisted NFT #" + id_price[0])
            except AssertionError as err:
                await message.channel.send(err)

        elif message.content.startswith("!shop"):
            message_content = message.content.replace("!shop", '').strip()
            try:
                if message_content == '':
                    owner = message.author
                else:
                    owner = message.guild.get_member_named(message_content)
                assert owner != None, "Member does not exist"
                self.c.execute("SELECT id, url, price FROM nfts WHERE userid = ?", (str(owner.id),))
                items = self.c.fetchall()
                await message.channel.send(owner.nick + "'s NFT shop includes:")
                for item in items:
                    if item[2] != 0:
                        embed = Embed(title="NFT #" + str(item[0]), description="Listed for " + str(item[2]) + " Common Cents")
                        embed.set_image(url=item[1])
                        await message.channel.send(embed=embed)
            except AssertionError as err:
                await message.channel.send(err)
            except ValueError as err:
                await message.channel.send(err)

        elif message.content.startswith("!buy"):
            await self.tutorial(message, [('NFT ID', 'number')])
            nft_id = message.content.replace("!buy", '').strip()
            try:
                self.c.execute("SELECT url, userid, price FROM nfts WHERE id = ?", (int(nft_id),))
                nft_info = self.c.fetchone()
                assert nft_info != None, "An NFT with that ID does not exist"
                assert nft_info[2] != 0, "That NFT is not for sale"
                assert nft_info[1] != str(message.author.id), "You cannot buy your own NFT"
                self.c.execute("SELECT points FROM braincell_points WHERE name=?", (str(message.author),))
                author_info = self.c.fetchone()
                assert author_info != None, "You do not have any Common Cents"
                assert author_info[0] >= nft_info[2], "You do not have enough Common Cents"
                self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?,?)", (str(message.author), author_info[0] - nft_info[2]))
                owner = self.get_user(int(nft_info[1]))
                self.c.execute("SELECT points FROM braincell_points WHERE name=?", (str(owner),))
                owner_points = self.c.fetchone()
                if owner_points == None:
                    points = nft_info[2]
                else:
                    points = owner_points[0] + nft_info[2]
                self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?,?)", (str(owner), points))
                self.c.execute("REPLACE INTO nfts (id, url, userid, price) VALUES (?,?,?,?)", (int(nft_id), nft_info[0], str(message.author.id), 0))
                await message.channel.send("You have purchased NFT #" + nft_id + " from " + owner.name)
                self.db.commit()
            except AssertionError as err:
                await message.channel.send(err)

        elif message.content.startswith("!blockchain"):
            self.c.execute("SELECT * FROM nfts")
            items = self.c.fetchall()
            for item in items:
                if item[3] != 0:
                    owner = self.get_user(int(item[2]))
                    embed = Embed(title="NFT #" + str(item[0]), description="Listed for " + str(item[3]) + " Common Cents by " + owner.name)
                    embed.set_image(url=item[1])
                    await message.channel.send(embed=embed)

        elif message.content.startswith("!collection"):
            await self.tutorial(message, [('username', "user's nickname")])
            message_content = message.content.replace("!collection", '').strip()
            try:
                if message_content == '':
                    owner = message.author
                else:
                    owner = message.guild.get_member_named(message_content)
                assert owner != None, "Member does not exist"
                self.c.execute("SELECT id, url, price FROM nfts WHERE userid = ?", (str(owner.id),))
                items = self.c.fetchall()
                await message.channel.send(owner.nick + "'s NFT collection includes:")
                for item in items:
                    if item[2] == 0:
                        embed = Embed(title="NFT #" + str(item[0]), description="Owned by " + owner.nick)
                        embed.set_image(url=item[1])
                        await message.channel.send(embed=embed)
            except AssertionError as err:
                await message.channel.send(err)
            except ValueError as err:
                await message.channel.send(err)

        elif message.content.startswith("!unlist"):
            await self.tutorial(message, [('NFT ID', 'number')])
            message_content = message.content.replace("!unlist", '').strip()
            try:
                self.c.execute("SELECT url, userid FROM nfts WHERE id=?", (int(message_content),))
                nft_info = self.c.fetchone()
                assert nft_info != None, "The NFT ID you gave does not exist"
                assert nft_info[1] == str(message.author.id), "You do not own this NFT"
                self.c.execute("REPLACE INTO nfts (id, url, userid, price) VALUES (?,?,?,?)", (int(message_content), nft_info[0], str(message.author.id), 0))
                self.db.commit()
                await message.channel.send("You have returned NFT #" + message_content + " to your collection")
            except AssertionError as err:
                await message.channel.send(err)

        elif message.content.startswith("!nft"):
            await self.tutorial(message, [('NFT ID', 'number')])
            message_content = message.content.replace("!nft", '').strip()
            try:
                self.c.execute("SELECT url, userid FROM nfts WHERE id=?", (int(message_content),))
                nft_info = self.c.fetchone()
                assert nft_info != None, "The NFT ID you gave does not exist"
                owner = message.guild.get_member(int(nft_info[1]))
                embed = Embed(title="NFT #" + str(message_content), description="Owned by " + owner.nick)
                embed.set_image(url=nft_info[0])
                await message.channel.send(embed=embed)
            except AssertionError as err:
                await message.channel.send(err)

        elif message.content.startswith("!remove"):
            await self.tutorial(message, [('NFT ID', 'number')])
            message_content = message.content.replace("!remove", '').strip()
            author = str(message.author.id)
            try:
                self.c.execute("SELECT price FROM nfts WHERE userid=? AND id=?", (author, int(message_content)))
                nft = self.c.fetchone()
                assert nft != None, "You do not own the NFT ID you gave"
                assert nft[0] != 0, "This NFT is listed in your shop. Please !unlist your NFT before removing it"
                self.c.execute("DELETE FROM nfts WHERE userid=? AND id=?", (author, int(message_content)))
                self.db.commit()
                await message.channel.send("You have removed NFT #" + message_content)
            except AssertionError as err:
                await message.channel.send(err)


#--------------------------Misc---------------------------------------

        elif message.content.startswith('!whenjoin'):
            year = str(message.author.joined_at.year)
            month = str(message.author.joined_at.month)
            day = str(message.author.joined_at.day)
            hour = str(message.author.joined_at.hour)
            minute = str(message.author.joined_at.minute)
            second = str(message.author.joined_at.second)
            await message.channel.send(month + '/' + day + '/' + year + ' (m/d/y) at ' + hour + ':' + minute + ':' + second + ' GMT')

        elif message.content.startswith('!howlong'):
            diff = datetime.now() - message.author.joined_at
            await message.channel.send('You have been in the Dojo for ' + str(diff.days) + ' days')

        elif message.content.startswith('!nicksleep'):
            self.c.execute("SELECT count FROM counters WHERE counter = ?", ("nick_sleep",))
            nick_sleep = self.c.fetchone()
            times = nick_sleep[0] + 1
            await message.channel.send("Nick has fallen asleep in the Dojo " + str(times) + " times")
            self.c.execute("REPLACE INTO counters (counter, count) VALUES (?, ?)", ("nick_sleep", times))
            self.db.commit()

        elif message.content.startswith("I'm "):
            if message.guild.id == 578065102310342677:
                message_content = message.content.replace("I'm ", '').strip()
                await message.channel.send("Hi " + message_content + ", I'm Robin")


        elif "thank you robin" in message.content.lower():
            await message.channel.send("You're welcome")

        elif "this is so sad" in message.content.lower():
            await self.vc_connect(message)
            try:
                await self.vc_play_song('https://www.youtube.com/watch?v=Gl6ekgobG2k&ab_channel=ReptileLegitYT',message)
            except:
                pass

        elif "goodnight girl" in message.content.lower():
            await self.vc_connect(message)
            try:
                await self.vc_play_song('https://www.youtube.com/watch?v=ykLDTsfnE5A&ab_channel=J7ck2',message)
            except:
                pass

        elif message.content.startswith('!8ball'):
            answers = ['Absolutely will happen!', 'Maybe someday...', 'Probably I guess', 'Yes, definitely', "I don't know dude", "I can't tell", 'The answer is no', 'It looks doubtful', "Don't count on it", 'No']
            ans = randint(0, len(answers))
            await message.channel.send(answers[ans])

        elif message.content.startswith('!nerd'):
            rando = randint(1,len(message.guild.members))
            num = 0
            for member in message.guild.members:
                num += 1
                if rando == num:
                    await message.channel.send(member.display_name + " is a nerd")

        elif message.content.startswith('!icon'):
            await message.channel.send("", file=File("dojo.png"))


        elif message.content.startswith('!gibby'):
            await message.channel.send("<:gibby:760384610696953887>")


        elif message.content.startswith('!longgibby'):
            await message.channel.send("", file=File("longgibby.jpg"))


        elif message.content.startswith('!widegibby'):
            await message.channel.send("", file=File("widegibby.jpg"))


        elif message.content.startswith('!test'):
            await message.channel.send("Test Successful!")


        elif message.content.startswith('!alive'):
            await message.channel.send("I am alive. - Robin")

        elif message.content.startswith('!'):
            self.c.execute("SELECT * FROM commands")        # to be optimized
            commands = self.c.fetchall()
            for command in commands:
                if message.content == command[0]:
                    await message.channel.send(command[1])
            self.db.commit()

#----------------------------EVENTS-------------------------------------------

    async def on_reaction_add(self, reaction, user):
        #for !play requests
        if reaction.message.author == self.user and self.play_text in reaction.message.content and user != self.user:
            if reaction.emoji == "✅":
                await user.add_roles(reaction.message.guild.get_role(self.yes_role_id))
                await reaction.message.edit(content=reaction.message.content + '\n*' + user.display_name + '*')
                #checkmark_select = (reaction.message.channel.name,)
                #self.c.execute("SELECT yes FROM play_requests WHERE game=?", checkmark_select)
                #yes_list = self.c.fetchone()
                #yes_list = yes_list[0] + ' ' + str(user)
                #checkmark_update = (yes_list, reaction.message.channel.name)
                #self.c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", checkmark_update)
                #self.db.commit()
            if reaction.emoji == "❌":
                await user.add_roles(reaction.message.guild.get_role(self.no_role_id))
                #xmark_select = (reaction.message.channel.name,)
                #self.c.execute("SELECT no FROM play_requests WHERE game=?", xmark_select)
                #no_list = self.c.fetchone()
                #no_list = no_list[0] + ' ' + str(user)
                #xmark_update = (no_list, reaction.message.channel.name)
                #self.c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", xmark_update)
                #self.db.commit()
            if reaction.emoji == "❓":
                await user.add_roles(reaction.message.guild.get_role(self.maybe_role_id))
        #for !jeopardy games
        if reaction.message.content == "buzz" and self.jeopardy == True and self.jeopardy_host == user.name:
            if reaction.emoji == "✅":
                await reaction.message.channel.send(reaction.message.author.nick + " got it correct")
                self.answered = False
            if reaction.emoji == "❌":
                await reaction.message.channel.send(reaction.message.author.nick + " got it incorrect")
                self.answered = False
        #for !poll
        if "made a poll:" in reaction.message.content and user != self.user:
            self.c.execute("SELECT emoji FROM emojis WHERE emoji = ?", str(reaction.emoji))
            emojis = self.c.fetchall()
            for emoji in emojis:
                to_send = ''
                if emoji[0] in reaction.message.content:
                    options = reaction.message.content.split(":")
                    for option in options:
                        if emoji[0] in option and option[0] != emoji[0]:
                            to_send = to_send + option + ':' + emoji[0]
                        else:
                            to_send = to_send + option + ':'
                    to_send = to_send[:-1]
                    await reaction.message.edit(content=to_send)
        #for !calendar
        if reaction.message.author == self.user and "The Dojo Calendar" in reaction.message.content and user != self.user:
            if reaction.emoji == "⬅️":
                await reaction.remove(user)
                date_re = search("(.*)(\d\d\d\d)-(\d\d)-(\d\d)(.*)", reaction.message.content)
                today = date(int(date_re.group(2)), int(date_re.group(3)), int(date_re.group(4))) - timedelta(weeks=1)
                to_send = "**The Dojo Calendar** on the week of *" + str(today) + "*\n"   #year - month - day
                day_num = today.isoweekday()
                counter = 0
                dailys = []
                self.c.execute("SELECT event_name, time, gang FROM calendar")
                items = self.c.fetchall()
                for item in items:
                    if "daily" in item[0].lower():
                        dailys += (item[0], item[1], item[2])
                days_of_the_week = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
                for day in days_of_the_week:
                    to_send += "__" + day + "__\n"
                    dayofweek = today - timedelta(days=day_num) + timedelta(days=counter)
                    month = dayofweek.strftime("%m")
                    day = dayofweek.strftime("%d")
                    year = dayofweek.strftime("%Y")
                    calendar_select = (month, day, year)
                    self.c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", calendar_select)
                    get_items = self.c.fetchall()
                    get_items.append(dailys)
                    items = []
                    for i in get_items:         #removes duplicates
                        if i != []:
                            append_bool = True
                            for item in items:
                                if item != []:
                                    if i[0] == item[0] and i[1] == item[1] and i[2] == item[2]:
                                        append_bool = False
                            if append_bool == True:
                                items.append(i)
                    for item in items:
                        if item != []:
                            to_send += item[0] + ' at ' + item[1]
                            if item[2]:
                                to_send += ' (' + item[2] + ')'
                            to_send += '\n'
                    counter += 1
                    to_send += '\n'
                await reaction.message.edit(content=to_send)
            if reaction.emoji == "➡️":
                await reaction.remove(user)
                date_re = search("(.*)(\d\d\d\d)-(\d\d)-(\d\d)(.*)", reaction.message.content)
                today = date(int(date_re.group(2)), int(date_re.group(3)), int(date_re.group(4))) + timedelta(weeks=1)
                to_send = "**The Dojo Calendar** on the week of *" + str(today) + "*\n"   #year - month - day
                day_num = today.isoweekday()
                counter = 0
                dailys = []
                self.c.execute("SELECT event_name, time, gang FROM calendar")
                items = self.c.fetchall()
                for item in items:
                    if "daily" in item[0].lower():
                        dailys += (item[0], item[1], item[2])
                days_of_the_week = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
                for day in days_of_the_week:
                    to_send += "__" + day + "__\n"
                    dayofweek = today - timedelta(days=day_num) + timedelta(days=counter)
                    month = dayofweek.strftime("%m")
                    day = dayofweek.strftime("%d")
                    year = dayofweek.strftime("%Y")
                    calendar_select = (month, day, year)
                    self.c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", calendar_select)
                    get_items = self.c.fetchall()
                    get_items.append(dailys)
                    items = []
                    for i in get_items:         #removes duplicates
                        if i != []:
                            append_bool = True
                            for item in items:
                                if item != []:
                                    if i[0] == item[0] and i[1] == item[1] and i[2] == item[2]:
                                        append_bool = False
                            if append_bool == True:
                                items.append(i)
                    for item in items:
                        if item != []:
                            to_send += item[0] + ' at ' + item[1]
                            if item[2]:
                                to_send += ' (' + item[2] + ')'
                            to_send += '\n'
                    counter += 1
                    to_send += '\n'
                await reaction.message.edit(content=to_send)
                #print("next week")
            if reaction.emoji == "➕":
                timeout_bool = False
                components = ["*event name*", "mm/dd/yyyy", "(H)H:MM*am/pm*", '*gang (If none, type "none")*']
                sections = []
                author = user
                channel = reaction.message.channel
                def check(msg):
                    return msg.author == author and msg.channel == channel
                for section in components:
                    await reaction.message.channel.send("To add your event, please type the " + section + ":")
                    try:
                        response = await self.wait_for('message', check=check, timeout=30)
                    except TimeoutError:
                        await reaction.message.channel.send("Event not created (You took too long)")
                        timeout_bool = True
                        break
                    else:
                        sections.append(response.content)
                if timeout_bool == False:
                    date_re = search(r'(\d\d)/(\d\d)/(\d\d\d\d)', sections[1])
                    time_re = search('((\d){1,2}:\d\d(am|pm))', sections[2])
                    if not (date_re and time_re):
                        await reaction.message.channel.send("Invalid date/time")
                        raise ValueError(sections[0] + ' does not have date or time')
                    if time_re.group(1)[0] == '0':
                        await reaction.message.channel.send("Invalid date/time: Included 0 at start of hour")
                        raise ValueError(reaction.message + ' Invalid format: includes 0 at beginning of hour')
                    else:
                        addevent_insert = (sections[0], date_re.group(3), date_re.group(1), date_re.group(2), time_re.group(0), sections[3])
                        self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', addevent_insert)
                        self.db.commit()
                        await reaction.message.channel.send("Successfully added an event to the calendar")
                await reaction.remove(user)
            if reaction.emoji == "➖":
                author = user
                channel = reaction.message.channel
                def check(msg):
                    return msg.author == author and msg.channel == channel
                await reaction.message.channel.send("To delete an event, please type the *event name*")
                try:
                    response = await self.wait_for('message', check=check, timeout=30)
                except TimeoutError:
                    await reaction.message.channel.send("Event not deleted (You took too long)")
                else:
                    self.c.execute("SELECT * FROM calendar")
                    before_num = len(self.c.fetchall())
                    delevent_delete = (response.content,)
                    self.c.execute("DELETE FROM calendar WHERE event_name=?", delevent_delete)
                    self.db.commit()
                    self.c.execute("SELECT * FROM calendar")
                    after_num = len(self.c.fetchall())
                    if before_num - after_num >= 1:
                        await reaction.message.channel.send("Successfully deleted " + response.content + " event")
                    else:
                        await reaction.message.channel.send("No such event exists. Try again and be sure to type the *exact* event name (case sensitive)")
                finally:
                    await reaction.remove(user)

        #!leaderboard
        if reaction.message.author == self.user and "Common Cents Leaderboard:" in reaction.message.content and user != self.user:
            if reaction.emoji == "⬅️":
                number_test = False
                for char in reaction.message.content:   #get the number of the last rank
                    if char == '.':
                        number_test = False
                    if number_test:
                        number += char
                    if char == '\n':
                        number = ''
                        number_test = True
                if int(number) < 20:
                    number = 20
                self.c.execute("SELECT * FROM braincell_points ORDER BY points DESC")
                items = self.c.fetchall()
                self.db.commit()
                to_send = '🪙  **Common Cents Leaderboard:**  🪙\n'
                j = 0
                for item in items:
                    j+=1
                    if j > int(number) - 10:
                        break
                    if j > int(number) - 20:
                        try:
                            name = reaction.message.guild.get_member_named(item[0]).display_name
                        except AttributeError:
                            j-=1
                            continue
                        to_send += str(j) + '. ' + name + ':'
                        i = len(name)*2
                        while i < 60:
                            to_send += ' '
                            i+=1
                        cents = item[1]
                        while cents > 0:
                            if (cents//100) > 0:
                                to_send += '💎'
                                cents -= 100
                            elif (cents//10) > 0:
                                to_send += '💵'
                                cents -= 10
                            else:
                                to_send += '🪙'
                                cents -= 1
                        to_send += '|   ' + str(item[1]) + '\n'
                await reaction.message.edit(content=to_send)
                await reaction.remove(user)

            if reaction.emoji == "➡️":
                number_test = False
                for char in reaction.message.content:   #get the number of the last rank
                    if char == '.':
                        number_test = False
                    if number_test:
                        number += char
                    if char == '\n':
                        number = ''
                        number_test = True
                self.c.execute("SELECT * FROM braincell_points ORDER BY points DESC")
                items = self.c.fetchall()
                self.db.commit()
                if int(number) + 10 > len(items):
                    number = len(items) - 10
                to_send = '🪙  **Common Cents Leaderboard:**  🪙\n'
                j = 0
                for item in items:
                    j+=1
                    if j > int(number) + 10:
                        break
                    if j > int(number):
                        try:
                            name = reaction.message.guild.get_member_named(item[0]).display_name
                        except AttributeError:
                            j-=1
                            continue
                        to_send += str(j) + '. ' + name + ':'
                        i = len(name)*2
                        while i < 60:
                            to_send += ' '
                            i+=1
                        cents = item[1]
                        while cents > 0:
                            if (cents//100) > 0:
                                to_send += '💎'
                                cents -= 100
                            elif (cents//10) > 0:
                                to_send += '💵'
                                cents -= 10
                            else:
                                to_send += '🪙'
                                cents -= 1
                        to_send += '|   ' + str(item[1]) + '\n'
                await reaction.message.edit(content=to_send)
                await reaction.remove(user)
        #for !sing
        if reaction.message.author == self.user and len(reaction.message.embeds) != 0 and user != self.user:
            if "Robin is now singing:" in reaction.message.embeds[0].title:
                if str(reaction.emoji) == "👍":
                    song_name = reaction.message.embeds[0].description
                    values = (user.id, song_name)
                    self.c.execute("SELECT * FROM music WHERE userid=? AND song=?", values)
                    items = self.c.fetchall()
                    if len(items) > 0:
                        values = (user.id, song_name, 1)
                        self.c.execute("REPLACE INTO music (userid, song, liked) VALUES (?, ?, ?)", values)
                    else:
                        values = (user.id, song_name, 1)
                        self.c.execute("INSERT INTO music VALUES (?, ?, ?)", values)
                    self.db.commit()
                if str(reaction.emoji) == "👎":
                    song_name = reaction.message.embeds[0].description
                    values = (user.id, song_name)
                    self.c.execute("SELECT * FROM music WHERE userid=? AND song=?", values)
                    items = self.c.fetchall()
                    if len(items) > 0:
                        values = (user.id, song_name, 0)
                        self.c.execute("REPLACE INTO music (userid, song, liked) VALUES (?, ?, ?)", values)
                    else:
                        values = (user.id, song_name, 0)
                        self.c.execute("INSERT INTO music VALUES (?, ?, ?)", values)
                    self.db.commit()


#````````````````````MARKED FOR CLEANUP`````````````````````````

        if reaction.message.author == self.user and "React to Join a Role:" in reaction.message.content and user != self.user:
            before_roles = len(user.roles)
            if str(reaction.emoji) == "🎥":
                if reaction.message.guild.get_role(736618281632268369) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(736618281632268369))   #Movie Night Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Movie Night Gang")
                    await reaction.message.channel.send('*This is an NSFW Gang*')
            elif str(reaction.emoji) == "🧑‍💼":
                if reaction.message.guild.get_role(799751796281049149) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(799751796281049149))   #Presentation Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Presentation Gang")
            elif reaction.emoji.id == 586388193860124673:
                if reaction.message.guild.get_role(578065727148523520) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(578065727148523520))   #Minecraft Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Minecraft Gang")
            elif reaction.emoji.id == 804144662372810763:
                if reaction.message.guild.get_role(631381336216567811) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(631381336216567811))   #Overwatch Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Overwatch Gang")
            elif reaction.emoji.id == 804146585998065675:
                if reaction.message.guild.get_role(631381556677574666) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(631381556677574666))   #TFT Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to TFT Gang")
            elif reaction.emoji.id == 804144489349251123:
                if reaction.message.guild.get_role(652672401036935190) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(652672401036935190))   #Civ Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Civ Gang")
            elif reaction.emoji.id == 804147220256915466:
                if reaction.message.guild.get_role(697229534595907595) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(697229534595907595))   #Warcraft Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Warcraft Gang")
            elif reaction.emoji.id == 804146850104999946:
                if reaction.message.guild.get_role(712503396317265930) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(712503396317265930))   #Jackbox Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Jackbox Gang")
            elif reaction.emoji.id == 804146402258714634:
                if reaction.message.guild.get_role(730207607180099654) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(730207607180099654))   #League Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to League Gang")
            elif reaction.emoji.id == 754595623415578665:
                if reaction.message.guild.get_role(752041724750069861) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(752041724750069861))   #Among Us Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Among Us Gang")
            elif reaction.emoji.id == 804148267327684648:
                if reaction.message.guild.get_role(758201150762778664) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(758201150762778664))   #RuneScape Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to RuneScape Gang")
            elif reaction.emoji.id == 804147593768206378:
                if reaction.message.guild.get_role(774093125144018984) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(774093125144018984))   #DND Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to DND Gang")
            elif reaction.emoji.id == 804145901630128128:
                if reaction.message.guild.get_role(794745361461280768) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(794745361461280768))   #Chess Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Chess Gang")
            elif reaction.emoji.id == 804147857719951431:
                if reaction.message.guild.get_role(803020418319122453) not in user.roles:
                    await user.add_roles(reaction.message.guild.get_role(803020418319122453))   #Stardew Gang
                    await reaction.message.channel.send("Added " + user.display_name + " to Stardew Gang")
            await reaction.remove(user)
#`````````````````````````````````````````````````````

    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) == "☑️" and payload.message_id == 759611108541071380:
            await payload.member.remove_roles(payload.member.guild.get_role(self.initiate_role_id))
        #for react-roles
        #await self.debug("test 1")
        if payload.emoji.id == 1067155138235596810 and payload.channel_id == 1027646452371046430 and payload.member != self.user:
            await self.debug("test 2")
            partial = payload.message_id.get_partial_message()
            message = await partial.fetch()
            role_name = message.content.strip().lower()
            self.debug(role_name)
            for role in message.guild.roles:
                #print(role)
                if role.name.lower() == role_name:
                    await self.debug("test 3")
                    await payload.member.add_roles(role)
                    await message.remove_reaction(self.get_emoji(1067155138235596810), payload.member)

        if payload.emoji.id == 1067157267922821220 and payload.channel_id == 1027646452371046430 and payload.member != self.user:
            partial = payload.message_id.get_partial_message()
            message = await partial.fetch()
            role_name = message.content.strip().lower()
            for role in message.guild.roles:
                if role.name.lower() == role_name:
                    await payload.member.remove_roles(role)
                    await message.remove_reaction(self.get_emoji(1067157267922821220), payload.member)


    async def on_reaction_remove(self, reaction, user):
        if reaction.message.author == self.user and self.play_text in reaction.message.content and user != self.user:
            if reaction.emoji == "✅":
                await user.remove_roles(reaction.message.guild.get_role(self.yes_role_id))
                reaction_message = reaction.message.content.replace('\n*'+user.display_name+'*', '').strip()
                await reaction.message.edit(content=reaction_message)
                # checkmark_select = (reaction.message.channel.name,)
                # self.c.execute("SELECT yes FROM play_requests WHERE game=?", checkmark_select)
                # yes_list = self.c.fetchone()
                # yes_list = yes_list[0].replace(str(user), '').strip()
                # checkmark_update = (yes_list, reaction.message.channel.name)
                # self.c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", checkmark_update)
                # self.db.commit()
            if reaction.emoji == "❌":
                await user.remove_roles(reaction.message.guild.get_role(self.no_role_id))
                # xmark_select = (reaction.message.channel.name,)
                # self.c.execute("SELECT no FROM play_requests WHERE game=?", xmark_select)
                # no_list = self.c.fetchone()
                # no_list = no_list[0].replace(str(user), '').strip()
                # xmark_update = (no_list, reaction.message.channel.name)
                # self.c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", xmark_update)
                # self.db.commit()
            if reaction.emoji == "❓":
                await user.remove_roles(reaction.message.guild.get_role(self.maybe_role_id))
        #for !poll
        if "made a poll:" in reaction.message.content and user != self.user:
            self.c.execute("SELECT emoji FROM emojis WHERE emoji = ?", str(reaction.emoji))
            emojis = self.c.fetchall()
            for emoji in emojis:
                to_send = ''
                if emoji[0] in reaction.message.content:
                    options = reaction.message.content.split(":")
                    for option in options:
                        if emoji[0] in option and option[0] == emoji[0]:
                            to_send = to_send + option[1:] + ':'
                        else:
                            to_send = to_send + option + ':'
                    to_send = to_send[:-1]
                    await reaction.message.edit(content=to_send)
        if reaction.message.author == self.user and len(reaction.message.embeds) != 0 and user != self.user:
            if "Robin is now singing:" in reaction.message.embeds[0].title:
                if str(reaction.emoji) == "👍":
                    song_name = reaction.message.embeds[0].description
                    values = (user.id, song_name, 1)
                    self.c.execute("DELETE FROM music WHERE userid=? AND song=? AND liked=?", values)
                    self.db.commit()
                if str(reaction.emoji) == "👎":
                    song_name = reaction.message.embeds[0].description
                    values = (user.id, song_name, 0)
                    self.c.execute("DELETE FROM music WHERE userid=? AND song=? AND liked=?", values)
                    self.db.commit()


    async def on_member_join(self, member):
        try:
            await member.add_roles(member.guild.get_role(self.initiate_role_id))
        except:
            pass


    async def on_voice_state_update(self, member, before, after):
        try:
            if before.channel != None:                          #Tests if leaving vc
                if member == self.user:                         #If Robin is leaving, remove from vc dict
                    del self.vc[str(before.channel.id)]
                if str(before.channel.id) in self.vc.keys():    #Tests if in vc with Robin
                    if len(before.channel.members) == 1:        #Tests if Robin is alone
                        await self.vc[str(before.channel.id)].disconnect()
                        del self.vc[str(before.channel.id)]
        except:
            pass
        try:
            mute = self.get_channel(870946768928534528)
            if before.channel == None and after.channel != None and after.channel.guild.id == 578065102310342677:
                await mute.set_permissions(member, send_messages = True, read_messages = True)
            elif before.channel != None and after.channel == None and before.channel.guild.id == 578065102310342677:
                await mute.set_permissions(member, send_messages = False, read_messages = False)
        except:
            pass


#--------------------FUNCTIONS------------------------

    async def post(self, channel_name, text):
        channels = self.text_channels
        channel = self.get_channel(channels[channel_name]) # channel ID goes here
        await channel.send(text)


    async def vc_connect(self, message):
        try:
            user = message.author
            voice_channel = user.voice.channel
            assert voice_channel != None, "You are not in a voice channel"
            if str(user.voice.channel.id) in self.vc.keys():
                pass
            else:
                for voice_client in self.voice_clients:
                    if voice_client.guild == message.guild:
                        assert not (voice_client.is_playing() or voice_client.is_paused()), "I am currently active in another voice channel. Thank you for your patience"
                        await voice_client.disconnect()
                        if str(message.author.voice.channel.id) in self.vc:
                            del self.vc[str(message.author.voice.channel.id)]
                        if message.id in self.waiting_channels:
                            self.waiting_channels.remove(message.id)
                voice_obj = await voice_channel.connect()
                self.vc[str(user.voice.channel.id)] = voice_obj
                #await message.channel.send('Robin has connected')
        except AssertionError as err:
            if message.id not in self.waiting_channels:
                await message.channel.send(err)
                self.waiting_channels.append(message.id)


    async def vc_disconnect(self, message):
        try:
            assert message.author.voice != None, "You must be in a voice channel with Robin to disconnect her"
            channel_id = str(message.author.voice.channel.id)
            assert channel_id in self.vc.keys(), "You must be in a voice channel with Robin to disconnect her"
            assert self.vc[channel_id] != None, 'Robin must !connect first'
            assert self.vc[channel_id].channel == message.author.voice.channel, 'You must be in a voice channel with Robin to disconnect her'
            if self.vc[str(message.author.voice.channel.id)].is_connected():
                await self.vc[str(message.author.voice.channel.id)].disconnect()
                await message.channel.send('Robin has disconnected')
            else:
                await message.channel.send('Robin is not in a channel')
            if str(message.author.voice.channel.id) in self.vc:
                del self.vc[str(message.author.voice.channel.id)]
        except AssertionError as err:
            await message.channel.send(err)


    async def vc_say(self, message):        #instead of message, make it channel
        self.voice_block = True
        try:
            assert message.author.voice != None, "You must be in a voice channel to use the !say command"
            channel_id = str(message.author.voice.channel.id)
            assert channel_id in self.vc.keys(), "Robin is not connected"
            assert self.vc[channel_id] != None, "Robin is not connected"
            assert self.vc[channel_id].channel == message.author.voice.channel, "Robin is not connected"

            say_content = message.content.replace("!say", '').strip()
            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                say_content = say_content.replace(char, '')
            assert len(say_content) > 0 or len(say_content) < 255, 'Message must be 1-255 characters long'

            while not isfile(AUDIO_PATH+"/"+say_content+".mp3"):
                await sleep(0.1)
                print("test")
            self.vc[channel_id].play(FFmpegPCMAudio(executable=FFMPEG_PATH, source=AUDIO_PATH+"/"+say_content+".mp3"))
            while self.vc[channel_id].is_playing():
                await sleep(10)
                if self.vc[channel_id] == None:
                    break
            remove(AUDIO_PATH+"/"+say_content+".mp3")
        except AssertionError as err:
            if str(err) == "Robin is not connected":
                await self.vc_connect(message)
                if self.vc[channel_id].channel == message.author.voice.channel:
                    await self.vc_say(message)
            await message.channel.send(err)
        finally:
            self.voice_block = False


    async def vc_play_song(self, url, message):     #Fix 403s
        #!sing
        #await self.debug("two and one")
        player = await YTDLSource.from_url(url, loop=None, stream=True)
        #await self.debug("two and two")
        try:
            self.vc[str(message.author.voice.channel.id)].play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        except Exception as err:
            return (player.title, player.url)
        #await self.debug("two and three")
        minutes = player.duration // 60
        seconds = player.duration % 60
        embed = Embed(title="Robin is now singing:", description=f"{player.title}", footer=f"({minutes} minutes {seconds} seconds)", url=player.url)
        current_song = await message.channel.send(embed=embed)
        self.playing = url
        await current_song.add_reaction('👍')
        await current_song.add_reaction('👎')
        return None


    async def vc_get_obj(self, message):
        try:
            channel_id = str(message.author.voice.channel.id)
        except:
            await message.channel.send("You are not in a voice channel")
        try:
            voice = self.vc[channel_id]
        except:
            await message.channel.send("Robin is not connected to your voice channel")
        return voice


    async def transaction(self, giver, receiver, value, message):    #self type, string, string, int, message
        giver_member = str(message.guild.get_member_named(giver))
        receiver_member = str(message.guild.get_member_named(receiver))
        try:
            assert giver_member != None, "Member does not exist"
            assert receiver_member != None, "Member does not exist"
            assert value >= 0, "You cannot gift negative points"
            assert giver_member != receiver_member, "You cannot gift to yourself"
            giver_select = (giver_member,)
            self.c.execute('SELECT points FROM braincell_points WHERE name=?', giver_select)
            giver_points = self.c.fetchone()
            receive_select = (receiver_member,)
            self.c.execute('SELECT points FROM braincell_points WHERE name=?', receive_select)
            receive_points = self.c.fetchone()
            assert giver_points != None, "You have no Common Cents"
            assert giver_points[0] >= value, "You do not have enough Common Cents to give"
            author_replace = (giver_member, giver_points[0]-value)
            self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", author_replace)
            if receive_points == None:
                receive_replace = (receiver_member, value)
            else:
                receive_replace = (receiver_member, receive_points[0]+value)
            self.c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", receive_replace)
            self.db.commit()
            return "You have given " + value + " Common Cents to " + receiver
        except AssertionError as err:
            await message.channel.send(err)

    async def tutorial(self, message, options):
        if ' ' not in message.content.strip():
            to_send = message.content + ': Use of ' + message.content + ' requires'
            for option in options:
                to_send += ' ['
                to_send += option[0]
                to_send += '] ('
                to_send += option[1]
                to_send += ')'
                if option != options[-1]:
                    to_send += ','
            await message.channel.send(to_send)

    async def debug(self, text):
        user = self.get_user(344304643767271425)
        await user.send(text)



#-----------------------LOOPS-------------------------------

    @loop(seconds = 1)
    async def jukebox(self):
        if len(self.song_queue) != 0:
            #print("jukebox 1")
            if self.next_song == None:
                self.next_song = self.song_queue.pop()  #self.next_song: (url, channel_id, message)
                #print("jukebox 2")
        if self.next_song != None:
            #print("jukebox 3")
            if self.next_song[1] in self.vc.keys():
                #print("jukebox 4")
                voice_client = self.vc[self.next_song[1]]
                if voice_client.is_connected() and not (voice_client.is_playing() or voice_client.is_paused() and not self.looping):
                    #print("jukebox 5")
                    await self.vc_play_song(self.next_song[0], self.next_song[2])
                    self.next_song = None
            else:
                if len(self.next_song[2].author.voice.channel.members) < 1:        #Tests if Robin is alone
                    #print("jukebox 6")
                    await self.vc_disconnect(self.next_song[2])
                    self.song_queue = []
                else:
                    await self.vc_connect(self.next_song[2])
                    #print("jukebox 7")


    @loop(seconds = 5)
    async def robin_STT(self):
        if self.connected == True:
            msg = get_msg()
            if msg != None:
                if msg == DISCONNECT_MESSAGE:
                    self.connected = False
                elif msg == CONNECT_UI_MESSAGE:
                    channel_list = 'channel_list: '
                    for channel in self.text_channels.keys():
                        channel_list += str(channel) + ','
                    channel_list = channel_list.strip(',')
                    send(self.conn, 'Send to:UI ' + channel_list)
                else:
                    try:
                        to_post = msg.split(' ', 1)
                        await self.post(to_post[0], to_post[1])
                    except:
                        pass
        #API
        if not self.inqueue.empty():  # Structure the queue and check which type of input is used and then do the approp action
            to_use = self.inqueue.get()
            if to_use[0] == REQUEST_MESSAGE:
                channels = self.text_channels
                channel = self.get_channel(channels[to_use[1]])
                messages = [(message.id, message.author.display_name, message.content) async for message in channel.history(limit=10)]
                self.outqueue.put(messages)
            elif to_use[0] == VOICE_REQUEST_MESSAGE:
                out_list = []
                if self.next_song != None:
                    out_list.append((self.next_song[0], self.get_channel(int(self.next_song[1])).name))   # url, channel name
                    for song in self.song_queue:
                        out_list.append((song[0], self.get_channel(int(song[1])).name))
                else:
                    out_list.append((None, None))
                self.outqueue.put(out_list)
            elif to_use[0] == VOICE_SEND_MESSAGE:
                message = await self.get_channel(582064740973543435).send("Queueing " + to_use[1] + "...")
                try:
                    assert message.author.voice != None, "Robin must be connected to a voice channel"
                    title_url = await self.vc_play_song(url, message)
                    if title_url != None:
                        channel_id = str(message.author.voice.channel.id)
                        self.song_queue = [(url,channel_id,message)] + self.song_queue
                        await message.channel.send("Your song has been queued")
                except AssertionError as err:
                    await message.channel.send(err)
                except Exception as err:
                    print(err)
            else:
                await self.post(to_use[0], to_use[1])
            #print("You said " + to_use[0] + " to " + to_use[1])
        if (not self.voice_queue.empty()) and self.voice_block == False:
            to_say = self.voice_queue.get()
            await self.vc_say(to_say)

    @loop(minutes = 20)
    async def braincell_swap(self):
        members = self.get_channel(578065102310342679).members      #get the-main-dojo members
        not_bots = []
        for member in members:
            if not member.bot: #bots
                not_bots.append(member)
        braincell_role = self.get_guild(578065102310342677).get_role(771408034957623348)
        #print(not_bots)
        for member in not_bots:
            if braincell_role in member.roles:
                await member.remove_roles(braincell_role)
        size = len(not_bots)
        new_user = randint(1,size)
        i = 0
        for member in not_bots:
            i+=1
            if i == new_user:
                await member.add_roles(braincell_role)
        self.think_lock = False


    @loop(hours = 3)
    async def posture_check(self):
        user = self.get_user(295033460794589184)
        await user.send("Posture Check!")

    @loop(minutes = 1)
    async def check_datetime(self):
        today = date.today()
        month = today.strftime("%m")
        day = today.strftime("%d")
        year = today.strftime("%Y")
        t = localtime()
        current_time = strftime("%I:%M%p", t)
        if current_time[0] == '0':
            current_time = current_time[1:]
        check_datetime_select = (month, day, year, current_time.lower())
        self.c.execute("SELECT event_name, gang FROM calendar WHERE month = ? AND day = ? AND year = ? AND time = ?", check_datetime_select)
        events = self.c.fetchall()
        for event in events:
            #await self.get_channel(582060071052115978).send(event[0] + " is starting right now!")
            if event[1] and (event[1] != "none"):
                mention = ''
                for role in self.get_guild(578065102310342677).roles:
                    if role.name.lower() == event[1].lower():   #find gang role from gang field
                        mention = role.mention
                        channel_name = role.name.lower()
                        for letter in role.name.lower():
                            if letter == ' ':
                                channel_name = channel_name.replace(' ', '-')
#````````````````````````````````````MARKED FOR CLEANUP````````````````````````````````````
                        for channel in self.get_guild(578065102310342677).text_channels:    #find gang channel from gang role
                            if channel.name == channel_name:
                                if 'daily' in event[0].lower():
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    daily_select = (event[0],)
                                    self.c.execute('SELECT * FROM calendar WHERE event_name = ?', daily_select)
                                    daily_event = self.c.fetchone()
                                    self.c.execute('DELETE FROM calendar WHERE event_name = ?', daily_select)
                                    daily_tomorrow = date.today() + timedelta(days=1)
                                    daily_insert = (daily_event[0], daily_tomorrow.year, daily_tomorrow.month, daily_tomorrow.day, daily_event[4], daily_event[5])
                                    self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', daily_insert)
                                    self.db.commit()
                                elif 'weekly' in event[0].lower():
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    weekly_select = (event[0],)
                                    self.c.execute('SELECT * FROM calendar WHERE event_name = ?', weekly_select)
                                    weekly_event = self.c.fetchone()
                                    self.c.execute('DELETE FROM calendar WHERE event_name = ?', weekly_select)
                                    next_week = date.today() + timedelta(weeks=1)
                                    weekly_insert = (weekly_event[0], next_week.year, next_week.month, next_week.day, weekly_event[4], weekly_event[5])
                                    self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', weekly_insert)
                                    self.db.commit()
                                elif 'monthly' in event[0].lower():
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    monthly_select = (event[0],)
                                    self.c.execute('SELECT * FROM calendar WHERE event_name = ?', monthly_select)
                                    monthly_event = self.c.fetchone()
                                    self.c.execute('DELETE FROM calendar WHERE event_name = ?', monthly_select)
                                    if date.today().month == 2:
                                        extra_days = 0
                                    elif date.today().month == 4 or 6 or 9 or 11:
                                        extra_days = 2
                                    else:
                                        extra_days = 3
                                    next_month = date.today() + timedelta(weeks=4, days=extra_days)
                                    monthly_insert = (monthly_event[0], next_month.year, next_month.month, next_month.day, monthly_event[4], monthly_event[5])
                                    self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', monthly_insert)
                                    self.db.commit()
                                else:
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    self.c.execute("DELETE FROM calendar WHERE month = ? AND day = ? AND year = ? AND time = ?", check_datetime_select)
                                    self.db.commit()
            else:
                #await self.get_channel(582060071052115978).send(event[0] + " is starting right now!")
                if 'daily' in event[0].lower():
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    daily_select = (event[0],)
                    self.c.execute('SELECT * FROM calendar WHERE event_name = ?', daily_select)
                    daily_event = self.c.fetchone()
                    self.c.execute('DELETE FROM calendar WHERE event_name = ?', daily_select)
                    daily_tomorrow = date.today() + timedelta(days=1)
                    daily_insert = (daily_event[0], daily_tomorrow.year, daily_tomorrow.month, daily_tomorrow.day, daily_event[4], daily_event[5])
                    self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', daily_insert)
                    self.db.commit()
                elif 'weekly' in event[0].lower():
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    weekly_select = (event[0],)
                    self.c.execute('SELECT * FROM calendar WHERE event_name = ?', weekly_select)
                    weekly_event = self.c.fetchone()
                    self.c.execute('DELETE FROM calendar WHERE event_name = ?', weekly_select)
                    next_week = date.today() + timedelta(weeks=1)
                    weekly_insert = (weekly_event[0], next_week.year, next_week.month, next_week.day, weekly_event[4], weekly_event[5])
                    self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', weekly_insert)
                    self.db.commit()
                elif 'monthly' in event[0].lower():
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    monthly_select = (event[0],)
                    self.c.execute('SELECT * FROM calendar WHERE event_name = ?', monthly_select)
                    monthly_event = self.c.fetchone()
                    self.c.execute('DELETE FROM calendar WHERE event_name = ?', monthly_select)
                    if date.today().month == 2:
                        extra_days = 0
                    elif date.today().month == 4 or 6 or 9 or 11:
                        extra_days = 2
                    else:
                        extra_days = 3
                    next_month = date.today() + timedelta(weeks=4, days=extra_days)
                    monthly_insert = (monthly_event[0], next_month.year, next_month.month, next_month.day, monthly_event[4], monthly_event[5])
                    self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', monthly_insert)
                    self.db.commit()
                elif 'birthday' in event[0].lower():
                    await self.get_channel(578065102310342679).send(event[0])
                    birthday_select = (event[0],)
                    self.c.execute('SELECT * FROM calendar WHERE event_name = ?', birthday_select)
                    birthday_event = self.c.fetchone()
                    self.c.execute('DELETE FROM calendar WHERE event_name = ?', birthday_select)
                    birthday_insert = (birthday_event[0], date.today().year + 1, date.today().month, date.today().day, birthday_event[4], birthday_event[5])
                    self.c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', birthday_insert)
                    self.db.commit()
                else:
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    self.c.execute("DELETE FROM calendar WHERE month = ? AND day = ? AND year = ? AND time = ?", check_datetime_select)
                    self.db.commit()
#```````````````````````````````````````````````````````````````````````````````

#def start(host):
    #app.run(host=host)

if __name__ == '__main__':
    #api_start = Thread(target=start, args=('0.0.0.0',))
    #api_start.start()
    client = MyClient(InQueue, OutQueue, intents=intents)
    client.run(TOKEN)
