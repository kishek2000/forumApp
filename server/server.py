import socket
import os
import re
import json
from pathlib import Path

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
        # Send client a message with all command options
        commands_list = ["CRT", "MSG", "DLT", "EDT", "LST",
                         "RDT", "UPD", "DWN", "RMV", "XIT", "SHT"]
        command_prompt = "Enter one of the following commands: " + \
            ", ".join(commands_list) + ": "
        client_conn.send(command_prompt.encode('utf-8'))

        # Receive  option by client
        selection = client_conn.recv(1024).decode('utf-8')
        if selection[0:3] in commands_list:
            # Send authentication to client
            client_conn.send(
                str({"msg": "valid", "stdout": "False"}).encode('utf-8')
            )
            # Receive confirmation from client
            _ = client_conn.recv(1024).decode('utf-8')
            # Print client operation
            print(username, "issued", selection[0:3], "command")
            # Execute the client's command selection
            return_state = execute_command_selection(
                selection, username, client_conn)
            if return_state == False:
                client_conn.close()
                print(f"{username} exited")
                break
        else:
            client_conn.send(
                str({"msg": "Invalid command", "stdout": "True"}).encode('utf-8')
            )


def get_active_threads():
    server_files = os.listdir()
    server_files.remove('credentials.txt')
    server_files.remove('server.py')
    active_threads = []
    for file in server_files:
        if not Path(file).suffix:
            active_threads.append(file)
    return active_threads


def get_thread_messages(thread):
    read_thread_fd = open(thread, "r")
    lines = read_thread_fd.read().splitlines()[1:]
    return lines

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
            str({"msg": error_message, "stdout": "True"}).encode('utf-8')
        )
    else:
        # Create file for our thread
        open(thread_title, "x")
        client_conn.send(
            str({"msg": "success", "stdout": "False"}).encode('utf-8')
        )
        # Open writable file descriptor and add username at the top
        thread_fd = open(thread_title, "a")
        thread_fd.write(username)


def handle_post_message_command(client_command, username, client_conn):
    '''
    Handler for MSG command
    '''
    # Strip off the thread title and message
    thread_title = client_command.split(" ")[1]
    message = " ".join(client_command.split(" ")[2:])

    # Check the thread_title provided is in the active threads
    # If so, append the message with the appropriate message number
    active_threads = get_active_threads()
    if thread_title in active_threads:
        read_thread_fd = open(thread_title, "r")
        read_thread_fd_lines = read_thread_fd.read()
        total_messages = len(read_thread_fd_lines.splitlines()) - 1
        read_thread_fd.close()

        write_thread_fd = open(thread_title, "a")
        write_thread_fd.write(f"\n{total_messages + 1} {username}: {message}")
        client_conn.send(
            str({"msg": "success", "stdout": "False"}).encode('utf-8')
        )
    else:
        client_conn.send(
            str({"msg": "Thread does not exist", "stdout": "True"}).encode('utf-8')
        )


def delete_thread_message(thread_title, message_to_delete):
    read_file_fd = open(thread_title, "r")
    thread_creator = read_file_fd.read().splitlines()[0]

    current_messages = get_thread_messages(thread_title)
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


def handle_delete_message_command(client_command, username, client_conn):
    '''
    Handler for DLT command
    '''
    # Strip off the thread title and the message number
    thread_title = client_command.split(" ")[1]
    message_number = client_command.split(" ")[2]
    # Check if thread exists, then check if message exists, then check if
    # the given username was the one who created that message
    active_threads = get_active_threads()
    if thread_title in active_threads:
        thread_messages = get_thread_messages(thread_title)
        total_messages = len(thread_messages)
        message_index = int(message_number)-1
        if total_messages > message_index:
            message_creator = thread_messages[message_index].split(" ")[
                1].replace(':', '')

            if message_creator == username:
                message_to_delete = thread_messages[message_index]
                delete_thread_message(thread_title, message_to_delete)

                client_conn.send(
                    str({"msg": f"The message has been deleted",
                         "stdout": "True"}).encode('utf-8')
                )
            else:
                client_conn.send(
                    str({"msg": f"The message belongs to another user and cannot be edited",
                         "stdout": "True"}).encode('utf-8')
                )
                print("Message cannot be deleted")
        else:
            client_conn.send(
                str({"msg": f"The message does not exist in this thread",
                     "stdout": "True"}).encode('utf-8')
            )
    else:
        client_conn.send(
            str({"msg": f"Thread does not exist",
                 "stdout": "True"}).encode('utf-8')
        )


