import socket                

s = socket.socket()          
port = 12345                
  
# Next bind to the port 
# we have not typed any ip in the ip field 
# instead we have inputted an empty string 
# this makes the server listen to requests  
# coming from other computers on the network 
s.bind(('', port))         
print ("Waiting for clients") 
  
# put the socket into listening mode 
s.listen(5)      
  
# a forever loop until we interrupt it or  
# an error occurs 
while True: 
  
    # Establish connection with client. 
    c, addr = s.accept()      
    print("Client connected")
    
    ## Await successful authentication
    is_authenticated = False
    authenticated_username = ""
    while True:
        authentication_status = c.recv(1024).decode('utf-8')
        if authentication_status != "unsuccessful":
            authenticated_username = authentication_status
            print(authentication_status, "successful login")
            is_authenticated = True
            break
        else:
            print("Incorrect password")
  
    if (is_authenticated):
        ## Send a welcome message to the client for the forum  
        c.send(str('Welcome to the forum.\n\
                    Enter one of the following commands: \
                    CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT: '
        ).encode('utf-8'))
        ## Receive option by client
        selection = c.recv(1024).decode('utf-8')
        ## Print client operation
        print(authentication_status, "issued", selection, "command")
  
    # Close the connection with the client 
    c.close() 