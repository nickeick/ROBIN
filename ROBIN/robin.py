from speech_recognition import Recognizer, Microphone, UnknownValueError, WaitTimeoutError
from time import localtime, strftime, sleep
from playsound import playsound
from gtts import gTTS
from queue import Queue
from threading import Thread
from threadedGUI import ThreadedClient
from tkinter import Tk
from datetime import datetime
from discord_bot import MyClient
from pandas_datareader import get_data_yahoo
#import asyncio
#import GUI
#from win32com.client import Dispatch

TOKEN = 'NjYyODM5NzgxMDkyNDkxMjg0.XhAB3A.fdTozwZH2YFMDy9LY6DzQ5y6YUY'
gui_queue = Queue()
discord_queue = Queue()

class ROBIN:
    def __init__(self):
        self.numbers = [
            'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
            'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
            'twenty', 'twenty-one', 'twenty-two', 'twenty-three', 'twenty-four', 'twenty-five', 'twenty-six', 'twenty-seven', 'twenty-eight', 'twenty-nine',
            'thirty', 'thirty-one', 'thirty-two', 'thirty-three', 'thirty-four', 'thirty-five', 'thirty-six', 'thirty-seven', 'thirty-eight', 'thirty-nine',
            'fourty', 'fourty-one', 'fourty-two', 'fourty-three', 'fourty-four', 'fourty-five', 'fourty-six', 'fourty-seven', 'fourty-eight', 'fourty-nine',
            'fifty', 'fifty-one', 'fifty-two', 'fifty-three', 'fifty-four', 'fifty-five', 'fifty-six', 'fifty-seven', 'fifty-eight', 'fifty-nine'
        ]
        self.discord_message = ['','']
        # functions below -----------
        self.function_tree = Tree("Robin", '''
self.speak("Hello Nick")
self.listen("Tell Robin something: ", "goodbye")
                ''')
        time_tree = Tree("time",'''
        self.get_time()
        self.speak(self.time)
                        ''')
        self.function_tree.add_child(time_tree)
        discord_tree = Tree("Discord", '''
self.discord()
        ''')
        self.keys = ["Robin",
                    "time",
                    "Discord"]
        self.funcs = ['''
self.speak("Hello Nick")
self.listen("Tell Robin something: ", "goodbye")
                ''',
                '''
self.get_time()
self.speak(self.time)
                ''',
                '''
self.discord()
                ''']
        self.listen()

    def listen(self, prompt = "Say something: ", waitfor = "exit", defaults = True, functions = None):
        text = ""
        if defaults:
            keys = self.keys
            funcs = self.funcs
        else:
            keys = []
            funcs = []
        try:
            for key in functions:
                keys.append(key)
                funcs.append(functions[key])
        except:
            pass
        while text != waitfor:      #loop
            text = self.hear(prompt)
            if not gui_queue.empty():
                text = gui_queue.get()      #queue
            if text != "Couldn't understand you":
                try:
                    print('You said: ' + text)
                    i = 0
                    for key in keys:
                        if key in text + " ":
                            exec(funcs[i])
                            return
                        i+=1
                except TypeError:
                    pass

    def hear(self, prompt = "Say something: "):
        r = Recognizer()
        with Microphone() as source:
            r.adjust_for_ambient_noise(source, duration = 1)
            print(prompt)
            try:
                audio = r.listen(source, timeout = 2)
                text = r.recognize_google(audio)
                return text
            except UnknownValueError:
                return "Couldn't understand you"
            except WaitTimeoutError:
                pass

    def speak(self, string, lang = 'en'):
        tts = gTTS(text=string, lang=lang)
        filename = string + ".mp3"
        f = open("audio/saved.txt","a+")
        saved_audio = f.read()
        if not string in saved_audio:
            tts.save("audio/" + filename)
            f.write(string + "\n")
        playsound("audio/" + filename)
        print("Robin said: " + string)

    def get_time(self):
        t = localtime()
        current_time = strftime("%I:%M", t)
        self.time = self.time_to_string(current_time)

    def time_to_string(self, time):
        string = ''
        part = 1
        for char in time:
            if char == ':':
                string = ''
                part += 1
            else:
                string += char
                if part == 1:
                    self.hours = self.numbers[int(string)]
                elif part == 2:
                    self.minutes = self.numbers[int(string)]
        return self.hours + ' ' + self.minutes

    def discord(self):
        dict = {"nick samas dojo": "self.discord_message[0] = 'nick-samas-dojo'",
                "memes": "self.discord_message[0] = 'memes'",
                "announcements": "self.discord_message[0] = 'announcements'",
                "suggestions": "self.discord_message[0] = 'suggestions'",
                "Think Tank": "self.discord_message[0] = 'think-tank'",
                "admins": "self.discord_message[0] = 'admins'",
                "donors": "self.discord_message[0] = 'donors'",
                "bot test": "self.discord_message[0] = 'bot-test'",
                "music requests": "self.discord_message[0] = 'music-requests'",
                "General": "self.discord_message[0] = 'general'"}
        #self.speak("In what channel?") #add audio clips
        self.listen("In what channel?", "Understood", defaults = False, functions = dict)
        #self.speak("What message?") #add audio clips
        self.listen("What message?", "Message sent", defaults = False, functions = {"": "self.discord_message[1] = text"})
        discord_queue.put(self.discord_message)
        self.listen()

class Tree:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def find_child(self, child):
        try:
            return self.children.index(child)
        except:
            return None

    def get_key(self):
        return self.key

    def get_value(self):
        return self.value

    def is_leaf(self):
        if self.children == []:
            return True
        else:
            return False


if __name__ == '__main__':
    root = Tk()
    bot = MyClient(discord_queue)
    client = ThreadedClient(root, gui_queue, ROBIN)
    #bot.run(TOKEN)
    root.mainloop()
    bot.run(TOKEN)