def update_thread_message(thread_title, message_to_update, message_index):
    read_file_fd = open(thread_title, "r")
    thread_creator = read_file_fd.read().splitlines()[0]

    current_messages = get_thread_messages(thread_title)
    write_file_fd = open(thread_title, "w")
    write_file_fd.write(f"{thread_creator}\n")
    index = 1
    total_messages = len(current_messages)
    for old_message in current_messages:
        if index == message_index:
            old_message_prefix = " ".join(old_message.split(" ")[0:2])
            write_file_fd.write(old_message_prefix + " " + message_to_update)
        else:
            write_file_fd.write(old_message)
        if index < total_messages:
            write_file_fd.write("\n")
        index += 1


def handle_edit_message_command(client_command, username, client_conn):
    '''
    Handler for EDT command
    '''
    # Strip off the thread title and the message number
    thread_title = client_command.split(" ")[1]
    message_number = client_command.split(" ")[2]
    updated_message = client_command.split(" ")[3:]
    # Check if thread exists, then check if message exists, then check if
    # the given username was the one who created that message
    active_threads = get_active_threads()
    if thread_title in active_threads:
        thread_messages = get_thread_messages(thread_title)
        total_messages = len(thread_messages)
        message_index = int(message_number)
        if total_messages >= message_index:
            message_to_update = " ".join(updated_message)
            message_creator = thread_messages[message_index-1].split(" ")[
                1].replace(':', '')

            if message_creator == username:
                update_thread_message(
                    thread_title, message_to_update, message_index
                )

                client_conn.send(
                    str({"msg": f"The message has been updated",
                         "stdout": "True"}).encode('utf-8')
                )
            else:
                client_conn.send(
                    str({"msg": f"The message belongs to another user and cannot be edited",
                         "stdout": "True"}).encode('utf-8')
                )
                print("Message cannot be edited")
        else:
            client_conn.send(
                str({"msg": f"The message does not exist in this thread",
                     "stdout": "True"}).encode('utf-8')
            )
    else:
        client_conn.send(
            str({"msg": f"Thread does not exist",
                 "stdout": "True"}).encode('utf-8')
        )


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
                 "stdout": "True"}).encode('utf-8')
        )
    else:
        print(active_threads)
        client_conn.send(
            str({"msg": "No threads to list", "stdout": "True"}).encode('utf-8')
        )


def handle_read_thread_command(client_command, username, client_conn):
    '''
    Handler for RDT command
    '''
    # Strip the thread title from command
    thread_title = client_command.split(" ")[1]
    # If it's part of the active threads, send the messages
    active_threads = get_active_threads()
    if thread_title in active_threads:
        thread_messages = get_thread_messages(thread_title)
        thread_messages_string = '\n'.join(thread_messages)
        client_conn.send(
            str({"msg": thread_messages_string, "stdout": "True"}).encode('utf-8')
        )
    else:
        client_conn.send(
            str({"msg": "Thread does not exist", "stdout": "True"}).encode('utf-8')
        )

    pass


