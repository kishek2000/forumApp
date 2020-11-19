import os
import json
import re
import math
from utils import ForumUtils, SocketUtils


class ForumCommands():
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.forum_utils = ForumUtils()
        self.socket_utils = SocketUtils(self.client_socket)

    def handle_create_thread_command(self, client_command, username, clients):
        '''
        Handler for CRT command
            --> The client should pass in a thread name
            --> Thread name should be one word after the CRT command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 2:
            self.socket_utils.send_message(
                "Invalid syntax for CRT", stdout="True"
            )
        else:
            # Strip off the thread title from the client's command
            thread_title = client_command.split(" ")[1]
            # Check if the title exists in active threads
            active_threads = self.forum_utils.get_active_threads()
            if thread_title in active_threads:
                error_message = f"Thread {thread_title} exists"
                print(error_message)
                self.socket_utils.send_message(
                    error_message, stdout="True"
                )
            else:
                # Create file for our thread
                open(thread_title, "x")
                self.socket_utils.send_message(
                    str(f"Thread {thread_title} created"), stdout="True"
                )
                # Open writable file descriptor and add username at the top
                thread_fd = open(thread_title, "a")
                print(f"Thread {thread_title} created")
                thread_fd.write(username)

    def handle_post_message_command(self, client_command, username, clients):
        '''
        Handler for MSG command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) <= 2:
            self.socket_utils.send_message(
                "Invalid syntax for MSG", stdout="True"
            )
        else:
            # Strip off the thread title and message
            thread_title = client_command.split(" ")[1]
            message = " ".join(client_command.split(" ")[2:])

            # Check the thread_title provided is in the active threads
            # If so, append the message with the appropriate message number
            active_threads = self.forum_utils.get_active_threads()
            if thread_title in active_threads:
                read_thread_fd = open(thread_title, "r")
                read_thread_fd_lines = read_thread_fd.read()
                total_messages = len(read_thread_fd_lines.splitlines()) - 1
                read_thread_fd.close()

                write_thread_fd = open(thread_title, "a")
                write_thread_fd.write(
                    f"\n{total_messages + 1} {username}: {message}")
                self.socket_utils.send_message(
                    str(f"Message posted to {thread_title} thread"), stdout="True"
                )
                print(f"Message posted to {thread_title} thread")
            else:
                self.socket_utils.send_message(
                    str(f"Thread {thread_title} does not exist"), stdout="True"
                )

    def handle_delete_message_command(self, client_command, username, clients):
        '''
        Handler for DLT command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 3:
            self.socket_utils.send_message(
                "Invalid syntax for DLT", stdout="True"
            )
        else:
            # Strip off the thread title and the message number
            thread_title = client_command.split(" ")[1]
            message_number = client_command.split(" ")[2]
            # Check if thread exists, then check if message exists, then check if
            # the given username was the one who created that message
            active_threads = self.forum_utils.get_active_threads()
            if thread_title in active_threads:
                thread_messages = self.forum_utils.get_thread_messages(
                    thread_title)
                total_messages = len(thread_messages)
                message_index = int(message_number)-1
                if total_messages > message_index:
                    message_creator = thread_messages[message_index].split(" ")[
                        1].replace(':', '')

                    if message_creator == username:
                        message_to_delete = thread_messages[message_index]
                        self.forum_utils.delete_thread_message(
                            thread_title, message_to_delete)

                        self.socket_utils.send_message(
                            "The message has been deleted", stdout="True"
                        )
                    else:
                        self.socket_utils.send_message(
                            "The message belongs to another user and cannot be deleted", stdout="True"
                        )
                        print("Message cannot be deleted")
                else:
                    self.socket_utils.send_message(
                        "The message does not exist in this thread", stdout="True"
                    )
            else:
                self.socket_utils.send_message(
                    str(f"Thread {thread_title} does not exist"), stdout="True"
                )

    def handle_edit_message_command(self, client_command, username, clients):
        '''
        Handler for EDT command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) <= 3:
            self.socket_utils.send_message(
                "Invalid syntax for EDT", stdout="True"
            )
        else:
            # Strip off the thread title and the message number
            thread_title = client_command.split(" ")[1]
            message_number = client_command.split(" ")[2]
            updated_message = client_command.split(" ")[3:]
            # Check if thread exists, then check if message exists, then check if
            # the given username was the one who created that message
            active_threads = self.forum_utils.get_active_threads()
            if thread_title in active_threads:
                thread_messages = self.forum_utils.get_thread_messages(
                    thread_title)
                total_messages = len(thread_messages)
                message_index = int(message_number)
                if total_messages >= message_index:
                    message_to_update = " ".join(updated_message)
                    message_creator = thread_messages[message_index-1].split(" ")[
                        1].replace(':', '')

                    if message_creator == username:
                        self.forum_utils.update_thread_message(
                            thread_title, message_to_update, message_index
                        )

                        self.socket_utils.send_message(
                            "The message has been updated", stdout="True"
                        )
                    else:
                        self.socket_utils.send_message(
                            "The message belongs to another user and cannot be edited", stdout="True"
                        )
                        print("Message cannot be edited")
                else:
                    self.socket_utils.send_message(
                        "The message does not exist in this thread", stdout="True"
                    )
            else:
                self.socket_utils.send_message(
                    str(f"Thread {thread_title} does not exist"), stdout="True"
                )

    def handle_list_threads_command(self, client_command, username, clients):
        '''
        Handler for LST command
            --> The client should pass no params
            --> This handler should simply list active threads by title
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 1:
            self.socket_utils.send_message(
                "Invalid syntax for LST", stdout="True"
            )
        else:
            # Extract the files in this dir and remove config files
            active_threads = self.forum_utils.get_active_threads()
            if len(active_threads) > 0:
                active_threads_string = "\n".join(active_threads)
                self.socket_utils.send_message(
                    str(f"The list of active threads:\n{active_threads_string}"), stdout="True"
                )

            else:
                self.socket_utils.send_message(
                    "No threads to list", stdout="True"
                )

    def handle_read_thread_command(self, client_command, username, clients):
        '''
        Handler for RDT command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 2:
            self.socket_utils.send_message(
                "Invalid syntax for RDT", stdout="True"
            )
        else:
            # Strip the thread title from command
            thread_title = client_command.split(" ")[1]
            # If it's part of the active threads, send the messages
            active_threads = self.forum_utils.get_active_threads()
            if thread_title in active_threads:
                thread_messages = self.forum_utils.get_thread_messages(
                    thread_title)
                if len(thread_messages) == 0:
                    self.socket_utils.send_message(
                        str(f"Thread {thread_title} is empty"), stdout="True"
                    )

                else:
                    thread_messages_string = '\n'.join(thread_messages)
                    self.socket_utils.send_message(
                        thread_messages_string, stdout="True"
                    )
            else:
                self.socket_utils.send_message(
                    "Thread does not exist", stdout="True"
                )

    def handle_upload_file_command(self, client_command, username, clients):
        '''
        Handler for UPD command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 3:
            self.socket_utils.send_message(
                "Invalid syntax for UPD", stdout="True"
            )
        else:
            # Strip thread title from command
            thread_title = client_command.split(" ")[1]
            # Get active threads
            active_threads = self.forum_utils.get_active_threads()
            # Check if title is in active threads
            if thread_title in active_threads:
                # Confirm the thread was found to the client, and ask them for their file
                self.socket_utils.send_message("Thread found, send file")
                # Receive username and filename from client
                file_info_obj = self.socket_utils.recv_message()
                username = file_info_obj["username"]
                filename = file_info_obj["filename"]
                chunks = file_info_obj["chunks"]

                # Confirm json was received
                self.socket_utils.send_message("Received")
                # Receive file
                new_file_fd = open(str(f"{thread_title}-{filename}"), "wb")
                new_file_contents = b''
                while chunks > 0:
                    new_file_contents += self.socket_utils.recv_bytes()
                    self.socket_utils.send_message(
                        str(f"Received chunk no. {chunks}"))
                    chunks -= 1
                new_file_fd.write(new_file_contents)
                new_file_fd.close()

                thread_fd = open(thread_title, "a")
                thread_fd.write(str(f"\n{username} uploaded {filename}"))

                # Confirm file uploaded
                self.socket_utils.send_message(
                    str(f"{filename} uploaded to {thread_title} thread"), stdout="True"
                )
                print(f"{username} uploaded {filename} to {thread_title} thread")
            else:
                self.socket_utils.send_message(
                    str(f"{thread_title} thread does not exist"), stdout="True"
                )

    def handle_download_file_command(self, client_command, username, clients):
        '''
        Handler for DWN command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 3:
            self.socket_utils.send_message(
                "Incorrect syntax for DWN", stdout="True"
            )
        else:
            # Strip thread title and filenme from command
            thread_title = client_command.split(" ")[1]
            filename = client_command.split(" ")[2]
            # Get active threads
            active_threads = self.forum_utils.get_active_threads()
            # Check if title is in active threads
            if thread_title in active_threads:
                # check if the file exists in thread
                server_files = os.listdir()
                server_filename = str(f"{thread_title}-{filename}")
                if server_filename in server_files:
                    # Confirm we can send file to client, and send the chunks needed
                    chunks = math.ceil(os.path.getsize(filename) / 1024)
                    self.socket_utils.send_message(
                        "Sending file details",
                        options={
                            "filename": filename,
                            "chunks": chunks
                        }
                    )
                    # Ack from client
                    _ = self.socket_utils.recv_message()
                    with open(server_filename, "rb") as file:
                        thread_file_contents = file.read(1024)
                        while thread_file_contents:
                            self.socket_utils.send_bytes(thread_file_contents)
                            # Ack from client that they received chunk
                            _ = self.socket_utils.recv_message()
                            thread_file_contents = file.read(1024)
                    print(f"{filename} downloaded from {thread_title} thread")
                else:
                    self.socket_utils.send_message(
                        str(f"File does not exist in {thread_title} thread"), stdout="True"
                    )
                    print(f"{filename} does not exist in {thread_title} thread")
            else:
                self.socket_utils.send_message(
                    str(f"{thread_title} thread does not exist"), stdout="True"
                )

    def handle_remove_thread_command(self, client_command, username, clients):
        '''
        Handler for RMV command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 2:
            self.socket_utils.send_message(
                "Invalid syntax for RMV", stdout="True"
            )
        else:
            # Strip thread title from command
            thread_title = client_command.split(" ")[1]
            # Get the active threads
            active_threads = self.forum_utils.get_active_threads()
            # If in active thread, then check if the
            # username was the creator of the thread.
            # If so, remove, otherwise send error.
            # If not in active thread, also send error
            if thread_title in active_threads:
                read_file_fd = open(thread_title, "r")
                creator = read_file_fd.readlines()[0].strip("\n")
                if creator == username:
                    os.remove(thread_title)
                    server_files = os.listdir()
                    for file in server_files:
                        if thread_title in file:
                            os.remove(file)
                    print(f"Thread {thread_title} removed")
                    self.socket_utils.send_message(
                        str(f"Thread {thread_title} removed"), stdout="True"
                    )
                else:
                    self.socket_utils.send_message(
                        str(f"The thread {thread_title} was created by another user and cannot be removed"), stdout="True"
                    )

            else:
                self.socket_utils.send_message(
                    str(f"Thread {thread_title} does not exist"), stdout="True"
                )

    def handle_exit_command(self, client_command, username, clients):
        '''
        Handler for XIT command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 1:
            self.socket_utils.send_message(
                "Invalid syntax for XIT", stdout="True"
            )
        else:
            self.socket_utils.send_message(
                "Goodbye", stdout="True"
            )
            return {'exit': True}

    def handle_shutdown_server_command(self, client_command, username, clients):
        '''
        Handler for SHT command
        '''
        # Simple syntax check of command - return error message if incorrect
        if len(client_command.split(" ")) != 2:
            self.socket_utils.send_message(
                "Invalid syntax for SHT", stdout="True"
            )
        else:
            # Strip password
            admin_password = client_command.split(" ")[1]
            if admin_password != "destroyforum":
                self.socket_utils.send_message(
                    "Invalid admin password", stdout="True"
                )
            else:
                with clients["lock"]:
                    for client in clients["clients"]:
                        client.shutdown(
                            {
                                "msg": "Goodbye. Server shutting down",
                                "stdout": "True",
                                "shutdown": "True"
                            }
                        )
                print("Server shutting down")
                server_files = os.listdir()
                server_files.remove("server.py")
                server_files.remove('forum_service.py')
                server_files.remove('forum_commands.py')
                server_files.remove('utils.py')
                for file in server_files:
                    os.remove(file)
                os._exit(0)
