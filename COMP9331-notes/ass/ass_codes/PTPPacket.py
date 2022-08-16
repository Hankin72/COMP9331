import time
import threading
import json
import pickle


class Packet:
    def __init__(self, ACK=0, SYN=0, FIN=0, Data=0):
        # header data
        self.src_port = 0
        self.des_port = 0
        self.seq_num = 0
        self.ack_num = 0
        self.time = 0

        # init flags
        self.ACK = ACK
        self.SYN = SYN
        self.FIN = FIN
        self.Data = Data

        # data
        self.data = None

    def encode(self):
        dict_ = {}
        dict_['src_port'] = self.src_port
        dict_['des_port'] = self.des_port
        dict_['seq_num'] = self.seq_num
        dict_['ack_num'] = self.ack_num
        dict_['ACK'] = self.ACK
        dict_['SYN'] = self.SYN
        dict_['FIN'] = self.FIN
        dict_['Data'] = self.Data
        dict_['data'] = self.data
        dict_['time'] = self.time
        bytes_dict = pickle.dumps(dict_)

        return bytes_dict

    def __str__(self):
        s = "_______________________\n"
        s += "|{:^10}|{:^10}|\n".format('src_port', 'des_port')
        s += "_______________________\n"
        s += "|{:^10d}|{:^10d}|\n".format(self.src_port, self.des_port)
        s += "|{:^10}|{:^10}|\n".format('seq_num', 'ack_num')
        s += "_______________________\n"
        s += "|{:^10d}|{:^10d}|\n".format(self.seq_num, self.ack_num)
        s += "_______________________\n"
        s += "|{:^5}{:^5}{:^5}{:^5}|\n".format('ACK', 'SYN', 'FIN', 'Data')
        s += "|{:^5}{:^5}{:^5}{:^5}|\n".format(self.ACK, self.SYN, self.FIN, self.Data)
        s += "-----------------------\n"
        s += str(self.data) + "\n"
        s += "__________time_____________\n"
        s += str(self.time)
        return s

    @staticmethod
    def decode(data):
        packet = Packet()
        temp = pickle.loads(data)
        packet.src_port = temp['src_port']
        packet.des_port = temp['des_port']
        packet.seq_num = temp['seq_num']
        packet.ack_num = temp['ack_num']
        packet.ACK = temp['ACK']
        packet.SYN = temp['SYN']
        packet.FIN = temp['FIN']
        packet.Data = temp['Data']
        packet.data = temp['data']
        packet.time = temp['time']
        return packet


class Log():
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'w')
        self.file.write('<msg_type>  <time>  <packet_type>  <seq>  <size>  <ack>\n')
        self.data_size = 0
        self.num_packets = 0
        self.pck_loss = 0

        self.retransmit = 0
        self.dup_count = 0
        self.dup_ack = 0
        self.re_recv = 0
        self.start_time = time.time()

        # self.snd = []
        # self.rcv = []

    def log_edit(self, m_type=None, packet=None, end_time=0.0, num_of_bytes=0, is_send=True, is_loss=False):

        # self.file.close()
        # if is_loss:
        #     packet_type = 'drop'
        # else:
        if packet.ACK:
            if packet.SYN:
                packet_type = 'SA'
            elif packet.FIN:
                packet_type = 'FA'
            elif packet.Data:
                packet_type = 'D'
            else:
                packet_type = 'A'
        if packet.SYN:
            if packet.ACK:
                packet_type = 'SA'
            elif not packet.ACK:
                packet_type = 'S'
        if packet.FIN:
            if packet.ACK:
                packet_type = 'FA'
            elif not packet.ACK:
                packet_type = 'F'

        time_ = round((end_time - self.start_time) * 1000, 3)
        message = '{:<12}{:<8}{:^15}{:<7}{:<8}{:<6}\n'
        write_msg = message.format(m_type, time_, packet_type, packet.seq_num, num_of_bytes, packet.ack_num)
        if is_send:
            self.file.write(write_msg)
        else:
            self.file.write(write_msg)

    def sender_rst(self):
        self.file.write('\n\n')
        self.file.write('Amount of (original) Data Transferred (in bytes): {}\n'.format(self.data_size))
        self.file.write('Number of Data Segments Sent (excluding retransmissions): {}\n'.format(self.num_packets))
        self.file.write('Number of (all) Packets Dropped (by the PL module): {}\n'.format(self.pck_loss))
        self.file.write('Number of Retransmitted Segments: {}\n'.format(self.retransmit))
        self.file.write('Number of Duplicate Acknowledgements received: {}\n'.format(self.dup_ack))
        self.file.write('\n')

    def receiver_rst(self):
        self.file.write('\n\n')
        self.file.write(
            'Amount of (original) Data Received (in bytes) – do not include retransmitted data: {}\n'.format(
                self.data_size))
        self.file.write('Number of (original) Data Segments Received: {}\n'.format(self.num_packets))
        self.file.write('Number of duplicate segments received (if any): {}\n'.format(self.re_recv))
        self.file.write('\n')

if __name__ == '__main__':
    pass