def handle_upload_file_command(client_command, username, client_conn):
    '''
    Handler for UPD command
    '''
    # Strip thread title from command
    thread_title = client_command.split(" ")[1]
    # Get active threads
    active_threads = get_active_threads()
    # Check if title is in active threads
    if thread_title in active_threads:
        # Confirm the thread was found to the client, and ask them for their file
        client_conn.send(
            str({"msg": "Thread found, send file",
                 "stdout": "False"}).encode('utf-8')
        )
        # Receive username and filename from client
        response_data = client_conn.recv(1024).decode('utf-8')
        response_json = json.loads(re.sub(r"'(\S+)'", r'"\1"', response_data))
        username = response_json["username"]
        filename = response_json["filename"]

        # Confirm json was received
        client_conn.send(
            str({"msg": "Received username and filename, send file",
                 "stdout": "False"}).encode('utf-8')
        )
        # Receive file
        new_file_contents = client_conn.recv(999999).decode()
        new_file_fd = open(str(f"{thread_title}-{filename}"), "w")
        new_file_fd.write(new_file_contents)
        new_file_fd.close()

        thread_fd = open(thread_title, "a")
        thread_fd.write(str(f"\n{username} uploaded {filename}"))

        # Confirm file uploaded
        client_conn.send(
            str({"msg": str(f"{filename} uploaded to {thread_title} thread"),
                 "stdout": "True"}).encode('utf-8')
        )
        print(f"Yoda uploaded {filename} to {thread_title} thread")
    else:
        client_conn.send(
            str({"msg": str(f"{thread_title} thread does not exist"),
                 "stdout": "True"}).encode('utf-8')
        )


def handle_download_file_command(client_command, username, client_conn):
    '''
    Handler for DWN command
    '''
    # Strip thread title and filenme from command
    thread_title = client_command.split(" ")[1]
    filename = client_command.split(" ")[2]
    # Get active threads
    active_threads = get_active_threads()
    # Check if title is in active threads
    if thread_title in active_threads:
        # check if the file exists in thread
        server_files = os.listdir()
        server_filename = str(f"{thread_title}-{filename}")
        if server_filename in server_files:
            thread_file_contents = open(server_filename, "r").read()
            data_json = str({"filename": filename,
                             "contents": thread_file_contents, "stdout": "False"})
            client_conn.send(data_json.encode('utf-8'))
            print(f"{filename} downloaded from {thread_title} thread")
        else:
            client_conn.send(
                str({"msg": str(f"File does not exist in {thread_title} thread"),
                     "stdout": "True"}).encode('utf-8')
            )
            print(f"{filename} does not exist in {thread_title} thread")
    else:
        client_conn.send(
            str({"msg": str(f"{thread_title} thread does not exist"),
                 "stdout": "True"}).encode('utf-8')
        )


def handle_remove_thread_command(client_command, username, client_conn):
    '''
    Handler for RMV command
    '''
    # Strip thread title from command
    thread_title = client_command.split(" ")[1]
    # Get the active threads
    active_threads = get_active_threads()
    # If in active thread, remove, otherwise send error
    if thread_title in active_threads:
        os.remove(thread_title)
        server_files = os.listdir()
        for file in server_files:
            if thread_title in file:
                os.remove(file)
        print("Thread %s removed" % thread_title)

        client_conn.send(
            str({"msg": "Thread %s removed" %
                 thread_title, "stdout": "True"}).encode('utf-8')
        )
    else:
        client_conn.send(
            str({"msg": "Thread does not exist", "stdout": "True"}).encode('utf-8')
        )


def handle_exit_command(client_command, username, client_conn):
    '''
    Handler for XIT command
    '''
    client_conn.send(
        str({"msg": "Goodbye", "stdout": "True"}).encode('utf-8')
    )
    return False


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
    return_state = COMMAND_SWITCH[command_selection[0:3]](
        command_selection, username, client_conn
    )
    if return_state == False:
        return False
    else:
        # Return confirmation from client
        return client_conn.recv(1024).decode('utf-8')

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
                _ = client_conn.recv(1024).decode('utf-8')

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
