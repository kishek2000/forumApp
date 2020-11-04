import socket
import json

###############################################
################## FUNCTIONS ##################
###############################################


def handle_authentication():
    is_authenticated = {"success": False, "new": False}
    while (True):
        username = input("Enter username: ")
        s.send(str(username).encode('utf-8'))
        username_confirmation = s.recv(1024).decode('utf-8')

        if username_confirmation == "True":
            password = input("Enter password: ")
            s.send(str(password).encode('utf-8'))
            # Check for confirmation from server
            success = s.recv(1024).decode('utf-8')
            if success == "authenticated":
                is_authenticated = {"success": True, "new": False}
                # Send acknowledgement of receiving authentication
                s.send(str("authentication received").encode('utf-8'))
                break
            else:
                print("Invalid password")
        else:
            new_password = input(f"Enter new password for {username}: ")
            s.send(str(new_password).encode('utf-8'))
            # Check for confirmation from server
            new_user_is_authenticated = s.recv(1024).decode('utf-8')
            if new_user_is_authenticated == "authenticated":
                is_authenticated = {"success": True, "new": True}
                # Send acknowledgement of receiving authentication
                s.send(str("authentication received").encode('utf-8'))
                break
    return is_authenticated


def handle_system_commands():
    # Begin an infinite loop for using the system by its commands
    while True:
        # The commands that can be chosen by a user:
        commands_list = ["CRT", "MSG", "DLT", "EDT", "LST",
                         "RDT", "UPD", "DWN", "RMV", "XIT", "SHT"]

        command_prompt = "Enter one of the following commands: " + \
            ", ".join(commands_list) + ":\n"
        option_choice = input(str(command_prompt))

        # The handlers for each command
        if option_choice[0:3] in commands_list:
            # Send choice by client to server
            s.send(str(option_choice).encode('utf-8'))
            res = s.recv(1024).decode('utf-8')
            response = json.loads(res.replace("'", "\""))
            if response["stdout"] == 'True':
                print(response["msg"])
        else:
            print("Invalid command")


def handle_welcome_message(is_new_authenticated_user):
    if not is_new_authenticated_user:
        # If you are a returning user, there is a welcome message
        welcome_message = s.recv(1024).decode('utf-8')
        print(welcome_message)

###############################################
##################### MAIN ####################
###############################################


def run_client():
    is_authenticated = handle_authentication()
    if is_authenticated["success"]:
        handle_welcome_message(is_authenticated["new"])
        handle_system_commands()
    # close the connection
    s.close()


if __name__ == "__main__":
    s = socket.socket()
    port = 12345
    s.connect(('127.0.0.1', port))
    run_client()
