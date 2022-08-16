"""
COMP9331-21T2-Lab2-Exercise 5
Haojin Guo
z5216214
21,6,2021

UDP-Client

The used Python version is Python 3.7.7

"""

import sys
import socket
import time
from datetime import datetime
import numpy as np

client_ip = sys.argv[1]
client_port = int(sys.argv[2])

# address = ('127.0.0.1', 8000)

# #SOCK_DGRAM --> UDP，SOCKET_STREAM --> TCP
sock_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

RTT_list = []
lost_packet = 0

start_num = 3331
end_num = 3345


def check_time(start_num, sock_UDP, time_request):
    try:
        sock_UDP.settimeout(0.6)
        response_data, sever_address = sock_UDP.recvfrom(1024)
        time_response = datetime.now()
        rtt = round((time_response - time_request).total_seconds() * 1000)
        sock_UDP.settimeout(None)
    except socket.timeout:
        return None
    else:
        return rtt


def for_timeout(client_ip, start_num):
    timeout_msg = f"Ping to {client_ip}, seq = {start_num}, rtt = time out"
    print(timeout_msg)


# 3331 to 3345,  send 15 pings to the server
while start_num <= end_num:

    time_start = datetime.now()
    time_start = str(time_start)

    ping_msg = f'PING{start_num} -- {time_start}\r\n'

    time_request = datetime.now()

    sock_UDP.sendto(ping_msg.encode("UTF-8"), (client_ip, client_port))

    rtt_ = check_time(start_num, sock_UDP, time_request)

    if rtt_:

        RTT_list.append(rtt_)
        output_msg = f"Ping to {client_ip}, seq = {start_num}, rtt = {rtt_} ms"
        print(output_msg)
    else:
        lost_packet += 1
        for_timeout(client_ip, start_num)

    start_num = start_num + 1

sock_UDP.close()
print()
print(f'In 15 packets, there are {15 - int(lost_packet)} packets received.')

RTT = np.array(RTT_list)
print(f"The minimum RTT is {RTT.min()} ms")
print(f"The maximum RTT is {RTT.max()} ms")
print(f"The average RTT is {round(RTT.mean())} ms")
