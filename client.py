#!/usr/bin/python3

from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from threading import Thread
from os.path import getsize
from time import sleep

HEADER = 256
HOST = "10.0.0.30"  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
ADDR = (HOST, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "#DISCONNECT#"
PING_MESSAGE = "#PING#"
CONFIRM_MESSAGE = "Message received:"
FAIL_MESSAGE = "Message failed:"
BUFFER_SIZE = 2048

msg_queue = []
send_queue = []

def send(conn, msg):
    send_queue.append(msg)
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)

def send_file(conn, filename):
    send(conn, "file:"+filename)
    filesize = getsize(filename)
    with open(filename, "rb") as f:
        while True:
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                break
            send_queue.append(bytes_read)
            bytes_length = len(bytes_read)
            send_length = str(bytes_length).encode(FORMAT)
            send_length += b' ' * (HEADER - len(send_length))
            conn.sendall(send_length)
            conn.sendall(bytes_read)
            #send(conn, bytes_read)
    sleep(2)
    send(conn, "close:"+filename)

def handle_server(conn, addr):
    print("[CONNECTED] " + str(addr))

    connected = True
    while connected:
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
        except:
            break
        if msg_length:
            try:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)
                if msg == PING_MESSAGE:
                    send(conn, PING_MESSAGE)
                if msg == DISCONNECT_MESSAGE:
                    #print("[DISCONNECTED] " + str(addr))
                    close_conn(conn)
                    connected = False
                #print("[" + str(addr) + "]: " + msg)
                if msg.startswith(FAIL_MESSAGE):
                    failed_message = msg.replace(FAIL_MESSAGE, '')
                    for message in send_queue:
                        if failed_message in message:
                            send(conn, message)

                if (not msg.startswith(CONFIRM_MESSAGE)) and (not msg.startswith(FAIL_MESSAGE)):
                    msg_queue.append(msg)
            except Exception as err:
                print(err)
    return

def get_msg():
    if msg_queue:
        msg = msg_queue.pop(0)
        return msg


def close_conn(conn):
    send(conn, DISCONNECT_MESSAGE)
    conn.shutdown(SHUT_RDWR)
    conn.close()
    print("[DISCONNECTED]: " + str(ADDR))

def start():
    client = socket(AF_INET, SOCK_STREAM)
    client.connect(ADDR)
    thread = Thread(target=handle_server, args=(client, ADDR))
    thread.start()
    if __name__ == '__main__':
        send(client, "Client:default")
        connected = True
    else:
        return client, ADDR
    while connected:
        print("Send something to Robin: ")
        try:
            text = input()
            send(client, text)
        except KeyboardInterrupt:
            text = "disconnect"
        if text == "disconnect":
            connected = False
            close_conn(client)


if __name__ == '__main__':
    start()
    exit()
