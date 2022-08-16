from ass_demo import PTPSocket

if __name__ == "__main__":
    client_socket = PTPSocket.PTPSocket()

    client_socket.connect(('127.0.0.1', 10893))

    # client_socket.send()

    client_socket.close()
