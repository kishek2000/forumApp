import socket
import json
import re
import os
import sys
import math
import select
import time

from utils import SocketUtils


class Client():
    def __init__(self):
        self.port = 8080
        self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.forum_utils = ClientForumUtils(self.server_conn)
        self.client_commands = ClientCommands(self.server_conn)

    def connect_client(self):
        try:
            self.server_conn.connect(('', self.port))
            self.run_client(self.server_conn)
        except KeyboardInterrupt:
            pass

    def run_client(self, server_conn):
        is_authenticated, username = self.forum_utils.handle_authentication(
            server_conn)
        if is_authenticated["success"]:
            self.client_commands.handle_welcome_message(
                is_authenticated["new"], server_conn
            )
            self.client_commands.initiate_forum_connection(
                server_conn, username
            )
        # close the connection
        server_conn.close()


class ClientForumUtils():
    def __init__(self, server_conn):
        self.server_conn = server_conn
        self.socket_utils = SocketUtils(self.server_conn)

    def handle_authentication(self, server_conn):
        is_authenticated = {"success": False, "new": False}
        while (True):
            username = input("Enter username: ")
            self.socket_utils.send_message(
                "Sending username", stdout="False", options={"username": username}
            )
            username_confirmation = self.socket_utils.recv_message()

            if "success" in dict.keys(username_confirmation) and username_confirmation["success"] == "True":
                password = input("Enter password: ")
                self.socket_utils.send_message(
                    "Sending password", stdout="False", options={"password": password}
                )
                # Check for confirmation from server
                success = self.socket_utils.recv_message()
                if "success" in dict.keys(success) and success["success"] == "True":
                    is_authenticated = {"success": True, "new": False}
                    # Send acknowledgement of receiving authentication
                    self.socket_utils.send_message("Authentication received")
                    break
                else:
                    # Send acknowledgement of receiving failure
                    self.socket_utils.send_message("Failure received")
                    print(success["msg"])
            elif username_confirmation["stdout"] == "True":
                # Send acknowledgement of receiving failure
                self.socket_utils.send_message("Failure received")
                print(username_confirmation["msg"])
            else:
                new_password = input(f"Enter new password for {username}: ")
                self.socket_utils.send_message(
                    "Sending new password", stdout="False", options={"password": new_password}
                )
                # Check for confirmation from server
                _ = self.socket_utils.recv_message()
                # new_user_is_authenticated = get_response_object(res)
                # print(new_user_is_authenticated["msg"])
                is_authenticated = {"success": True, "new": True}
                # Send acknowledgement of receiving authentication
                self.socket_utils.send_message("Authentication received")
                break
        return is_authenticated, username

    def handle_shutdown(self, res, server_conn):
        if "shutdown" in dict.keys(res) and res["shutdown"] == "True":
            print(res["msg"])
            server_conn.close()
            os._exit(0)

    def handle_command_response(self, server_conn, command_response):
        if command_response["msg"] == "Goodbye":
            print(command_response["msg"])
            server_conn.close()
            sys.exit(0)
        else:
            print(command_response["msg"])


