import socket
import json
import re

###############################################
################## FUNCTIONS ##################
###############################################


def handle_authentication(s):
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
    return is_authenticated, username


def handle_system_commands(s, username):
    # Begin an infinite loop for using the system by its commands
    while True:
        commands_prompt = s.recv(1024).decode('utf-8')
        option_choice = input(commands_prompt)
        s.send(option_choice.encode('utf-8'))

        # Server response, validating command:
        res = s.recv(1024).decode('utf-8')
        response_validation = get_response_object(res)
        if response_validation["stdout"] == 'True':
            # Print error message
            print(response_validation["msg"])
        elif option_choice[0:3] == "UPD":
            # Send confirmation from client
            s.send(str({"msg": "confirmed validation",
                        "stdout": 'False'}).encode('utf-8'))
            # At this point in uploading a file, we now need to send
            # the username and the filename
            _ = s.recv(1024).decode('utf-8')
            file_name = option_choice.split(" ")[2]
            s.send(
                str({"username": str(username), "filename": str(file_name)}).encode('utf-8'))
            # After sending these, we look for confirmation from the server it was received
            _ = s.recv(1024).decode('utf-8')
            # Finally, we then send the file
            file_bytes = open(file_name, "r").read()
            s.send(file_bytes.encode('utf-8'))
            # Receive confirmation from server for sent file
            res = s.recv(1024).decode('utf-8')
            command_response = get_response_object(res)
            # Send confirmation for command response from client
            s.send(str({"msg": "confirmed response",
                        "stdout": 'False'}).encode('utf-8'))
            if command_response["stdout"] == 'True':
                handle_command_response(s, command_response)
        elif option_choice[0:3] == "DWN":
            # Send confirmation from client
            s.send(str({"msg": "confirmed validation",
                        "stdout": 'False'}).encode('utf-8'))
            # At this point in uploading a file, if it's all good we can receive it
            response = s.recv(1024).decode('utf-8')
            command_response = get_response_object(response)
            # If all good, we can write the file:
            if command_response["filename"]:
                downloaded_file_fd = open(command_response["filename"], "w")
                downloaded_file_fd.write(command_response["contents"])
                print(
                    f"{command_response['filename']} successfully downloaded")
        else:
            # Send confirmation from client
            s.send(str({"msg": "confirmed validation",
                        "stdout": 'False'}).encode('utf-8'))

            # Receive response from server for command provided
            res = s.recv(1024).decode('utf-8')
            command_response = get_response_object(res)
            # Send confirmation for command response from client
            s.send(str({"msg": "confirmed response",
                        "stdout": 'False'}).encode('utf-8'))
            if command_response["stdout"] == 'True':
                handle_command_response(s, command_response)


def handle_command_response(s, command_response):
    if command_response["msg"] == "Goodbye":
        print(command_response["msg"])
        s.close()
        exit(0)
    else:
        print(command_response["msg"])


def get_response_object(res):
    json_string = re.sub(r"'", r'"', res)
    json_string = re.sub(r"([\w]+)\"([\w]+)", r"\1'\2", json_string)
    return json.loads(json_string)


def handle_welcome_message(is_new_authenticated_user, s):
    if not is_new_authenticated_user:
        # If you are a returning user, there is a welcome message
        welcome_message = s.recv(1024).decode('utf-8')
        print(welcome_message)
        # Send confirmation from client
        s.send(str({"msg": "received welcome", "stdout": 'False'}).encode('utf-8'))

###############################################
##################### MAIN ####################
###############################################


def run_client(s):
    is_authenticated, username = handle_authentication(s)
    if is_authenticated["success"]:
        handle_welcome_message(is_authenticated["new"], s)
        handle_system_commands(s, username)
    # close the connection
    s.close()


if __name__ == "__main__":
    s = socket.socket()
    port = 12345
    s.connect(('127.0.0.1', port))
    run_client(s)
