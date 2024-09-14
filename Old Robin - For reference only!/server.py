#!/usr/bin/python3

from socket import gethostbyname, gethostname, socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from threading import Thread, activeCount
from time import sleep, time
from queue import Queue
from os import popen, kill, system
from subprocess import call
from signal import SIGKILL

HEADER = 256
HOST = gethostbyname(gethostname())  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
ADDR = (HOST, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "#DISCONNECT#"
PING_MESSAGE = "#PING#"
RESTART_MESSAGE = "#RESTART#"
CONFIRM_MESSAGE = "Message received:"
FAIL_MESSAGE = "Message failed:"

server = socket(AF_INET, SOCK_STREAM)
server.bind(ADDR)

#CONNECTIONS = {}
DEFAULTS = 0
PINGED = False

class Node:
    client_name = None
    connection = None
    prev = None
    next = None

    def get_name(self):
        return self.client_name

    def set_name(self, name):
        self.client_name = name

    def get_conn(self):
        return self.connection

    def set_conn(self, conn):
        self.connection = conn

class linkedlist:
    start = None

    def __find__(self, name):
        next_node = self.start
        while next_node != None:
            if next_node.get_name() == name:
                return next_node
            else:
                next_node = next_node.next
        return None

    def first(self):
        return self.start

    def add_conn(self, name, conn):
        node = Node()
        node.set_name(name)
        node.set_conn(conn)
        if self.start == None:
            self.start = node
        else:
            next_node = self.start
            while next_node.next != None:
                next_node = next_node.next
            node.prev = next_node
            node.next = None
            next_node.next = node

    def remove_conn(self, name):
        node = self.__find__(name)
        if node:
            if node.prev == None:
                self.start = node.next
            else:
                node.prev.next = node.next
            return node.get_conn()

    def find_conn_by_name(self, name):
        node = self.__find__(name)
        if node:
            return node.get_conn()
        else:
            return None

    def find_name_by_conn(self, conn):
        if self.start == None:
            return None
        else:
            next_node = self.start
            while next_node != None:
                if next_node.get_conn() == conn:
                    return next_node.get_name()
                else:
                    next_node = next_node.next
            return None

    def get_names(self):
        next_node = self.start
        names = []
        while next_node != None:
            names.append(next_node.get_name())
            next_node = next_node.next
        return names

CONNECTIONS = linkedlist()

def send(conn, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    test = int(send_length)
    try:
        conn.send(send_length)
        conn.send(message)
    except:
        pass

def processes():
    try:
        pids = []
        for line in popen("ps ax | grep python | grep -v grep"):
            fields = line.split()                       #find and don't add server.py
            for field in fields:
                print(field)
            pid = fields[0]
            pids.append(pid)
            #os.kill(int(pid), SIGKILL)
        print("Process Successfully terminated")
        return pids
    except:
        print("Error in termination")


def handle_client(conn, addr, ping_queue):
    print("[NEW CONNECTION] " + str(addr) + " connected.")

    file_write = None
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            try:
                msg_length = int(msg_length)
                bytes = conn.recv(msg_length)
                try:
                    msg = bytes.decode(FORMAT)
                except:
                    pass
            except:
                msg = msg_length


            if msg == PING_MESSAGE:
                ping_queue.put(True)

            elif msg == "#DISCONNECTALL#":
                while CONNECTIONS.get_names() != []:
                    key = CONNECTIONS.get_names()[0]
                    connection = CONNECTIONS.remove_conn(key)
                    send(connection, DISCONNECT_MESSAGE)
                print("[DISCONNECTING]... ALL CONNECTIONS")
                break

            elif msg == DISCONNECT_MESSAGE:
                #while CONNECTIONS.get_names() != []:
                name = CONNECTIONS.find_name_by_conn(conn)
                if name:
                    CONNECTIONS.remove_conn(name)
                    print("[DISCONNECT] " + name + " disconnected")
                break

            #elif msg.startswith("Disconnect:"):
                #client_name = msg.replace("Disconnect:", '')
                #if client_name:
                    #connection = CONNECTIONS.remove_conn(client_name)
                    #send(connection, DISCONNECT_MESSAGE)


            elif msg == RESTART_MESSAGE:
                while CONNECTIONS.get_names() != []:
                    key = CONNECTIONS.get_names()[0]
                    connection = CONNECTIONS.remove_conn(key)
                    send(connection, DISCONNECT_MESSAGE)
                print("[DISCONNECTING]... ALL CONNECTIONS")
                pids = processes()
                while pids != []:
                    pid = pids.pop(-1)
                    kill(int(pid), SIGKILL)
                system("systemctl reboot -i")

            elif msg.startswith("Client:"):                   #send "Client:client_name"
                client_name = msg.replace("Client:", '')
                if client_name:
                    if client_name == "default":
                        global DEFAULTS
                        DEFAULTS += 1
                        client_name += str(DEFAULTS)
                    CONNECTIONS.add_conn(client_name, conn)
                    print("[" + client_name + " CONNECTED]")

            elif msg.startswith("Send to:"):                  #send "Send to:client_name message"
                sendto_message = msg.replace("Send to:", '')
                if sendto_message:
                    client_name = sendto_message.split(' ')[0]
                    to_send = sendto_message.replace(client_name, '')[1:]
                    send(CONNECTIONS.find_conn_by_name(client_name), to_send)

            elif msg.startswith("file:"):
                if file_write == None:
                    file_write = msg.replace("file:", '')
                    f = open(file_write, "wb")
                    start = time()
                else:
                    send(conn, "File send in progress")

            elif file_write != None:
                end = time()
                if end-start > 1:
                    file_write = None
                    f.close()
                else:
                    f.write(bytes)
                    start = time()

            send(conn, CONFIRM_MESSAGE + msg)
    conn.shutdown(SHUT_RDWR)
    conn.close()
    return

def ping_all(queue):
    while True:
        sleep(5)
        #conn_keys = CONNECTIONS.keys()
        next_node = CONNECTIONS.first()
        while next_node != None:
        #for key in conn_keys:
        #try:
            start = time()
            #send(CONNECTIONS[key], PING_MESSAGE)
            send(next_node.get_conn(), PING_MESSAGE)
            while queue.empty():               #wait to receive ping from client
                sleep(0.1)
            end = time()
            while not queue.empty():           #empty the queue
                queue.get()
            if 'UI' in CONNECTIONS.get_names():
                send(CONNECTIONS.find_conn_by_name('UI'), "#PINGED# " + str(next_node.get_name()))
            print("[PINGED] by " + next_node.get_name() + " in " + str(end-start) + " seconds")
        #except:
            #CONNECTIONS.remove_conn(next_node.get_name())
            next_node = next_node.next


def start():
    server.listen()
    print("[LISTENING] Server is listening on " + str(HOST))
    ping_queue = Queue()
    pings = Thread(target=ping_all, args=(ping_queue,))
    pings.start()
    while True:
        conn, addr = server.accept()
        thread = Thread(target=handle_client, args=(conn, addr, ping_queue))
        thread.start()
        print("[ACTIVE CONNECTIONS] " + str(activeCount()-1))


print("[STARTING] Server is starting...")
start()
exit()
