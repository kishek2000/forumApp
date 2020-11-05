import socket
import json

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
    return is_authenticated


def handle_system_commands(s):
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
                print(command_response["msg"])


def get_response_object(res):
    return json.loads(res.replace("'", "\""))


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
    is_authenticated = handle_authentication(s)
    if is_authenticated["success"]:
        handle_welcome_message(is_authenticated["new"], s)
        handle_system_commands(s)
    # close the connection
    s.close()


if __name__ == "__main__":
    s = socket.socket()
    port = 12345
    s.connect(('127.0.0.1', port))
    run_client(s)
