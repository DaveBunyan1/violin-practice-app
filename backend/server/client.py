import threading
import socket
from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

client.send("Hello, World!".encode("utf-8"))
print(client.recv(1024).decode("utf-8"))
