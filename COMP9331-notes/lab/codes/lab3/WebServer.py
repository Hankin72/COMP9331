"""
COMP9331-21T2-Lab3-Exercise 4
Haojin Guo
z5216214
28,6,2021

TcpServer

The used Python version is Python 3.7.7

"""
#
# coding: utf-8
from socket import *
import socket as sk
import sys
import matplotlib.pyplot as plt

BUFFER_SIZE = 2048


def valid_(message, connectionSocket):
    filename = message.split("\n")[0].split(" ")[1][1:]

    try:
        with open(filename, 'rb') as f_pbj:
            content = f_pbj.read()
        if 'html' in filename:
            response = "HTTP/1.1 200 OK\r\nContent_Type: text/html\r\n\r\n"
        elif 'png' in filename:
            response = "HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n"

        connectionSocket.sendall(response.encode())
        connectionSocket.sendall(content)
        connectionSocket.close()

    except FileNotFoundError:
        return False
    else:
        return True


def unvalid_(connectionSocket):
    response = "HTTP/1.1 404 File not found\r\n\r\n"
    response = response.encode()
    content = "<h1><center><center> 404 Error: File not found! </center></center></h1>"
    content = content.encode()
    connectionSocket.sendall(response)
    connectionSocket.sendall(content)
    connectionSocket.close()


def main():
    local_host = "127.0.0.1"
    PortNumber = int(sys.argv[1])
    # #SOCK_DGRAM --> UDP，SOCKET_STREAM --> TCP
    serverSocket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)

    serverSocket.bind((local_host, PortNumber))
    # the socket is bound to the address of AF_INET, by the form of tuple(localhost, port).

    serverSocket.listen(5)
    # The serverSocket then goes in the listen state to listen for client connection requests.
    print("The server is ready to receive ... ")
    print()

    try:
        while 1:
            connectionSocket, addr = serverSocket.accept()

            msg = connectionSocket.recv(BUFFER_SIZE).decode()
            print(msg)

            valid_request = valid_(msg, connectionSocket)
            if not valid_request:
                unvalid_(connectionSocket)
    except KeyboardInterrupt:
        print("Finish the attempt! ")


if __name__ == "__main__":
    main()
