import threading
import socket
from dotenv import load_dotenv
import os
from typing import List
from audio.record import note_queue

load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()


clients: List[socket.socket] = []


def broadcast(message: bytes):
    for client in clients:
        client.send(message)


def handle(client: socket.socket):
    while True:
        try:
            message = client.recv(1024)
            broadcast(message)
        except:
            clients.remove(client)
            client.close()
            break


def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {address}.")

        clients.append(client)

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


def broadcast_pitch():
    while True:
        freq, note = note_queue.get()
        msg = f"{freq:.2f} Hz → {note}".encode("utf-8")
        broadcast(msg)


def run():
    threading.Thread(target=receive).start()
    threading.Thread(target=broadcast_pitch).start()
    print(f"TCP server running on {HOST}:{PORT}")