class ClientCommands():
    def __init__(self, server_conn):
        self.server_conn = server_conn
        self.socket_utils = SocketUtils(self.server_conn)
        self.client_forum_utils = ClientForumUtils(self.server_conn)

    def initiate_forum_connection(self, server_conn, username):
        # Begin an infinite loop for using the system by its commands
        while True:
            commands_prompt_obj = self.socket_utils.recv_message()
            print(commands_prompt_obj["msg"])
            in_ready, _, _ = select.select(
                [sys.stdin, server_conn], [], [], 100
            )

            for channel in in_ready:
                if channel == server_conn:
                    res_obj = self.socket_utils.recv_message()
                    self.client_forum_utils.handle_shutdown(
                        res_obj, server_conn
                    )
                elif channel == sys.stdin:
                    option_choice = channel.readline().rstrip()
                    self.process_command(server_conn, option_choice, username)

    def handle_upload(self, server_conn, option_choice, username):
        # At this point in uploading a file, we now need to send
        # the username and the filename
        _ = self.socket_utils.recv_message()
        filename = option_choice.split(" ")[2]
        # Check the filename is in the cwd:
        if not os.path.exists(filename):
            print(
                f"File {filename} does not exist in your directory. Please try again."
            )
        else:
            # Compute the chunks:
            chunks = math.ceil(os.path.getsize(filename) / 1024)
            self.socket_utils.send_message(
                "Sending file details",
                stdout="False",
                options={
                    "username": username, "filename": filename, "chunks": chunks
                }
            )
            # After sending these, we look for confirmation from the server it was received
            _ = self.socket_utils.recv_message()
            # Finally, we then send the file
            with open(filename, "rb") as file:
                thread_file_contents = file.read(1024)
                while thread_file_contents:
                    self.socket_utils.send_bytes(thread_file_contents)
                    # Ack from server that they received chunk
                    _ = self.socket_utils.recv_message()
                    thread_file_contents = file.read(1024)

            # Receive final confirmation from server for sent file
            command_response = self.socket_utils.recv_message()
            # Send confirmation for command response from client
            self.socket_utils.send_message("Confirmed upload successful")
            if command_response["stdout"] == 'True':
                self.client_forum_utils.handle_command_response(
                    server_conn, command_response
                )

    def handle_download(self, server_conn, option_choice, username):
        # At this point in uploading a file, if it's all good we can receive it
        command_response = self.socket_utils.recv_message()
        # If all good, we can write the file:
        if "filename" in dict.keys(command_response):
            self.socket_utils.send_message("Ready to download")
            downloaded_file_fd = open(
                command_response["filename"], "wb"
            )
            chunks = command_response["chunks"]
            file_contents = b''
            while chunks > 0:
                file_contents += self.socket_utils.recv_bytes()
                self.socket_utils.send_message(
                    str(f"Received chunk no {chunks}")
                )
                chunks -= 1
            downloaded_file_fd.write(file_contents)
            downloaded_file_fd.close()
            print(
                f"{command_response['filename']} successfully downloaded"
            )
            # Send confirmation for command response from client
            self.socket_utils.send_message("Successfully downloaded file")
        else:
            self.client_forum_utils.handle_command_response(
                server_conn, command_response
            )
            # Send confirmation for command response from client
            self.socket_utils.send_bytes("Confirmed response")

    def process_command(self, server_conn, option_choice, username):
        self.socket_utils.send_message(option_choice)
        # Server response, validating command:
        response_validation = self.socket_utils.recv_message()
        # Send confirmation from client
        self.socket_utils.send_message("Confirmed validation")
        if response_validation["stdout"] == 'True':
            # Print error message
            print(response_validation["msg"])
        elif option_choice[0:3] == "UPD":
            self.handle_upload(server_conn, option_choice, username)
        elif option_choice[0:3] == "DWN":
            self.handle_download(server_conn, option_choice, username)
        else:
            # Receive response from server for command provided
            command_response = self.socket_utils.recv_message()
            self.client_forum_utils.handle_shutdown(
                command_response, server_conn
            )
            # Send confirmation for command response from client
            self.socket_utils.send_message("Confirmed response")
            if command_response["stdout"] == 'True':
                self.client_forum_utils.handle_command_response(
                    server_conn, command_response
                )

    def handle_welcome_message(self, is_new_authenticated_user, server_conn):
        if not is_new_authenticated_user:
            # If you are a returning user, there is a welcome message
            welcome_message_obj = self.socket_utils.recv_message()
            print(welcome_message_obj["msg"])
            # Send confirmation from client
            self.socket_utils.send_bytes("Received welcome")


if __name__ == "__main__":
    client = Client()
    client.connect_client()
