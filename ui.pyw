#!/usr/bin/python3

from socket import SHUT_RDWR
from client import start, get_msg, send, send_file, close_conn
from tkinter import Tk, Frame, Button, Canvas, Entry, Label, StringVar
from threading import Thread
from time import time

HEIGHT = 700
WIDTH = 800
DISCONNECT_MESSAGE = "#DISCONNECT#"

class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        print("[STARTING GUI]...")

        self.conn, self.addr = start()
        send(self.conn, "Client:UI")

        self.master = master
        self.canvas = Canvas(master, height=HEIGHT, width=WIDTH)
        self.canvas.pack()
        self.top_frame = Frame(self.canvas, bg='blue', bd=5)
        self.top_frame.place(relx=0.5, rely=0.1, relwidth=0.75, relheight=0.6, anchor='n')
        self.bottom_frame = Frame(self.canvas, bg='red', bd=5)
        self.bottom_frame.place(relx=0.5, rely=0.8, relwidth=0.75, relheight=0.2, anchor='n')
        self.create_widgets()

    def create_widgets(self):
        self.start = Button(self.top_frame, text="Start ROBIN", command=self.send)
        self.start.pack(side="top")
        #ping status
        thread = Thread(target=self.check_ping)
        thread.start()
        #discord input
        channels = ["general", "memes", "announcements", "suggestions", "think-tank", "bot-test"]
        entries = []
        i = 0
        for channel in channels:
            i+=60
            entries.append(Entry(self.top_frame))
            entries[-1].place(x = 20, y = i, width=200, height=25)
        functions = []
        e = 0
        for channel in channels:
            func = self.make_f(entries[e], channel)
            functions.append(func)
            e+=1
        i = 0
        j = 0
        for channel in channels:
            i+=60
            self.send_to = Button(self.top_frame, text="Send to "+channel, command=functions[j])
            self.send_to.place(x = 20, y = i+25, width=200, height=25)
            j+=1
        #file send to server
        self.file_entry = Entry(self.top_frame)
        self.file_entry.place(relx = 0.6, rely = 0.85, width = 200, height=25)
        self.file_button = Button(self.top_frame, text="Send file to Server", command=self.send_file_f(self.conn, self.file_entry))
        self.file_button.place(relx = 0.6, rely = 0.9, width = 200, height=25)
        #close ui
        self.quit = Button(self.bottom_frame, text="QUIT", fg="red",
                              command=self.close)
        self.quit.pack(side="bottom")
        #close all
        self.all = Button(self.bottom_frame, text="Close All Connections", fg="red",
                              command=self.close_all)
        self.all.pack(side="top")

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
                        l = Label(self.top_frame, text=client_ping+" connected", fg='White', bg='Green')
                        l.place(relx=0.9, y=10+height, anchor='n')
                        height+=20
                        clients_label[client_ping] = l
                        clients_time[client_ping] = time()
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
        # while True:
        #     msg = get_msg()
        #     if msg:
        #         if msg == DISCONNECT_MESSAGE:
        #             break
        # print("[DISCONNECTED "+ str(self.addr) +"]")
        # self.master.destroy()
        # self.conn.shutdown(SHUT_RDWR)
        # self.conn.close()


root = Tk()
app = Application(master=root)
app.mainloop()
