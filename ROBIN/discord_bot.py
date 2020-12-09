from discord import Client, Game, File, PermissionOverwrite
from discord.ext.tasks import loop
from discord.utils import get
from asyncio import sleep
from queue import Queue
from random import randint
from sqlite3 import connect
from re import search
from datetime import date, timedelta
from time import localtime, strftime

# intents = Intents.default()
# intents.members = True
riot_key = 'RGAPI-c1dea331-c67e-470a-b89f-09980629c53f'

MyQueue = Queue()
db = connect('discord.db')
#tables:
#commands (command_name, output, author)
#play_requests (UNIQUE game text, time text, yes text, no text, requestor text)
#braincell_points (name text UNIQUE, points integer)
#calendar (event_name text, year integer, month integer, day integer, time text, gang text)


#create a cursor
c = db.cursor()
#create a table


class MyClient(Client):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue
        self.play_text = " is anyone interested in playing"
        self.yes_role_id = 757388821540372561
        self.no_role_id = 757389176449531954
        self.initiate_role_id = 759600936435449896
        self.jeopardy = False
        self.jeopardy_host = ""
        self.answered = False
        self.think_lock = False
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

        self.robin_STT.start()
        self.braincell_swap.start()
        self.check_datetime.start()

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        elif message.content.startswith('!help'):
            await message.channel.send('''!robin - A description of Robin
!join - Type !join followed by a role to join that role
!leave - Type !leave followed by a role to leave that role
!gangs - Type !gangs to get a complete list of the gang roles in the server
!addwaitlist - Type !addwaitlist followed by the name of a role and @ing someone to add them to the waitlist for that game
!waitlist - Type !waitlist and a role to see who is on that waitlist
!play - Type !play in any gang related chat to see if anyone is interested in playing the game. People can react with their availability
!replay - Type !replay to replay the last !play request
!yes - Type !yes to see who responded "Yes" to your !play request
!no - Type !no to see who responded "No" to your !play request
!reset - Type !reset to reset the yesses and nos to your !play request
!icon - Type !icon to get the server icon image
!braincell - Type !braincell to see who has the server brain cell role
!think - Type !think when you have the braincell role to gain a common cent
!leaderboard - Type !leaderboard to see who has the most common cents
!addevent - Type !addevent *event name* mm/dd/yyyy *time* to add an event to the calendar
!events - Type !events to get a list of outstanding events in the server
!delevent - Type !delevent to delete an event from the calendar
!today - Type !today to get the today's events from the calendar (Central Time)''')

        elif message.content == '!robin':
            await message.channel.send('Hello! I am a bot created by Nick who can speak on behalf of Nick.')

#---------------- Make Commands -----------------------------

        elif message.content.startswith('!addcom'):
            for role in message.author.roles:
                if role.name == "Server Admin":
                    com_message = message.content.replace('!addcom', '').strip().split(' ', 1)
                    if com_message[0][0] != '!' or com_message[0] == None or com_message[1] == None:
                        break
                    addcom_insert = (com_message[0], com_message[1], str(message.author))
                    c.execute("INSERT INTO commands VALUES (?,?,?)", addcom_insert)
                    db.commit()
                    await message.channel.send('Made command ' + com_message[0] + ' to send ' + com_message[1])


        elif message.content.startswith('!delcom'):
            for role in message.author.roles:
                if role.name == "Server Admin":
                    com_message = message.content.replace('!delcom', '').strip()
                    delcom_delete = (com_message,)
                    c.execute("DELETE from commands WHERE command_name=?", delcom_delete)
                    db.commit()
                    await message.channel.send("Deleted " + com_message)


        elif message.content.startswith('!commands'):
            if str(message.author) == 'nickeick#9008':
                c.execute("SELECT command_name from commands")
                items = c.fetchall()
                db.commit()
                for item in items:
                    await message.channel.send(item[0].strip("('), "))

