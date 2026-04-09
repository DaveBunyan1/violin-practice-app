import socket
from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()


while True:
    communication_socket, address = server.accept()
    print(f"Connected to {address}")
    message = communication_socket.recv(1024).decode("utf-8")
    print(f"Message from client is {message}")
    communication_socket.send("Got your message.".encode("utf-8"))
    communication_socket.close()
    print(f"Connection with {address} ended!")
