#!/usr/bin/python3

from socket import gethostbyname, gethostname, socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from threading import Thread, activeCount
from time import sleep, time
from queue import Queue

HEADER = 256
HOST = gethostbyname(gethostname())  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
ADDR = (HOST, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "#DISCONNECT#"
PING_MESSAGE = "#PING#"
CONFIRM_MESSAGE = "Message received:"
FAIL_MESSAGE = "Message failed:"

server = socket(AF_INET, SOCK_STREAM)
server.bind(ADDR)

CONNECTIONS = {}
DEFAULTS = 0
PINGED = False

def send(conn, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    test = int(send_length)
    conn.send(send_length)
    conn.send(message)

def handle_client(conn, addr, ping_queue):
    print("[NEW CONNECTION] " + str(addr) + " connected.")

    file_write = None
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            bytes = conn.recv(msg_length)
            try:
                msg = bytes.decode(FORMAT)
            except:
                pass
            #print("[" + str(addr) + "]: " + msg)

            if msg == PING_MESSAGE:
                ping_queue.put(True)

            elif msg == "#DISCONNECTALL#":
                while CONNECTIONS.keys() != []:
                    key = list(CONNECTIONS.keys())[0]
                    connection = CONNECTIONS.pop(key)
                    send(connection, DISCONNECT_MESSAGE)
                print("[DISCONNECTING]... ALL CONNECTIONS")
                break

            elif msg == DISCONNECT_MESSAGE:
                while CONNECTIONS.keys() != []:
                    key = list(CONNECTIONS.keys())[0]
                    connection = CONNECTIONS.pop(key)
                    if connection == conn:
                        print("[DISCONNECT] " + key + " disconnected")
                        break
                    else:
                        CONNECTIONS[key] = connection
                break

            elif msg.startswith("Client:"):                   #send "Client:client_name"
                client_name = msg.replace("Client:", '')
                if client_name:
                    if client_name == "default":
                        global DEFAULTS
                        DEFAULTS += 1
                        client_name += str(DEFAULTS)
                    CONNECTIONS[client_name] = conn
                    print("[" + client_name + " CONNECTED]")

            elif msg.startswith("Send to:"):                  #send "Send to:client_name message"
                sendto_message = msg.replace("Send to:", '')
                if sendto_message:
                    client_name = sendto_message.split(' ')[0]
                    to_send = sendto_message.replace(client_name, '')[1:]
                    send(CONNECTIONS[client_name], to_send)

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
        conn_keys = CONNECTIONS.keys()
        for key in conn_keys:
            start = time()
            send(CONNECTIONS[key], PING_MESSAGE)
            while queue.empty():               #wait to receive ping from client
                sleep(0.1)
            end = time()
            while not queue.empty():           #empty the queue
                queue.get()
            if 'UI' in CONNECTIONS.keys():
                send(CONNECTIONS['UI'], "#PINGED# " + str(key))
            print("[PINGED] by " + key + " in " + str(end-start) + " seconds")


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