#-------------------------Play Requests------------------------------------

        elif message.content.startswith('!join'):
            role_message = message.content.replace('!join', '').strip().lower()
            if role_message == '':
                await message.channel.send('Type !join and role(s) to join a role')
                return
            for role in message.guild.roles:
                if role.name.lower() in role_message:
                    if role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy":
                        await message.channel.send('You cannot join this role: ' + role.name)
                        return
                    else:
                        await message.author.add_roles(role)
                        if role.name == 'Movie Night Gang':
                            await message.channel.send('*This is an NSFW Gang*')
                        await message.channel.send('Added ' + message.author.display_name + ' to ' + role.name)


        elif message.content.startswith('!leave'):
            role_message = message.content.replace('!leave', '').strip().lower()
            if role_message == '':
                await message.channel.send('Type !leave and role(s) to leave a role')
                return
            for role in message.guild.roles:
                if role.name.lower() in role_message:
                    if role.name == 'Server Admin' or role.name == 'Donor' or role.name == 'Bots' or role.name == 'Robin Otto' or role.name == "Groovy":
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
                #self.play_messages.append(sent)
                if time == None:
                    time = ' '
                play_sql = (message.channel.name, time, '', '', str(message.author))
                c.execute("REPLACE INTO play_requests (game, time, yes, no, requestor) VALUES (?,?,?,?,?)", play_sql)
                db.commit()
            else:
                await message.channel.send("You can only send this command in a gang chat")


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
                c.execute("SELECT yes FROM play_requests WHERE game=?", replay_select)
                yes_list = c.fetchone()
                db.commit()
                for name in yes_list[0].split():
                    user = message.guild.get_member_named(name)
                    if user == None:
                        pass
                    else:
                        await user.add_roles(message.guild.get_role(self.yes_role_id))
                        try:
                            await sent.edit(content=sent.content + '\n*' + user.nick + '*')
                        except:
                            await sent.edit(content=sent.content + '\n*' + str(user)[:-5] + '*')


        elif message.content.startswith('!reset'):
            for member in message.guild.get_role(self.yes_role_id).members:
                await member.remove_roles(message.guild.get_role(self.yes_role_id))
            for member in message.guild.get_role(self.no_role_id).members:
                await member.remove_roles(message.guild.get_role(self.no_role_id))
            await message.channel.send("Removed all YES and NO roles")


        elif message.content.startswith('!yes'):
            to_send = 'members said YES:'
            number = 0
            for member in message.guild.get_role(self.yes_role_id).members:
                number += 1
                try:
                    to_send += '\n' + member.nick
                except:
                    to_send += '\n' + str(member)[:-5]
            await message.channel.send(str(number) + ' ' + to_send)


        elif message.content.startswith('!no'):
            to_send = 'members said NO:'
            number = 0
            for member in message.guild.get_role(self.no_role_id).members:
                number += 1
                try:
                    to_send += '\n' + member.nick
                except:
                    to_send += '\n' + str(member)[:-5]
            await message.channel.send(str(number) + ' ' + to_send)

#-----------------Waitlists----------------------------------

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
                try:
                    to_send += '\n' + person.nick
                except:
                    to_send += '\n' + str(person)[:-5]
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
                try:
                    to_send += '\n' + person.nick
                except:
                    to_send += '\n' + str(person)[:-5]
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
                    gang = message.content.replace('!makegang', '').strip()
                    new_role = await message.guild.create_role(name=gang + " Gang")
                    overwrites = {message.guild.default_role: PermissionOverwrite(read_messages=False),
                                    new_role: PermissionOverwrite(read_messages=True)}
                    await message.guild.create_text_channel(name=gang + "-gang", overwrites=overwrites, category=message.guild.get_channel(579796688420732949))
                    await message.channel.send(gang + ' Gang has been made! Type "!join ' + gang + ' Gang" to join')


        elif message.content.startswith('!gangs'):
            #to_send = '''Among Us Gang\nCiv Gang\nJackbox Gang\nLeague Gang\nMinecraft Gang\nMovie Night Gang\nOverwatch Gang\nParody Gang\nTFT Gang\nWarcraft Gang'''
            to_send = 'The Gangs:'
            for role in message.guild.roles:
                if "Gang" in role.name:
                    to_send += '\n' + role.name
            await message.channel.send(to_send)


        elif message.content.startswith('!roles'):
            roles = ''
            for role in message.author.roles:
                if role.name != '@everyone':
                    roles += role.name + ', '
            await message.channel.send(roles.strip(', '))

