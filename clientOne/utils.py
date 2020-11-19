import json
import re


class SocketUtils():
    def __init__(self, server_socket):
        self.server_socket = server_socket

    def create_message(self, message, stdout="False", options=None):
        msg = {"msg": message, "stdout": stdout}
        if options != None:
            for key in dict.keys(options):
                msg[key] = options[key]
        return msg

    def send_message(self, message, stdout="False", options=None):
        json_obj = self.create_message(message, stdout, options)
        encoded_message = str(json_obj).encode('utf-8')
        try:
            self.server_socket.send(encoded_message)
        except BrokenPipeError:
            print("Connection to server failed.")
            pass

    def recv_bytes(self):
        try:
            file_bytes = self.server_socket.recv(1024)
        except BrokenPipeError:
            print("Connection to client failed.")
            pass
        return file_bytes

    def send_bytes(self, file_bytes):
        try:
            self.server_socket.send(file_bytes)
        except BrokenPipeError:
            print("Connection to server failed.")
            pass

    def recv_message(self, bytes=1024):
        try:
            response = self.server_socket.recv(1024)
        except BrokenPipeError:
            print("Connection to server failed.")
            pass
        res = response.decode('utf-8')
        response_obj = self.get_response_object(res)
        return response_obj

    def get_response_object(self, res):
        json_string = re.sub(r"'", r'"', res)
        json_string = re.sub(r"([\w]+)\"([\w]+)", r"\1'\2", json_string)
        return json.loads(str(json_string))
