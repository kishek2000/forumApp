# forumApp

A network application written in python that imitates a forum system.

## Classes

In this network, the key classes that I use are:

- For the server:
  - ClientThread()
    - This creates a new thread for each client connection made to the server, and runs the services for it
  - Server()
    - This is where we manage connections made by clients and handle their forum commands
- For the client:
  - Client()
    - This simply forms a connection and sends commands, receives responses for them
- For both:
  - Command()
    - This is the base class for any given forum command
  - CommandUtils()
    - This is a class that stores util functions used by all forum commands
