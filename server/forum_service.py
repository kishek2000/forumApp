from utils import ForumUtils, SocketUtils
from forum_commands import ForumCommands


class ForumService():
    def __init__(self, client_socket, server):
        self.client_socket = client_socket
        self.socket_utils = SocketUtils(client_socket)
        self.forum_utils = ForumUtils()
        self.server_ops = server
        self.forum_commands = ForumCommands(self.client_socket)

        self.COMMAND_SWITCH = {
            "CRT": self.forum_commands.handle_create_thread_command,
            "MSG": self.forum_commands.handle_post_message_command,
            "DLT": self.forum_commands.handle_delete_message_command,
            "EDT": self.forum_commands.handle_edit_message_command,
            "LST": self.forum_commands.handle_list_threads_command,
            "RDT": self.forum_commands.handle_read_thread_command,
            "UPD": self.forum_commands.handle_upload_file_command,
            "DWN": self.forum_commands.handle_download_file_command,
            "RMV": self.forum_commands.handle_remove_thread_command,
            "XIT": self.forum_commands.handle_exit_command,
            "SHT": self.forum_commands.handle_shutdown_server_command
        }

    def authenticate_client(self, client_socket):
        is_authenticated = False
        welcome_message = ""
        username = ""
        while True:
            # Receive the username inputted by the client
            res_obj = self.socket_utils.recv_message()
            username = res_obj["username"]
            if (self.forum_utils.find_username(username)):
                # This means the username was found. Now, check
                # if it is already being used or not:
                if username in self.server_ops.ACTIVE_USERS:
                    # Specify that the username is already in use
                    self.socket_utils.send_message(
                        str(f"{username} has already logged in"), stdout="True"
                    )
                    print(str(f"{username} has already logged in"))
                    _ = self.socket_utils.recv_message()
                else:
                    # Confirm that username was found and we can
                    # move to the password input, and append
                    # to the users list if valid password inputted
                    self.socket_utils.send_message(
                        "Found user", options={"success": "True"}
                    )
                    # Receive entry for password
                    password_obj = self.socket_utils.recv_message()
                    password = password_obj["password"]
                    # Check if password is true
                    if (self.forum_utils.find_password(username, password)):
                        is_authenticated = True
                        welcome_message = "Welcome to the forum"
                        # Send confirmation that it's right
                        self.socket_utils.send_message(
                            "Authenticated user", options={"success": "True"}
                        )
                        print(f"{username} successful login")
                        self.server_ops.ACTIVE_USERS.append(username)
                        break
                    else:
                        # Invalid password, try again
                        print("Incorrect password")
                        self.socket_utils.send_message(
                            "Incorrect password", stdout="True"
                        )
                        _ = self.socket_utils.recv_message()
            else:
                print("New user")
                self.socket_utils.send_message("New")
                # Receive new password for this new username
                password_obj = self.socket_utils.recv_message()
                new_password = password_obj["password"]
                # Append into credentials.txt file
                self.forum_utils.append_credentials(username, new_password)
                # Send confirmation and authenticate the user
                self.socket_utils.send_message("Successfully logged in")
                is_authenticated = True
                print(f"{username} successfully logged in")
                self.server_ops.ACTIVE_USERS.append(username)
                break
        return (is_authenticated, welcome_message, username)

    def command_listener(self, client_conn, username, clients):
        # Begin infinite loop for system use by client
        while True:
            # Send client a message with all command options
            commands_list = ["CRT", "MSG", "DLT", "EDT", "LST",
                             "RDT", "UPD", "DWN", "RMV", "XIT", "SHT"]
            command_prompt = "Enter one of the following commands: " + \
                ", ".join(commands_list) + ": "

            self.socket_utils.send_message(command_prompt)

            # Receive option by client
            try:
                selection_obj = self.socket_utils.recv_message()
                selection = selection_obj["msg"]
                if selection.split(" ")[0] in commands_list:
                    # Send authentication to client
                    self.socket_utils.send_message("Valid")
                    # Receive confirmation from client
                    _ = self.socket_utils.recv_message()
                    # Print client operation
                    print(username, "issued", selection[0:3], "command")
                    # Execute the client's command selection
                    return_state = self.initiate_service(
                        selection, username, clients
                    )
                    if type(return_state) is dict:
                        if 'exit' in return_state.keys():
                            print(f"{username} exited")
                            return {'exit': True}
                else:
                    self.socket_utils.send_message(
                        "Invalid command", stdout="True"
                    )
                    # Receive confirmation from client
                    _ = self.socket_utils.recv_message()
            except OSError:
                # This means the client has shutdown. Simply pass
                pass

    def initiate_service(self, command_selection, username, clients):
        return_state = self.COMMAND_SWITCH[command_selection[0:3]](
            command_selection, username, clients
        )
        if return_state != None:
            return return_state
        else:
            # Return confirmation from client
            client_confirmation = self.socket_utils.recv_message()
            return client_confirmation
