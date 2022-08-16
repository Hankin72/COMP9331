from ass_demo import PTPSocket

if __name__ == "__main__":
    server_socket = PTPSocket.PTPSocket()

    server_socket.bind(('127.0.0.1', 10893))
    server_socket.listen()

    socket = server_socket.accept()

    # socket.close()