#------------------------The Braincell-----------------------------

        elif message.content.startswith('!braincell'):
            for member in message.guild.members:
                if message.guild.get_role(771408034957623348) in member.roles:
                    try:
                        await message.channel.send(member.nick + ' is hogging the server brain cell')
                    except:
                        await message.channel.send(str(member)[:-5] + ' is hogging the server brain cell')


        elif message.content.startswith('!think'):      #common cents
            if message.guild.get_role(771408034957623348) in message.author.roles:
                if self.think_lock == False:
                    await message.channel.send("🧠 This makes cents 🪙")
                    think_select = (str(message.author),)
                    c.execute("SELECT points FROM braincell_points WHERE name=?", think_select)
                    points = c.fetchone()
                    #print(points)
                    if points == None:
                        think_replace = (str(message.author), 1)
                    else:
                        think_replace = (str(message.author), points[0]+1)
                    c.execute("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", think_replace)
                    for member in message.guild.members:        # Server Genius
                        if message.guild.get_role(779433226560864267) in member.roles:
                            await member.remove_roles(message.guild.get_role(779433226560864267))
                    c.execute("SELECT name FROM braincell_points ORDER BY points DESC")
                    genius_name = c.fetchone()
                    genius_member = message.guild.get_member_named(genius_name[0])
                    await genius_member.add_roles(message.guild.get_role(779433226560864267))
                    db.commit()
                    self.think_lock = True
                else:
                    await message.channel.send("You've already got your cent <:bonk:772161497031507968>")
            else:
                await message.channel.send("You don't have the brain cell <:bonk:772161497031507968>")


        elif message.content.startswith('!leaderboard'):
            c.execute("SELECT * FROM braincell_points ORDER BY points DESC")
            items = c.fetchall()
            db.commit()
            to_send = '🪙  **Common Cents Leaderboard:**  🪙\n'
            for item in items:
                try:
                    name = message.guild.get_member_named(item[0]).nick + ':'
                except:
                    name = str(item[0])[:-5] + ':'
                to_send += name
                i = len(name)*2
                while i < 60:
                    to_send += ' '
                    i+=1
                for cents in range(item[1]):
                    to_send += '🪙'
                to_send += '|   ' + str(item[1]) + '\n'
            await message.channel.send(to_send)


        elif message.content.startswith('!atme'):
            await message.channel.send("Ashe, Erik, Corbin, Nick, Katie, Cole, Casey, Hanray, Snowman, Sarah, Colin, Firebox, Jaxington, Kittycat7070")

#--------------------------Events Calendar-----------------------------

        elif message.content.startswith('!addevent'):
            event_message = message.content.replace('!addevent', '').strip()
            try:
                date_re = search(r'(.+) (\d\d)/(\d\d)/(\d\d\d\d) ((\d){1,2}:\d\d(am|pm))(.*)', event_message)
                if not date_re:
                    raise ValueError(event_message + ' does not have name, date, time')
                addevent_insert = (date_re.group(1).strip(), date_re.group(4), date_re.group(2), date_re.group(3), date_re.group(5), date_re.group(8).strip().lower())
                c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', addevent_insert)
                db.commit()
                await message.channel.send("You have added " + date_re.group(1).strip() +" on "+ date_re.group(2) +"/"+ date_re.group(3) +"/"+ date_re.group(4) +" at "+ date_re.group(5) + " to the Calendar")
            except:
                await message.channel.send("To make an event, type !addevent *event name* mm/dd/yyyy (H)H:MM*am/pm* *gang (optional)*")


        elif message.content.startswith('!events'):
            c.execute("SELECT * FROM calendar ORDER BY year DESC, month DESC, day DESC")
            items = c.fetchall()
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
            db.commit()


        elif message.content.startswith('!delevent'):
            event_message = message.content.replace('!delevent', '').strip()
            c.execute("SELECT * FROM calendar")
            before_num = len(c.fetchall())
            delevent_delete = (event_message,)
            c.execute("DELETE FROM calendar WHERE event_name=?", delevent_delete)
            db.commit()
            c.execute("SELECT * FROM calendar")
            after_num = len(c.fetchall())
            if before_num - after_num >= 1:
                await message.channel.send("Successfully deleted " + event_message + " event")
            else:
                await message.channel.send("No such event exists, be sure to type !delevent *event name*")


        elif message.content.startswith("!thisweek"):
            pass


        elif message.content.startswith("!today"):
            await message.channel.send("Today's events are:")
            today = date.today()
            month = today.strftime("%m")
            day = today.strftime("%d")
            year = today.strftime("%Y")
            today_select = (month, day, year)
            c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", today_select)
            items = c.fetchall()
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
            c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", tomorrow_select)
            items = c.fetchall()
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
            c.execute("SELECT event_name, time, gang FROM calendar")
            items = c.fetchall()
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
                c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", calendar_select)
                get_items = c.fetchall()
                get_items.append(dailys)
                items = []
                for i in get_items:         #removes duplicates
                    append_bool = True
                    for item in items:
                        if i[0] == item[0] and i[1] == item[1] and i[2] == item[2]:
                            append_bool = False
                    if append_bool == True:
                        items.append(i)
                for item in items:
                    to_send += item[0] + ' at ' + item[1]
                    if item[2]:
                        to_send += ' (' + item[2] + ')'
                    to_send += '\n'
                counter += 1
                to_send += '\n'
            sent = await message.channel.send(to_send)
            await sent.add_reaction("⬅️")
            await sent.add_reaction("➡️")


