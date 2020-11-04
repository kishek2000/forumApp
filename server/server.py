import socket
import os

###############################################
################## UTILITY FUNCTIONS ##################
###############################################


def find_username(username):
    users_file_descriptor = open("credentials.txt", "r")
    users_credentials = users_file_descriptor.read()
    users_file_descriptor.close()
    users_credentials = users_credentials.splitlines()
    for line in users_credentials:
        stored_username = line.split(' ')[0]
        if username == stored_username:
            return True
    return False


def find_password(username, password):
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


def append_credentials(username, password):
    users_file_descriptor = open("credentials.txt", "a")
    users_file_descriptor.write(f"\n{username} {password}")
    users_file_descriptor.close()


def authenticate_client(client_conn):
    is_authenticated = False
    welcome_message = ""
    username = ""
    while True:
        # Receive the username inputted by the client
        username = client_conn.recv(1024).decode('utf-8')
        if (find_username(username)):
            # Confirm that username was found
            client_conn.send(str(True).encode('utf-8'))
            # Receive entry for password
            password = client_conn.recv(1024).decode('utf-8')
            # Check if password is true
            if (find_password(username, password)):
                is_authenticated = True
                welcome_message = "Welcome to the forum"
                # Send confirmation that it's right
                client_conn.send(
                    str("authenticated").encode('utf-8'))
                print(f"{username} successful login")
                break
            else:
                # Invalid password, try again
                print("Incorrect password")
                client_conn.send(str(False).encode('utf-8'))
        else:
            print("New user")
            client_conn.send(str(False).encode('utf-8'))
            # Receive new password for this new username
            new_password = client_conn.recv(1024).decode('utf-8')
            # Append into credentials.txt file
            append_credentials(username, new_password)
            # Send confirmation and authenticate the user
            client_conn.send(str("authenticated").encode('utf-8'))
            is_authenticated = True
            print(f"{username} successfully logged in")
            break

    return (is_authenticated, welcome_message, username)


def listen_to_client_commands(client_conn, username):
    # Begin infinite loop for system use by client
    while True:
        # Receive  option by client
        selection = client_conn.recv(1024).decode('utf-8')
        # Print client operation
        print(username, "issued", selection[0:3], "command")
        # Execute the client's command selection
        execute_command_selection(selection, username, client_conn)


def get_active_threads():
    active_threads = os.listdir()
    active_threads.remove('credentials.txt')
    active_threads.remove('server.py')
    return active_threads

###############################################
########### FORUM COMMAND FUNCTIONS ###########
###############################################


def handle_create_thread_command(client_command, username, client_conn):
    '''
    Handler for CRT command
        --> The client should pass in a thread name
        --> Thread name should be one word after the CRT command
    '''
    # Strip off the thread title from the client's command
    thread_title = client_command.split(" ")[1]
    # Check if the title exists in active threads
    active_threads = get_active_threads()
    if thread_title in active_threads:
        error_message = f"Thread {thread_title} exists"
        print(error_message)
        client_conn.send(
            str({"msg": error_message, "stdout": 'True'}).encode('utf-8')
        )
    else:
        # Create file for our thread
        open(thread_title, "x")
        client_conn.send(
            str({"msg": "success", "stdout": 'False'}).encode('utf-8')
        )
        # Open writable file descriptor and add username at the top
        thread_fd = open(thread_title, "a")
        thread_fd.write(username)


def handle_post_message_command(client_command, username, client_conn):
    '''
    Handler for MSG command
    '''

    pass


def handle_delete_message_command(client_command, username, client_conn):
    '''
    Handler for DLT command
    '''
    pass


def handle_edit_message_command(client_command, username, client_conn):
    '''
    Handler for EDT command
    '''
    pass


def handle_list_threads_command(client_command, username, client_conn):
    '''
    Handler for LST command
        --> The client should pass no params
        --> This handler should simply list active threads by title
    '''
    # Extract the files in this dir and remove config files
    active_threads = get_active_threads()
    if len(active_threads) > 0:
        active_threads_string = "\n".join(active_threads)
        client_conn.send(
            str({"msg": f"The list of active threads:\n{active_threads_string}",
                 "stdout": 'True'}).encode('utf-8')
        )
    else:
        print(active_threads)
        client_conn.send(
            str({"msg": "No threads to list", "stdout": 'True'}).encode('utf-8')
        )


def handle_read_thread_command(client_command, username, client_conn):
    '''
    Handler for RDT command
    '''
    pass


def handle_upload_file_command(client_command, username, client_conn):
    '''
    Handler for UPD command
    '''
    pass


def handle_download_file_command(client_command, username, client_conn):
    '''
    Handler for DWN command
    '''
    pass


def handle_remove_thread_command(client_command, username, client_conn):
    '''
    Handler for RMV command
    '''
    pass


def handle_exit_command(client_command, username, client_conn):
    '''
    Handler for XIT command
    '''
    pass


def handle_shutdown_server_command(client_command, username, client_conn):
    '''
    Handler for SHT command
    '''
    pass


# Setup for commands handler
COMMAND_SWITCH = {
    "CRT": handle_create_thread_command,
    "MSG": handle_post_message_command,
    "DLT": handle_delete_message_command,
    "EDT": handle_edit_message_command,
    "LST": handle_list_threads_command,
    "RDT": handle_read_thread_command,
    "UPD": handle_upload_file_command,
    "DWN": handle_download_file_command,
    "RMV": handle_remove_thread_command,
    "XIT": handle_exit_command,
    "SHT": handle_shutdown_server_command
}


def execute_command_selection(command_selection, username, client_conn):
    COMMAND_SWITCH[command_selection[0:3]](
        command_selection, username, client_conn
    )

###############################################
##################### MAIN ####################
###############################################


def run_server():
    while True:
        # Establish connection with client.
        client_conn, _ = s.accept()
        print("Client connected")

        # Handle the authentication process
        is_authenticated, welcome_message, username = authenticate_client(
            client_conn)

        if (is_authenticated):
            # Receive confirmation by client for their receipt of authentication
            confirmation = client_conn.recv(1024).decode('utf-8')
            # Send a welcome message to the client for the forum if they are a returning user
            if (welcome_message and confirmation):
                client_conn.send(str(welcome_message).encode('utf-8'))

            listen_to_client_commands(client_conn, username)
        # Close the connection with the client
        client_conn.close()


if __name__ == "__main__":
    s = socket.socket()
    port = 12345
    s.bind(('', port))

    print("Waiting for clients")
    s.listen(5)
    run_server()
