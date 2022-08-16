import time
import threading
import socket as sk
import sys
import queue

from PTPPacket import Packet, Log

STATE = {
    0: 'CLOSED',
    1: 'LISTEN',
    2: 'SYN-RCVD',
    3: 'ESTABLISHED',
    4: 'CLOSED-WAIT',
    5: 'LAST-ACK',
}


class Server:
    def __init__(self):
        self.receiver_port = int(sys.argv[1])
        self.FileReceived = str(sys.argv[2])
        with open(self.FileReceived, 'a+', encoding='utf-8') as test:
            test.truncate(0)

        self.log_filename = 'Receiver_log.txt'
        with open(self.log_filename, 'a+', encoding='utf-8') as test:
            test.truncate(0)
        self.log = Log(self.log_filename)

        self.receiver_address = ('127.0.0.1', self.receiver_port)
        self.source_address = ('127.0.0.1', 0)

        self.UDP_Server_socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

        self.is_server = False
        self.state = 0

        self.recv_buffer = queue.Queue()
        self.temp_buffer = {}

        self.init_seq_num = 0
        self.acknowledged_num = 0
        self.close_flag = False
        self.time_send = 0.0
        self.time_recv = 0.0

        threading.Thread(target=self.state_threading).start()

    def state_threading(self):
        while not self.close_flag:
            print(STATE[int(self.state)])
            time.sleep(1)

    def listen(self):
        self.UDP_Server_socket.bind(self.receiver_address)
        self.is_server = True
        self.state = 1

    def recv_data_threading(self):
        while True:
            if not self.is_server:
                continue
            try:
                packet = self._recv()
            except OSError:
                return

            if self.state == 0:
                pass
            elif self.state == 1:
                if packet.SYN:
                    syn = packet
                    self.log.log_edit(m_type='rcv', packet=syn,
                                      end_time=self.time_recv, num_of_bytes=0, is_send=False)

                    synack = Packet(ACK=1, SYN=1)
                    # synack.seq_num =  0
                    synack.seq_num = self.init_seq_num
                    synack.ack_num = syn.seq_num + 1
                    self._send(synack)
                    self.log.log_edit(m_type='snd', packet=synack,
                                      end_time=self.time_send, num_of_bytes=0, is_send=False)

                    self.init_seq_num = synack.ack_num
                    self.acknowledged_num = self.init_seq_num+1

                    self.state = 2
            elif self.state == 2:
                if packet.ACK:
                    ack = packet
                    self.log.log_edit(m_type='rcv', packet=ack,
                                      end_time=self.time_recv, num_of_bytes=0, is_send=False)
                    self.state = 3
                    print(STATE[3] + ' successful ' + ' ...\n')

            elif self.state == 3:
                if packet.ACK and packet.Data:
                    segment = packet
                    self.log.log_edit(m_type='rcv', packet=segment,
                                      end_time=self.time_recv, num_of_bytes=len(segment.data), is_send=False)
                    print(f"Start to receive the data: "
                          f",from port num: {segment.src_port} to des-port-num {segment.des_port} ================")

                    print('recv from client ===================')
                    # print(segment)
                    if segment.seq_num in self.temp_buffer or segment.seq_num < self.acknowledged_num:
                        self.log.dup_count += 1

                    if segment.seq_num == self.acknowledged_num:
                        self.acknowledged_num = segment.seq_num + len(segment.data)
                        self.recv_buffer.put(segment.data)

                        if len(self.temp_buffer) > 0:
                            # next expected seq_num from sender
                            next_expected_seq_num = segment.seq_num + len(segment.data)
                            while next_expected_seq_num in self.temp_buffer:

                                next_data = self.temp_buffer[next_expected_seq_num]
                                self.recv_buffer.put(next_data)

                                self.temp_buffer.pop(next_expected_seq_num)

                                next_expected_seq_num += len(next_data)
                                self.acknowledged_num += len(next_data)

                    if segment.seq_num > self.acknowledged_num:
                        self.temp_buffer[segment.seq_num] = segment.data
                        print(self.temp_buffer)

                    ack_reply = Packet(ACK=1)
                    ack_reply.ack_num = self.acknowledged_num
                    ack_reply.seq_num = self.init_seq_num
                    self._send(ack_reply)
                    # self.log.log_edit(m_type='snd', packet=ack_reply,
                    #                   end_time=self.time_send, num_of_bytes=0, is_send=False)
                    print('send  ACK to  client ===================')

                elif packet.FIN:
                    while self.recv_buffer.qsize() > 0:
                        file = open(self.FileReceived, 'ab')
                        data = self.recv_buffer.get()
                        self.log.data_size += 1 * len(data)
                        self.log.num_packets += 1
                        file.write(data)
                    print(self.temp_buffer)

                    print('1*' * 100)
                    print("start closing the connection ------------------------------- ")
                    # print("recv fin1 <<<<<<<<<<<<<<<<<<<<<<<< ")
                    fin1 = packet
                    self.log.log_edit(m_type='rcv', packet=fin1,
                                      end_time=self.time_recv, num_of_bytes=0, is_send=False)

                    ack1 = Packet(ACK=1)
                    ack1.seq_num = self.init_seq_num
                    ack1.ack_num = fin1.seq_num + 1
                    # print("send ack1  >>>>>>>>>>>>>>>>>>>>>>>>>> ")
                    self._send(ack1)
                    self.log.log_edit(m_type='snd', packet=ack1,
                                      end_time=self.time_send, num_of_bytes=0, is_send=False)
                    self.state = 4

                    fin2 = Packet(FIN=1, ACK=1)
                    fin2.seq_num = self.init_seq_num + 1
                    fin2.ack_num = fin1.seq_num + 1
                    self._send(fin2)
                    self.log.log_edit(m_type='snd', packet=fin2,
                                      end_time=self.time_send, num_of_bytes=0, is_send=False)
                    # print("send fin2 + ack1 >>>>>>>>>>>>>>>>>>>>>>>>>> ")
                    self.state = 5

            elif self.state == 5:
                ack2 = packet
                if packet.ACK:
                    # print("recv ack2  <<<<<<<<<<<<<<<<<<<<<<<<")

                    self.log.log_edit(m_type='rcv', packet=ack2,
                                      end_time=self.time_recv, num_of_bytes=0, is_send=False)

                    self.state = 0
                    self.UDP_Server_socket.close()
                    self.log.receiver_rst()
                    print("Connection Closed --------------------------- ")

    def _send(self, packet):
        packet.src_port = self.receiver_address[1]
        packet.des_port = self.source_address[1]
        self.UDP_Server_socket.sendto(packet.encode(), self.source_address)
        self.time_send = time.time()
        # print("Server send: ... ")

    def _recv(self):
        data_bytes, address = self.UDP_Server_socket.recvfrom(1024)
        self.time_recv = time.time()
        self.source_address = address
        packet = Packet.decode(data_bytes)

        # print("Server recv:  .. ")

        return packet

    def accept(self):
        while self.state != 3:
            #  阻塞
            pass
        # 返回自身，
        return self


if __name__ == '__main__':
    server_socket = Server()

    # server_socket.FileReceived = 'FileReceived.txt'
    a = time.time()
    server_socket.listen()

    server_socket.recv_data_threading()

    time.sleep(0.5)
    server_socket.close_flag = True

    b = time.time()

    print("\nTotal time cost {:.3f}s. \n".format(b - a))