#--------------------------Misc---------------------------------------

        elif message.content.startswith('!icon'):
            await message.channel.send("", file=File("dojo.gif"))


        elif message.content.startswith('!gibby'):
            await message.channel.send("<:gibby:760384610696953887>")


        elif message.content.startswith('!longgibby'):
            await message.channel.send("", file=File("longgibby.jpg"))


        elif message.content.startswith('!widegibby'):
            await message.channel.send("", file=File("widegibby.jpg"))


        elif message.content.startswith('!test'):
            await message.channel.send("Test Successful")


        elif message.content.startswith('!'):
            c.execute("SELECT * FROM commands")
            commands = c.fetchall()
            for command in commands:
                if message.content == command[0]:
                    await message.channel.send(command[1])
            db.commit()


    async def on_reaction_add(self, reaction, user):
        #for !play requests
        if reaction.message.author == self.user and self.play_text in reaction.message.content and user != self.user:
            if reaction.emoji == "✅":
                await user.add_roles(reaction.message.guild.get_role(self.yes_role_id))
                try:
                    await reaction.message.edit(content=reaction.message.content + '\n*' + user.nick + '*')
                except:
                    await reaction.message.edit(content=reaction.message.content + '\n*' + str(user)[:-5] + '*')
                checkmark_select = (reaction.message.channel.name,)
                c.execute("SELECT yes FROM play_requests WHERE game=?", checkmark_select)
                yes_list = c.fetchone()
                yes_list = yes_list[0] + ' ' + str(user)
                checkmark_update = (yes_list, reaction.message.channel.name)
                c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", checkmark_update)
                db.commit()
            if reaction.emoji == "❌":
                await user.add_roles(reaction.message.guild.get_role(self.no_role_id))
                xmark_select = (reaction.message.channel.name,)
                c.execute("SELECT no FROM play_requests WHERE game=?", xmark_select)
                no_list = c.fetchone()
                no_list = no_list[0] + ' ' + str(user)
                xmark_update = (no_list, reaction.message.channel.name)
                c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", xmark_update)
                db.commit()
        #for !jeopardy games
        if reaction.message.content == "buzz" and self.jeopardy == True and self.jeopardy_host == user.name:
            if reaction.emoji == "✅":
                await reaction.message.channel.send(reaction.message.author.nick + " got it correct")
                self.answered = False
            if reaction.emoji == "❌":
                await reaction.message.channel.send(reaction.message.author.nick + " got it incorrect")
                self.answered = False
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
                c.execute("SELECT event_name, time, gang FROM calendar")
                items = c.fetchall()
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
                    c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", calendar_select)
                    get_items = c.fetchall()
                    get_items.append(dailys)
                    items = []
                    for i in get_items:         #removes duplicates
                        append_bool = True
                        for item in items:
                            if i[0] == item[0] and i[1] == item[1] and i[2] == item[2]:
                                append_bool = False
                        if append_bool == True:
                            items.append(i)
                    for item in items:
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
                c.execute("SELECT event_name, time, gang FROM calendar")
                items = c.fetchall()
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
                    c.execute("SELECT event_name, time, gang FROM calendar WHERE month = ? AND day = ? AND year = ?", calendar_select)
                    get_items = c.fetchall()
                    get_items.append(dailys)
                    items = []
                    for i in get_items:         #removes duplicates
                        append_bool = True
                        for item in items:
                            if i[0] == item[0] and i[1] == item[1] and i[2] == item[2]:
                                append_bool = False
                        if append_bool == True:
                            items.append(i)
                    for item in items:
                        to_send += item[0] + ' at ' + item[1]
                        if item[2]:
                            to_send += ' (' + item[2] + ')'
                        to_send += '\n'
                    counter += 1
                    to_send += '\n'
                await reaction.message.edit(content=to_send)
                #print("next week")


    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) == "☑️" and payload.message_id == 759611108541071380:
            await payload.member.remove_roles(payload.member.guild.get_role(self.initiate_role_id))


    async def on_reaction_remove(self, reaction, user):
        if reaction.message.author == self.user and self.play_text in reaction.message.content and user != self.user:
            if reaction.emoji == "✅":
                await user.remove_roles(reaction.message.guild.get_role(self.yes_role_id))
                try:
                    reaction_message = reaction.message.content.replace('\n*'+user.nick+'*', '').strip()
                except:
                    reaction_message = reaction.message.content.replace('\n*'+str(user)[:-5]+'*', '').strip()
                await reaction.message.edit(content=reaction_message)
                checkmark_select = (reaction.message.channel.name,)
                c.execute("SELECT yes FROM play_requests WHERE game=?", checkmark_select)
                yes_list = c.fetchone()
                yes_list = yes_list[0].replace(str(user), '').strip()
                checkmark_update = (yes_list, reaction.message.channel.name)
                c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", checkmark_update)
                db.commit()
            if reaction.emoji == "❌":
                await user.remove_roles(reaction.message.guild.get_role(self.no_role_id))
                xmark_select = (reaction.message.channel.name,)
                c.execute("SELECT no FROM play_requests WHERE game=?", xmark_select)
                no_list = c.fetchone()
                no_list = no_list[0].replace(str(user), '').strip()
                xmark_update = (no_list, reaction.message.channel.name)
                c.execute("UPDATE play_requests SET yes = ? WHERE game = ?", xmark_update)
                db.commit()


    async def on_member_join(self, member):
        try:
            await member.add_roles(member.guild.get_role(self.initiate_role_id))
        except:
            pass


    async def post(self, channel_name, text):
        channels = {"general": 578065102310342679, #Actually "the-main-dojo"
                    "memes": 600497105399709725,
                    "announcements": 578065404031664137,
                    "suggestions": 615001686934683649,
                    "think-tank": 776603967475810304,
                    "admins": 578067589188681748,
                    "donors": 578067658818453542,
                    "bot-test": 582060071052115978,
                    "music-requests": 582064740973543435}
        channel = self.get_channel(channels[channel_name]) # channel ID goes here
        await channel.send(text)

    @loop(seconds = 5)
    async def robin_STT(self):
        if not self.queue.empty():
            to_say = self.queue.get()
            await self.post(to_say[0], to_say[1])
            print("You said " + to_say[0] + " to " + to_say[1])


    @loop(minutes = 20)
    async def braincell_swap(self):
        members = self.get_channel(578065102310342679).members      #get the-main-dojo members
        for member in members:
            if self.get_guild(578065102310342677).get_role(746572040131051563) in member.roles: #bots
                members.remove(member)
        braincell_role = self.get_guild(578065102310342677).get_role(771408034957623348)
        for member in members:
            if braincell_role in member.roles:
                await member.remove_roles(braincell_role)
        size = len(members)
        new_user = randint(1,size)
        i = 0
        for member in members:
            i+=1
            if i == new_user:
                await member.add_roles(braincell_role)
        self.think_lock = False


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
        c.execute("SELECT event_name, gang FROM calendar WHERE month = ? AND day = ? AND year = ? AND time = ?", check_datetime_select)
        events = c.fetchall()
        for event in events:
            #await self.get_channel(582060071052115978).send(event[0] + " is starting right now!")
            if event[1]:
                mention = ''
                for role in self.get_guild(578065102310342677).roles:
                    if role.name.lower() == event[1].lower():   #find gang role from gang field
                        mention = role.mention
                        channel_name = role.name.lower()
                        for letter in role.name.lower():
                            if letter == ' ':
                                channel_name = channel_name.replace(' ', '-')
                        for channel in self.get_guild(578065102310342677).text_channels:    #find gang channel from gang role
                            if channel.name == channel_name:
                                if 'daily' in event[0].lower():
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    daily_select = (event[0],)
                                    c.execute('SELECT * FROM calendar WHERE event_name = ?', daily_select)
                                    daily_event = c.fetchone()
                                    c.execute('DELETE FROM calendar WHERE event_name = ?', daily_select)
                                    daily_tomorrow = date.today() + timedelta(days=1)
                                    daily_insert = (daily_event[0], daily_tomorrow.year, daily_tomorrow.month, daily_tomorrow.day, daily_event[4], daily_event[5])
                                    c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', daily_insert)
                                elif 'weekly' in event[0].lower():
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    weekly_select = (event[0],)
                                    c.execute('SELECT * FROM calendar WHERE event_name = ?', weekly_select)
                                    weekly_event = c.fetchone()
                                    c.execute('DELETE FROM calendar WHERE event_name = ?', weekly_select)
                                    next_week = date.today() + timedelta(weeks=1)
                                    weekly_insert = (weekly_event[0], next_week.year, next_week.month, next_week.day, weekly_event[4], weekly_event[5])
                                    c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', weekly_insert)
                                elif 'monthly' in event[0].lower():
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    monthly_select = (event[0],)
                                    c.execute('SELECT * FROM calendar WHERE event_name = ?', monthly_select)
                                    monthly_event = c.fetchone()
                                    c.execute('DELETE FROM calendar WHERE event_name = ?', monthly_select)
                                    if date.today().month == 2:
                                        extra_days = 0
                                    elif date.today().month == 4 or 6 or 9 or 11:
                                        extra_days = 2
                                    else:
                                        extra_days = 3
                                    next_month = date.today() + timedelta(weeks=4, days=extra_days)
                                    monthly_insert = (monthly_event[0], next_month.year, next_month.month, next_month.day, monthly_event[4], monthly_event[5])
                                    c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', monthly_insert)
                                else:
                                    await channel.send(mention + ' ' + event[0] + " is starting right now!")
                                    c.execute("DELETE FROM calendar WHERE month = ? AND day = ? AND year = ? AND time = ?", check_datetime_select)
            else:
                #await self.get_channel(582060071052115978).send(event[0] + " is starting right now!")
                if 'daily' in event[0].lower():
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    daily_select = (event[0],)
                    c.execute('SELECT * FROM calendar WHERE event_name = ?', daily_select)
                    daily_event = c.fetchone()
                    c.execute('DELETE FROM calendar WHERE event_name = ?', daily_select)
                    daily_tomorrow = date.today() + timedelta(days=1)
                    daily_insert = (daily_event[0], daily_tomorrow.year, daily_tomorrow.month, daily_tomorrow.day, daily_event[4], daily_event[5])
                    c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', daily_insert)
                elif 'weekly' in event[0].lower():
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    weekly_select = (event[0],)
                    c.execute('SELECT * FROM calendar WHERE event_name = ?', weekly_select)
                    weekly_event = c.fetchone()
                    c.execute('DELETE FROM calendar WHERE event_name = ?', weekly_select)
                    next_week = date.today() + timedelta(weeks=1)
                    weekly_insert = (weekly_event[0], next_week.year, next_week.month, next_week.day, weekly_event[4], weekly_event[5])
                    c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', weekly_insert)
                elif 'monthly' in event[0].lower():
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    monthly_select = (event[0],)
                    c.execute('SELECT * FROM calendar WHERE event_name = ?', monthly_select)
                    monthly_event = c.fetchone()
                    c.execute('DELETE FROM calendar WHERE event_name = ?', monthly_select)
                    if date.today().month == 2:
                        extra_days = 0
                    elif date.today().month == 4 or 6 or 9 or 11:
                        extra_days = 2
                    else:
                        extra_days = 3
                    next_month = date.today() + timedelta(weeks=4, days=extra_days)
                    monthly_insert = (monthly_event[0], next_month.year, next_month.month, next_month.day, monthly_event[4], monthly_event[5])
                    c.execute('INSERT INTO calendar VALUES (?,?,?,?,?,?)', monthly_insert)
                else:
                    await self.get_channel(578065102310342679).send(event[0] + " is starting right now!")
                    c.execute("DELETE FROM calendar WHERE month = ? AND day = ? AND year = ? AND time = ?", check_datetime_select)



if __name__ == '__main__':
    client = MyClient(MyQueue)
    client.run('NjYyODM5NzgxMDkyNDkxMjg0.XhAB3A.fdTozwZH2YFMDy9LY6DzQ5y6YUY')
    db.close()
