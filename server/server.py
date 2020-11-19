import os
import re
import json
import socket
import threading

from pathlib import Path
from utils import ForumUtils, SocketUtils
from forum_commands import ForumCommands
from forum_service import ForumService


class ClientThread(threading.Thread):
    def __init__(self, client_socket, server):
        ''' Here, we initialise everything we need for each client thread '''
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.server_ops = server
        self.forum_service = ForumService(
            self.client_socket, self.server_ops
        )
        self.running = True

    def shutdown(self, shutdown_msg):
        self.forum_service.socket_utils.send_message(shutdown_msg)
        self.client_socket.close()

    def run(self):
        ''' This function is where we run our services for the connected client '''
        while self.running:
            is_authenticated, welcome_message, username = self.forum_service.authenticate_client(
                self.client_socket
            )
            if (is_authenticated):
                # Receive confirmation by client for their receipt of authentication
                confirmation = self.forum_service.socket_utils.recv_message()
                # Send a welcome message to the client for the forum if they are a returning user
                if (welcome_message and confirmation):
                    self.forum_service.socket_utils.send_message(
                        welcome_message)
                    _ = self.forum_service.socket_utils.recv_message()

                connection_state = self.forum_service.command_listener(
                    self.client_socket, username, self.server_ops.clients_object
                )
                if 'exit' in connection_state.keys():
                    # Close the connection with the client, and end the loop
                    self.client_socket.close()
                    break
        self.server_ops.ACTIVE_USERS.remove(username)


class Server():
    def __init__(self):
        # Constants for server
        self.PORT = 8080
        self.ADDR = '127.0.0.1'
        self.THREADS = []
        self.ACTIVE_USERS = []

        # Lock for all clients
        self.CLIENTS_LOCK = threading.Lock()
        self.clients_object = {
            "lock": self.CLIENTS_LOCK,
            "clients": self.THREADS
        }

        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run_server(self):
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        self.server_socket.bind(('', self.PORT))
        print("Waiting for clients")
        try:
            while True:
                self.server_socket.listen(1)
                # Connect to client
                client_socket, _ = self.server_socket.accept()
                print("Client connected")
                # Initialise new client thread
                new_client_thread = ClientThread(
                    client_socket, self
                )
                new_client_thread.start()
                with self.CLIENTS_LOCK:
                    self.THREADS.append(new_client_thread)
        except KeyboardInterrupt:
            os._exit(0)


if __name__ == "__main__":
    server = Server()
    server.run_server()
