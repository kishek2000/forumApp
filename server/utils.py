import os
import re
import json
from pathlib import Path


class ForumUtils():
    def __init__(self):
        pass

    def find_username(self, username):
        users_file_descriptor = open("credentials.txt", "r")
        users_credentials = users_file_descriptor.read()
        users_file_descriptor.close()
        users_credentials = users_credentials.splitlines()
        for line in users_credentials:
            stored_username = line.split(' ')[0]
            if username == stored_username:
                return True
        return False

    def find_password(self, username, password):
        users_file_descriptor = open("credentials.txt", "r")
        users_credentials = users_file_descriptor.read()
        users_file_descriptor.close()
        users_credentials = users_credentials.splitlines()
        for line in users_credentials:
            stored_username = line.split(' ')[0]
            stored_password = line.split(' ')[1]
            if password == stored_password and username == stored_username:
                return True
        return False

    def append_credentials(self, username, password):
        users_file_descriptor = open("credentials.txt", "a")
        users_file_descriptor.write(f"\n{username} {password}")
        users_file_descriptor.close()

    def delete_thread_message(self, thread_title, message_to_delete):
        read_file_fd = open(thread_title, "r")
        thread_creator = read_file_fd.read().splitlines()[0]

        current_messages = self.get_thread_messages(thread_title)
        write_file_fd = open(thread_title, "w")
        write_file_fd.write(f"{thread_creator}\n")
        index = 1
        total_new_messages = len(current_messages) - 1
        for old_message in current_messages:
            if old_message != message_to_delete:
                new_message_number = index
                updated_message = str(new_message_number) + " " + \
                    " ".join(old_message.split(" ")[1:])
                if new_message_number < total_new_messages:
                    updated_message += "\n"
                write_file_fd.write(updated_message)
                index += 1

    def update_thread_message(self, thread_title, message_to_update, message_index):
        read_file_fd = open(thread_title, "r")
        thread_creator = read_file_fd.read().splitlines()[0]

        current_messages = self.get_thread_messages(thread_title)
        write_file_fd = open(thread_title, "w")
        write_file_fd.write(f"{thread_creator}\n")
        index = 1
        total_messages = len(current_messages)
        for old_message in current_messages:
            if index == message_index:
                old_message_prefix = " ".join(old_message.split(" ")[0:2])
                write_file_fd.write(old_message_prefix +
                                    " " + message_to_update)
            else:
                write_file_fd.write(old_message)
            if index < total_messages:
                write_file_fd.write("\n")
            index += 1

    def get_active_threads(self):
        server_files = os.listdir()
        server_files.remove('credentials.txt')
        server_files.remove('server.py')
        server_files.remove('forum_service.py')
        server_files.remove('forum_commands.py')
        server_files.remove('utils.py')
        server_files.remove('__pycache__')
        active_threads = []
        for file in server_files:
            if not Path(file).suffix and not re.match("(.+?)(-.+)", file):
                active_threads.append(file)
        return active_threads

    def get_thread_messages(self, thread):
        read_thread_fd = open(thread, "r")
        lines = read_thread_fd.read().splitlines()[1:]
        return lines


class SocketUtils():
    def __init__(self, client_socket):
        self.client_socket = client_socket

    def create_message(self, message, stdout=False, options=None):
        msg = {"msg": message, "stdout": stdout}
        if options != None:
            for key in dict.keys(options):
                msg[key] = options[key]
        return msg

    def send_message(self, message, stdout="False", options=None):
        json_obj = self.create_message(message, stdout, options)
        encoded_message = str(json_obj).encode('utf-8')
        try:
            self.client_socket.send(encoded_message)
        except BrokenPipeError:
            print("Connection to client failed.")
            pass

    def send_bytes(self, file_bytes):
        try:
            self.client_socket.send(file_bytes)
        except BrokenPipeError:
            print("Connection to client failed.")
            pass

    def recv_bytes(self):
        try:
            file_bytes = self.client_socket.recv(1024)
        except BrokenPipeError:
            print("Connection to client failed.")
            pass
        return file_bytes

    def recv_message(self, bytes=1024):
        try:
            response = self.client_socket.recv(1024)
        except BrokenPipeError:
            print("Connection to client failed.")
            pass
        res = response.decode('utf-8')
        response_obj = self.get_response_object(res)
        return response_obj

    def get_response_object(self, res):
        json_string = re.sub(r"'", r'"', res)
        json_string = re.sub(r"([\w]+)\"([\w]+)", r"\1'\2", json_string)
        return json.loads(str(json_string))
