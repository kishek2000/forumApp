# Import socket module 
import socket                

# Create a socket object 
s = socket.socket()          
  
# Define the port on which you want to connect 
port = 12345                

# connect to the server on local computer 
s.connect(('127.0.0.1', port)) 

def find_credentials(username, password):
    users_file_descriptor = open("credentials.txt", "r")
    users_credentials = users_file_descriptor.read()
    users_credentials = users_credentials.splitlines()
    for line in users_credentials:
        if line == f"{username} {password}":
            return True
    return False


is_authenticated = False
while (True):
    username = input("Enter username: ")
    password = input("Enter password: ")

    if (find_credentials(username, password)):
        s.sendall(str(username).encode('utf-8'))
        is_authenticated = True
        break
    else:
        print("Invalid Password")
        s.send(str("unsuccessful").encode('utf-8'))

if (is_authenticated):
    ## Receive forum options from server, and select one
    forum_options = s.recv(1024).decode('utf-8')
    option_choice = input(str(forum_options))
    print(option_choice)
    ## Send choice by client to server
    s.send(str(option_choice).encode('utf-8'))


# close the connection 
s.close()