#!/usr/bin/python3

from socket import SHUT_RDWR
from client import start, get_msg, send, send_file, close_conn
from tkinter import Tk, Frame, Button, Canvas, Entry, Label, StringVar, BOTH
from tkinter.ttk import Scrollbar
from threading import Thread
from time import time
#from win32api import SetConsoleCtrlHandler

HEIGHT = 700
WIDTH = 800
DISCONNECT_MESSAGE = "#DISCONNECT#"
CONNECT_UI_MESSAGE = "#UICONNECTED#"
RESTART_MESSAGE = "#RESTART#"
CTRL_C_EVENT = 0
CTRL_BREAK_EVENT = 1
CTRL_CLOSE_EVENT = 2
CTRL_LOGOFF_EVENT = 5
CTRL_SHUTDOWN_EVENT = 6

class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        print("[STARTING GUI]...")

        self.conn, self.addr = start()
        send(self.conn, "Client:UI")
        self.master = master
        self.canvas = Canvas(master, height=HEIGHT, width=WIDTH)
        self.canvas.pack()
        #top
        self.top_frame = Frame(master, bg='blue')
        self.top_frame.place(relx=0.3, rely=0.1, relwidth=0.6, relheight=0.6, anchor='n')
        #scroll stuff
        self.top_canvas = Canvas(self.top_frame, bg='blue')
        self.top_canvas.pack(side='left', fill=BOTH, expand=1)
        self.top_scroll = Scrollbar(self.top_frame, orient='vertical', command=self.top_canvas.yview)
        self.top_scroll.pack(side='right', fill='y')
        self.top_canvas.configure(yscrollcommand=self.top_scroll.set)
        self.top_canvas.bind('<Configure>', lambda e: self.top_canvas.configure(scrollregion = self.top_canvas.bbox("all")))
        self.scroll_frame = Frame(self.top_canvas, bg='blue')
        self.top_canvas.create_window((0,0), window=self.scroll_frame, anchor='nw')
        #right
        self.right_frame = Frame(master, bg='green')
        self.right_frame.place(relx=0.8, rely=0.1, relwidth=0.4, relheight=0.6, anchor='n')
        #bottom
        self.bottom_frame = Frame(self.canvas, bg='red', bd=5)
        self.bottom_frame.place(relx=0.5, rely=0.8, relwidth=0.75, relheight=0.2, anchor='n')
        self.create_widgets()

    def create_widgets(self):
        #graph button
        self.graph = Button(self.right_frame, text="Make Graph", command=self.send)
        self.graph.pack(side='top')
        # #start button
        # self.start = Button(self.bottom_frame, text="Start ROBIN", command=self.send)
        # self.start.pack(side="top")
        #ping status
        thread = Thread(target=self.check_ping)
        thread.start()
        send(self.conn, "Send to:discord " + CONNECT_UI_MESSAGE)
        #restart robin
        self.restart = Button(self.bottom_frame, text="Restart ROBIN", command=self.restart)
        self.restart.pack(side="top")
        #file send to server
        self.file_entry = Entry(self.bottom_frame)
        self.file_entry.place(relx = 0.6, rely = 0.5, width = 200, height=25)
        self.file_button = Button(self.bottom_frame, text="Send file to Server", command=self.send_file_f(self.conn, self.file_entry))
        self.file_button.place(relx = 0.6, rely = 0.7, width = 200, height=25)
        #close ui
        self.quit = Button(self.bottom_frame, text="QUIT", fg="red",
                              command=self.close)
        self.quit.pack(side="bottom")
        #close all
        self.all = Button(self.bottom_frame, text="Close All Connections", fg="red",
                              command=self.close_all)
        self.all.pack(side="top")

    def update_channels(self, channel_list):
        channels = channel_list.split(',')
        entries = []
        i = 0
        for channel in channels:
            i+=1
            entries.append(Entry(self.scroll_frame))
            entries[-1].grid(row=i, column=0, pady=10, padx=10)
        functions = []
        e = 0
        for channel in channels:
            func = self.make_f(entries[e], channel)
            functions.append(func)
            e+=1
        i = 0
        j = 0
        for channel in channels:
            i+=1
            self.send_to = Button(self.scroll_frame, text="Send to "+channel, command=functions[j])
            self.send_to.grid(row=i, column=1, padx=10, pady=10)
            j+=1


    def send(self, entry, client_name):
        msg = entry.get()
        entry.delete(0, 'end')
        entry.insert(0, "")
        send(self.conn, "Send to:" + client_name + " " + msg)
        print("Sent: ", msg)

    def make_f(self, entry, channel):
        def send_channel():
            self.send(entry, "discord "+channel)
        return send_channel

    def send_file_f(self, conn, entry):
        def function():
            filename = entry.get()
            send_file(conn, filename)
        return function

    def check_ping(self):
        height = 0
        clients_time = {}
        clients_label = {}
        while True:
            msg = get_msg()
            if msg:
                if "#PINGED#" in msg:
                    client_ping = msg.replace('#PINGED#', '').strip()
                    if client_ping in clients_time.keys():
                        clients_label[client_ping].config(text=client_ping+" connected", bg='Green')
                        clients_time[client_ping] = time()
                    else:
                        color_var = StringVar()
                        l = Label(self.bottom_frame, text=client_ping+" connected", fg='White', bg='Green')
                        l.place(relx=0.1, y=10+height, anchor='n')
                        height+=20
                        clients_label[client_ping] = l
                        clients_time[client_ping] = time()
                elif msg.startswith('channel_list:'):
                    channel_list = msg.replace('channel_list:', '').strip()
                    self.update_channels(channel_list)
                elif msg == DISCONNECT_MESSAGE:
                    break
            for client in clients_time.keys():
                if time() - clients_time[client] > 10:
                    clients_label[client].config(text=client+" disconnected", bg='Red')
        print("[DISCONNECTED "+ str(self.addr) +"]")
        self.master.destroy()

    def close(self):
        close_conn(self.conn)
        self.master.destroy()

    def close_all(self):
        send(self.conn, "#DISCONNECTALL#")

    def restart(self):
        send(self.conn, RESTART_MESSAGE)



root = Tk()
app = Application(master=root)
app.mainloop()
