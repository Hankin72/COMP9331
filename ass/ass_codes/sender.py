import time
import threading
import socket as sk
import sys
import queue
import collections
from PTPPacket import Packet, Log
import random


class PLModule:
    def __init__(self, seed):
        if seed is not None:
            random.seed(seed)
            self.loss = random.random
        else:
            def loss(self):
                return 1
        return


STATE = {
    0: 'CLOSED',
    1: 'SYN-SENT',
    2: 'ESTABLISHED',
    3: 'FIN-WAIT-1',
    4: 'FIN-WAIT-2',
    5: 'TIME-WAIT',
}


class Client:
    def __init__(self):
        self.receiver_ip = str(sys.argv[1])
        self.receiver_port = int(sys.argv[2])
        self.FileToSend = str(sys.argv[3])
        # 最大窗口
        self.MWS = int(sys.argv[4])

        # 最大的传输数据量
        self.MSS = int(sys.argv[5])
        self.TIMEOUT = int(sys.argv[6])
        self.p_drop = float(sys.argv[7])
        self.seed = int(sys.argv[8])

        self.pld = PLModule(self.seed)

        self.log_filename = 'Sender_log.txt'

        with open(self.log_filename, 'a+', encoding='utf-8') as test:
            test.truncate(0)

        self.log = Log(self.log_filename)
        self.source_ip_port = ('127.0.0.1', 0)
        self.receiver_address = ('127.0.0.1', self.receiver_port)
        self.UDP_Client_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.send_buffer = queue.Queue()
        self.init_seq_num = 0
        self.sequence_number = 2
        self.state = 0

        self.close_flag = False
        self.is_using_close = True

        self.time_send = 0.0
        self.time_recv = 0.0
        self.sent_packets = 0
        self.recv_ack = 0

        self.length = int(self.MWS / self.MSS)
        self.m = int(self.length / 2)
        self.n = self.length - self.m
        self.window_unsent = collections.deque(maxlen=self.m)

        self.window_unacked = collections.deque(maxlen=self.n)

        self.transmitting = False
        self.reading_file = False
        self.resending = False

        self.temp_seq = None
        self.temp_count = 0

        self.time_start = 0.0
        self.TimeoutInterval = 1.0
        self.e_RTT = 0  # estimated RTT
        self.d_RTT = 0  # # devRTT

        self.lock = threading.Lock()
        threading.Thread(target=self.state_threading).start()

    def state_threading(self):

        while not self.close_flag:
            print(STATE[int(self.state)])
            time.sleep(1)

    def connection(self):
        print("Start connecting ... \n")
        syn = Packet(SYN=1)
        syn.seq_num = self.init_seq_num
        self.send_(syn)
        self.log.log_edit(m_type='snd', packet=syn,
                          end_time=self.time_send, num_of_bytes=0)

        self.state = 1
        synack = self.recv_()
        if synack.ACK and synack.SYN:
            self.log.log_edit(m_type='rcv', packet=synack,
                              end_time=self.time_recv, num_of_bytes=0)
            ack = Packet(ACK=1)
            ack.seq_num = synack.ack_num
            ack.ack_num = synack.seq_num + 1
            self.send_(ack)
            self.log.log_edit(m_type='snd', packet=ack,
                              end_time=self.time_send, num_of_bytes=0)
            self.state = 2
            print(STATE[2] + ' successful ' + ' ...\n')
            self.init_seq_num = ack.ack_num + 1

    def close(self):

        print("start closing the connection ------------------------------- ")
        fin1 = Packet(FIN=1)
        fin1.seq_num = self.init_seq_num
        fin1.ack_num = 1
        self.send_(fin1)
        self.log.log_edit(m_type='snd', packet=fin1,
                          end_time=self.time_send, num_of_bytes=0)
        self.state = 3
        ack1 = self.recv_()
        if ack1.ACK:
            self.log.log_edit(m_type='rcv', packet=ack1,
                              end_time=self.time_recv, num_of_bytes=0)
            self.state = 4
            fin2 = self.recv_()
            if fin2.FIN and fin2.ACK:
                self.log.log_edit(m_type='rcv', packet=fin2,
                                  end_time=self.time_recv, num_of_bytes=0)

                ack2 = Packet(ACK=1)
                ack2.seq_num = fin2.ack_num
                ack2.ack_num = fin2.seq_num + 1
                self.send_(ack2)
                self.log.log_edit(m_type='snd', packet=ack2,
                                  end_time=self.time_send, num_of_bytes=0)
                self.state = 5
                time.sleep(2 * self.TIMEOUT / 1000)
                self.state = 0
                self.UDP_Client_socket.close()
                self.log.sender_rst()
                print("Connection Closed --------------------------- ")

    def send_data(self):
        print("\nStart to transmit the data ..........")
        self.transmitting = True
        self.reading_file = True
        file = open(self.FileToSend, 'rb')
        thread_send = threading.Thread(target=self.send_data_threading)
        thread_send.setDaemon(True)
        thread_recv = threading.Thread(target=self.recv_data_threading)
        thread_recv.setDaemon(True)
        thread_send.start()
        thread_recv.start()
        while self.transmitting:
            self.lock.acquire()
            while self.reading_file and len(self.window_unsent) < self.m:

                data = file.read(self.MSS)
                if len(data) == 0:
                    self.reading_file = False
                    break
                self.log.data_size += len(data)
                self.log.num_packets += 1
                self.window_unsent.append((self.sequence_number, data, 0))
                self.sequence_number += len(data)

            self.lock.release()
            if len(self.window_unsent) == 0 and len(self.window_unacked)==0 and  not self.reading_file:
                time.sleep(0.5)
                self.transmitting = False
                print('1*' * 100)

    def send_data_threading(self):
        while self.transmitting:
            while len(self.window_unsent) > 0:
                item = self.window_unsent[0]
                seq_number = item[0]
                data = item[1]
                status = item[2]

                if status == 1:
                    self.log.retransmit += 1

                packet = Packet(ACK=1, Data=1)
                packet.seq_num = seq_number
                packet.ack_num = 1
                packet.data = data
                if self.pld is not None:
                    loss = self.pld.loss()
                    if loss > self.p_drop:
                        print("send data --------->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        self.send_(packet)
                        self.time_start = time.time()
                        self.log.log_edit(m_type='snd', packet=packet,
                                          end_time=self.time_send, num_of_bytes=len(packet.data))
                        self.window_unacked.append((seq_number,data,0))
                        self.window_unsent.popleft()
                    else:
                        self.log.pck_loss += 1
                        self.log.log_edit(m_type='drop', packet=packet,
                                          end_time=self.time_send, num_of_bytes=len(packet.data))

    def recv_data_threading(self):
        while self.transmitting:
            while len(self.window_unacked) > 0:
                # sorted(self.window_unacked, key=lambda x: x[0])
                try:
                    ack_packet = self.recv_()
                except OSError:
                    return
                self.log.log_edit(m_type='rcv', packet=ack_packet,
                                  end_time=self.time_recv, num_of_bytes=0)

                print("recv data <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<---------------")
                # print(ack_packet)
                ack = ack_packet.ack_num

                item = self.window_unacked[0]
                seq_number = item[0]
                data = item[1]
                status = item[2]
                expected_ack = seq_number + len(data)

                if (time.time() - self.time_start) > self.TIMEOUT / 1000:
                    print("Timeout Retransmitting {}".format('='))
                    self.log.retransmit +=1
                    self.TimeoutInterval *= 2

                if ack == expected_ack and len(self.window_unacked) > 0:
                    self.window_unacked.popleft()

                    s_RTT = round(self.time_recv - self.time_start, 3)  # sample_rtt
                    # print(s_RTT, self.time_recv, self.time_start)
                    self.e_RTT = 0.875 * self.e_RTT + 0.125 * s_RTT
                    self.d_RTT = 0.875 * self.d_RTT + 0.125 * abs(s_RTT - self.e_RTT)
                    self.TimeoutInterval = (self.e_RTT + 4 * self.d_RTT)

                    # self.window_unacked.remove((seq_number, data, status))
                elif ack < expected_ack:
                    if self.temp_seq is None:
                        self.temp_count = 1
                        self.log.dup_ack += 1

                    elif self.temp_seq == ack:
                        self.temp_count += 1
                        self.log.dup_ack += 1
                    else:
                        self.temp_seq = ack
                        self.temp_count = 1
                    if self.temp_count >= 3:
                        self.temp_seq = None
                        print("Fast Retransmitting {}\n".format('=' * 50))
                        self.log.retransmit += 1

                elif ack > seq_number and len(self.window_unacked) > 0:
                    self.lock.acquire()
                    for item in self.window_unacked:
                        if ack >= item[0] + len(item[1]):
                            self.window_unacked.popleft()
                    self.lock.release()

    def send_(self, packet):
        """send packet here"""
        packet.src_port = self.source_ip_port[1]
        packet.des_port = self.receiver_address[1]
        self.UDP_Client_socket.sendto(packet.encode(), self.receiver_address)
        self.time_send = time.time()

    def recv_(self):
        """recv packet"""
        data_bytes, address = self.UDP_Client_socket.recvfrom(2048)
        self.time_recv = time.time()
        self.receiver_address = address
        packet = Packet.decode(data_bytes)
        return packet


if __name__ == '__main__':
    client_socket = Client()

    # client_socket.MSS = 40
    # client_socket.MWS = 1000
    # client_socket.FileToSend = '256KB.txt'
    #
    # client_socket.TIMEOUT = 500
    # client_socket.p_drop = 0.2
    # client_socket.seed = 100
    a = time.time()
    client_socket.connection()

    client_socket.send_data()
    print(client_socket.TimeoutInterval)

    client_socket.close()

    time.sleep(0.5)
    client_socket.close_flag = True
    b = time.time()

    print("\nTotal time cost {:.3f}s. \n".format(b-a))
