#!/usr/bin/python3
# -*- coding: utf-8 -*-

# usage:
# python Sender.py RECEIVER_IP RECEIVER_PORT FILE_SENT MWS MSS GAMMA P_DROP P_DELAY MAX_DELAY SEED

import sys
import time
from socket import *
from copy import copy
import threading


from packet import *
from infrastructures import *


LOCALHOST = '127.0.0.1'
SENDER_IP = '127.0.0.1'
RECIVER_IP = '127.0.0.1'
SENDER_PORT = 9331
RECEIVER_PORT = 3331
MWS = 1000  # Maximum Window Size
MSS = 8  # Maximum Segment Size
TIMEOUT = 500
FILE_SENT = 'test.txt'
SEED = 0  # random seed for PLD module
LOG_NAME = 'Sender_log.txt'
GAMMA = 4
P_DROP = 0
P_DELAY = 0
MAX_DELAY = 500

SENDER_STATUS = {
                        0: 'closed', 
                        1: 'syn sent',
                        2: 'connection established',
                        3: 'FIN_WAIT_1',
                        4: 'FIN_WAIT_2',
                    }


class Sender:
    def __init__(self, source_ip=SENDER_IP, source_port=SENDER_PORT,\
                 dest_ip=RECIVER_IP, dest_port=RECEIVER_PORT):
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.sender = socket(AF_INET, SOCK_DGRAM)
        # self.sender.bind((source_ip, source_port))
        self.sender.connect((dest_ip, dest_port))
        print(f"{dest_ip}:{dest_port}")
        # self.sender.settimeout(TIMEOUT/1000)
        self.ack_num = 0
        self.seq_num = 0
        self.status = 0
        self.window = SenderWindow()
        self.reorder = None
        #This is to give a port in input_window for MAX_ORDER
        self.order_eta = MAX_ORDER
        self.pld = PLD(SEED, P_DROP, P_DELAY, MAX_DELAY)
        self.logger = Logger(LOG_NAME)
        self.e_RTT = 0  # estimated RTT
        self.d_RTT = 0  # devRTT
        self.timeout_interval = 1
        self.resending = False

    def establish(self):
        header = Header()
        self.isn = header.isn
        self.seq_num = self.isn
        header.syn = 1
        send_packet(self.sender, header, logger=self.logger)  # 1st handshake

        received_header, received_data, dest_ip, dest_port, received_time = \
                                        receive_packet(self.sender, self.logger)

        if received_header.syn == 1 and received_header.ack == 1:
            print('establishment request acked from {}:{}'.format(dest_ip, dest_port))
            header.syn = 0
            header.ack = 1
            self.ack_num = received_header.seq_num + 1
            header.ack_num = self.ack_num
            header.seq_num = received_header.ack_num
            self.seq_num = header.seq_num
            send_packet(self.sender, header, logger=self.logger)  # 3rd handshake

            self.status = 2
            return True

    def close(self):
        header = Header()
        header.fin = 1
        header.seq_num = self.seq_num
        header.ack_num = self.ack_num
        send_packet(self.sender, header, logger=self.logger)
        print('connection to {}:{} closing'.format(self.dest_ip, self.dest_port))
        received_header, received_data, dest_ip, dest_port, received_time = \
                        receive_packet(self.sender, self.logger)

        print(received_header.ack, received_header.ack_num, self.seq_num)
        if received_header.ack == 1 and received_header.ack_num == self.seq_num + 1:
            self.status = 3
            received_header, received_msg, dest_ip, dest_port, received_time = \
                            receive_packet(self.sender, self.logger)
            print('connection to {}:{} closed'.format(dest_ip, dest_port))
            header = Header()
            header.ack = 1
            self.ack_num = received_header.seq_num + 1
            header.ack_num = self.ack_num
            send_packet(self.sender, header, logger=self.logger)
            self.sender.close()
        self.logger.sender_conclude()

    def send_data(self, file):
        self.transmitting = True
        reading_file = True
        f = open(file, 'rb')

        sending_thread = Thread('sender', self)
        receiving_thread = Thread('receiver', self)
        self.lock = threading.Lock()

        sending_thread.start()
        receiving_thread.start()

        while self.transmitting:
            #print(self.window)
            self.lock.acquire()
            while reading_file and len(self.window) < MWS:
                data = f.read(MSS)
                if len(data) == 0:
                    reading_file = False
                    break
                self.window[self.seq_num] = {'data': data, 'status': 0}
                self.seq_num += len(data)
            self.lock.release()

            if len(self.window) == 0 and not reading_file:
                self.transmitting = False
        return

    def _sending_data_thread(self):
        while self.transmitting:
            for seq_num in list(self.window.keys()):
                if self.resending:
                    self.resending = False
                    break
                segment = self.window.get(seq_num)
                print("\n\n\n segment{}\n\n\n".format(segment))
                if segment is None:
                    continue
                sent_time = segment.get('time')
                print("\n\n\n sent_time{}\n\n\n".format(sent_time))
                sent_status = segment.get('status')
                print("\n\n\n sent_status{}\n\n\n".format(sent_status))
                # if sent_time is not None:
                #     print(time.time(), sent_time, time.time() - sent_time, TIMEOUT / 1000)
                # status 状态参数
                if not sent_status == 1 and (sent_time is None or time.time() - sent_time > self.timeout_interval):
                    # 这个包从未发送过
                    if sent_time is None:
                        self.logger.num_segments += 1
                    # 已经发送过，发送时间， 没有启动快速重传
                    if sent_time is not None and time.time() - sent_time > self.timeout_interval and sent_time != -1:
                        # 快送重传
                        if sent_time == -1:
                            print('fast-retransmit')
                            # calcu
                        else:
                            # 超时
                            print('time out, {} {} {} {}'.format(time.time(), sent_time, time.time() - sent_time, self.timeout_interval))
                            # calcu

                        self.timeout_interval *= 2
                        # 重传加+1
                        self.logger.retransmit += 1
                        #  字典中时间参数不为空
                    if segment.get('time'):
                        # 启动重传
                        segment['retransmit'] = True

                    header = Header()
                    header.seq_num = seq_num
                    header.ack_num = self.ack_num
                    segment['time'] = time.time()

                    category = send_packet(self.sender, header, segment['data'], self.pld, logger=self.logger)
                    # is loss = True
                    if category:

                        # what is reorder
                        # self.reorder = alsj
                        self.reorder = ['packet.msg']
                        if self.reorder is not None:
                            self.order_eta -= 1
                            if self.order_eta == 0:
                                send_packet(self.sender, header, segment['data'], None, logger=self.logger)

    def _receiving_data_thread(self):
        dup_seq = None
        dup_count = 0

        while self.transmitting:
            print('!!!\n', self.timeout_interval)
            received_header, _, _, _, received_time =\
                                receive_packet(self.sender, self.logger)
            ack = received_header.ack_num
            if not len(self.window) > 0:
                continue

            head_seq, expected_ack = self.window.head()
            print('self.window.head()==-=-=-=-=-=-\n',  head_seq, expected_ack)
            if ack == expected_ack:
                segment = self.window[head_seq]
                segment['status'] = 1
                if not segment.get('retransmit'):
                    # EstimatedRTT = (1 –  a) * EstimatedRTT +  a * SampleRTT
                    # DevRTT = (1 –  b) * DevRTT +  b * | SampleRTT – EstimatedRTT |
                    # TimeoutInterval = EstimatedRTT + GAMMA * DevRTT
                    s_RTT = round(received_time - segment['time'], 3) # sample_rtt
                    print(s_RTT, received_time, segment['time'])
                    self.e_RTT = 0.875 * self.e_RTT + 0.125 * s_RTT
                    self.d_RTT = 0.875 * self.d_RTT + 0.125 * abs(s_RTT - self.e_RTT)
                    self.timeout_interval = (self.e_RTT + GAMMA * self.d_RTT)

            elif ack < expected_ack:
                if dup_seq is None:
                    dup_seq = ack
                    dup_count = 1
                    self.logger.dup_count += 1
                elif dup_seq == ack:
                    dup_count += 1
                    self.logger.dup_count += 1
                else:
                    dup_seq = ack
                    dup_count = 1
                if dup_count >= 3:
                    dup_seq = None
                    self.window[head_seq]['time'] = -1
                    print("resending...%s" % head_seq)
                    self.resending = True
                    continue
            elif ack > head_seq:
                self.lock.acquire()
                for seq_num_in_window, seq_in_window in self.window.items():
                    if seq_num_in_window + len(seq_in_window['data']) <= ack:
                        seq_in_window['status'] = 1
                self.lock.release()


if __name__ == '__main__':
    RECEIVER_IP = "127.0.0.1"
    RECEIVER_PORT = 3331
    FILE_SENT = "test.txt"
    MWS = 1000
    MSS = 100
    GAMMA = 1
    P_DROP = 0.5
    PDuplicate = 0
    PCorrupt = 0
    POrder = 0
    MAX_ORDER = 0
    P_DELAY = 0
    MAX_DELAY = 0
    SEED = 0
    a = time.time()
    sender = Sender()
    sender.establish()
    sender.send_data(FILE_SENT)
    print('data transfering finished')
    sender.close()
    b = time.time()
    print(b-a)

