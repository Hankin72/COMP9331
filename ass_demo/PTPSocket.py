import threading
import time
import struct
import socket
import queue


# 协议头
class Header:
    def __init__(self, ACK=False, SYN=False, FIN=False):
        self.source_port = 0
        self.dest_port = 0
        self.sequence_number = 0
        self.acknowledgement_number = 0

        # 标志位
        self.ACK = ACK
        self.SYN = SYN
        self.FIN = FIN

    def toBytes(self):
        bytes = struct.pack(">QQQQ???",
                            self.source_port,
                            self.dest_port,
                            self.sequence_number,
                            self.acknowledgement_number,
                            self.ACK, self.SYN, self.FIN)
        return bytes

    # 解析的过程, 静态的，不需要生成一个对象，就可以调用它，
    @staticmethod
    def parse(bytes):
        header = Header()
        rst = struct.unpack(">QQQQ???", bytes)
        header.source_port = rst[0]
        header.dest_port = rst[1]
        header.sequence_number = rst[2]
        header.acknowledgement_number = rst[3]
        header.ACK = rst[4]
        header.SYN = rst[5]
        header.FIN = rst[6]

        return header

    def __str__(self):
        s = "_______________________\n"
        s += "|{:^10d}|{:^10d}|\n".format(self.source_port, self.dest_port)
        s += "|{:^10d}|{:^10d}|\n".format(self.sequence_number, self.acknowledgement_number)
        s += "|{:^7}{:^7}{:^7}|\n".format(self.ACK, self.SYN, self.FIN)
        s += "-----------------------"
        return s


# 协议段
class Segment:
    def __init__(self, ACK=False, SYN=False, FIN=False):
        self.header = Header(ACK, SYN, FIN)
        # 字节串
        self.data = b''

    def toBytes(self):
        bytes = self.header.toBytes() + self.data
        return bytes

    @staticmethod
    def parse(bytes):
        segment = Segment()
        header_bytes = bytes[:4 * 8 + 3]
        data = bytes[4 * 8 + 3:]

        # 通过Header将头部解析
        header = Header.parse(header_bytes)
        # 对应数据填入对应的字段中
        segment.header = header
        segment.data = data
        return segment

    def __str__(self):
        s = self.header.__str__() + "\n"
        s += self.data.decode() + "\n"
        s += "_______________________"
        return s

    def __len__(self):
        return 4 * 8 + 3 + len(self.data)


class PTPSocket:
    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip_port = ("127.0.0.1", 0)

        self.opposite_ip_port = ("127.0.0.1", 0)

        self.state = 'CLOSED'
        self.send_buffer = queue.Queue()
        self.recv_buffer = queue.Queue()
        self.sequence_num = 0

        self.is_server = False
        self.is_first_send = False
        self.is_using_close = False

        threading.Thread(target=self.send_threading).start()
        # threading.Thread(target=self.recv_threading).start()
        threading.Thread(target=self.recv_threading2).start()

        threading.Thread(target=self.log_threading).start()

    # log 文件。。。。
    def log_threading(self):
        while True:
            print(self.state)
            time.sleep(1)

    def bind(self, addr):
        self.ip_port = addr
        self.udp_socket.bind(self.ip_port)

    def listen(self):
        self.is_server = True
        self.state = 'LISTEN'

    def accept(self):
        while self.state != 'ESTABLISHED':
            #  阻塞
            pass
        # 返回自身，
        return self

    def connect(self, addr):
        self.opposite_ip_port = addr

        # 开始建立连接，开始三次握手
        # syn = Segment(SYN=True)
        # syn.header.sequence_number = self.sequence_num
        #
        # # send,直接进行发送
        # self._send(syn)
        # self.state = "SYN-SENT"
        #
        # synack = self._recv()
        # if synack.header.ACK and synack.header.SYN:
        #     ack = Segment(ACK=True)
        #     ack.header.sequence_number = synack.header.acknowledgement_number
        #     ack.header.acknowledgement_number = synack.header.sequence_number + 1
        #     self._send(ack)
        #     self.state = "ESTABLISHED"
        #     print("连接已经建立")
        syn = Segment(SYN=True)
        # send,直接进行发送
        self._send(syn)
        self.state = "SYN-SENT"
        # 至于connect才进行后面的连接工作
        while self.state != 'ESTABLISHED':
            pass

    # 真正的发送
    def _send(self, segment):
        # 端口号
        segment.header.source_port = self.ip_port[1]
        segment.header.dest_port = self.opposite_ip_port[1]
        self.udp_socket.sendto(segment.toBytes(), self.opposite_ip_port)
        print("send：")
        print(segment)

        if not self.is_first_send:
            self.is_first_send = True

    def send_threading(self):
        while True:
            segment = self.send_buffer.get()
            try:
                self._send(segment)
            except OSError:
                return

    # 把数据存在缓存
    def send(self, segment):
        self.send_buffer.put(segment)
        return len(segment)

    def _recv(self):
        bytes, addr = self.udp_socket.recvfrom(1024)
        self.opposite_ip_port = addr
        segment = Segment.parse(bytes)
        print("recv:")
        print(segment)
        return segment

    def recv_threading2(self):
        while True:
            if not self.is_first_send and not self.is_server:
                continue

            try:
                segment = self._recv()
            except OSError:
                return

            if self.state == 'CLOSED':
                pass

            elif self.state == 'LISTEN':
                syn = segment
                if syn.header.SYN:
                    synack = Segment(ACK=True, SYN=True)
                    """seq  and ack here"""
                    self._send(synack)
                    self.state = 'SYN-RCVD'

            elif self.state == 'SYN-SENT':
                synack = segment
                if synack.header.ACK and synack.header.SYN:
                    ack = Segment(ACK=True)
                    """seq  and ack here"""
                    self._send(ack)
                    self.state = "ESTABLISHED"
                    print("建立连接=====")

            elif self.state == 'SYN-RCVD':
                ack = segment
                if ack.header.ACK:
                    self.state = "ESTABLISHED"
                    print("连接已建立=================")

            elif self.state == "ESTABLISHED":
                if segment.header.FIN:
                    fin = segment
                    ack = Segment(ACK=True)
                    """seq  and ack here"""

                    self._send(ack)
                    self.state = 'CLOSE-WAIT'

                    fin2 = Segment(FIN=True)
                    self._send(fin2)
                    self.state = 'LAST-ACK'

                # 客户端接收到了 数据段的ack
                elif segment.header.ACK:
                    pass

                # 服务器接收到了 数据段，
                else:
                    pass


            elif self.state == 'FIN-WAIT-1':
                ack = segment
                if ack.header.ACK:
                    self.state = 'FIN-WAIT-2'

            elif self.state == 'FIN-WAIT-2':
                fin2 = segment
                if fin2.header.FIN:
                    ack = Segment(ACK=True)
                    self._send(ack)
                    self.state = 'TIME-WAIT'
                    time.sleep(0.5)
                    self.state = 'CLOSED'
                    self.udp_socket.close()

            # elif self.state == 'CLOSE-WAIT':
            #     pass
            elif self.state == 'LAST-ACK':
                ack = segment
                if ack.header.ACK:
                    self.state = 'CLOSED'
                    self.udp_socket.close()

            # elif self.state == 'TIME-WAIT':
            #     pass

    def recv_threading(self):
        while True:
            if self.is_first_send or self.is_server:
                segment = self._recv()
                # 建立连接
                if self.is_server and segment.header.SYN:
                    syn = segment
                    synack = Segment(ACK=True, SYN=True)
                    synack.header.acknowledgement_number = syn.header.sequence_number + 1
                    synack.header.sequence_number = self.sequence_num
                    self._send(synack)
                    self.state = "SYN-RCVD"
                    ack = self._recv()

                    if ack.header.ACK:
                        self.state = "ESTABLISHED"
                        print('已经建立连接。。。。。。')
                # close
                elif not self.is_using_close and segment.header.FIN:
                    fin = segment
                    print("recv fin1")
                    ack = Segment(ACK=True)
                    ack.header.sequence_number = self.sequence_num + 3000
                    ack.header.acknowledgement_number = fin.header.sequence_number + 1
                    self._send(ack)
                    print("send ack1")
                    self.state = 'CLOSE-WAIT'

                    fin2 = Segment(FIN=True)
                    fin2.header.sequence_number = self.sequence_num + 4000
                    self._send(fin2)
                    print("send fin2")
                    self.state = 'LAST-ACK'

                    ack2 = self._recv()
                    print("recv ack2")
                    if ack2.header.ACK:
                        self.state = 'CLOSED'

                else:
                    self.recv_buffer.put(segment)

    def recv(self):
        segment = self.recv_buffer.get()
        return segment

    def close(self):
        fin = Segment(FIN=True)
        self._send(fin)
        self.state = 'FIN-WAIT-1'

        # self.is_using_close = True
        #
        # fin = Segment(FIN=True)
        # fin.header.sequence_number = self.sequence_num + 1000
        # self._send(fin)
        # print("send fin1")
        # self.state = 'FIN-WAIT-1'

        # # recv 从buffer中取出
        # ack = self.recv()
        # print("recv ack1")
        # if ack.header.ACK:
        #     self.state = "FIN-WAIT-2"
        #     fin2 = self.recv()
        #     print("recv fin2")
        #     if fin2.header.FIN:
        #         ack2 = Segment(ACK=True)
        #         ack2.header.sequence_number = self.sequence_num + 2000
        #         ack2.header.acknowledgement_number = fin2.header.sequence_number + 1
        #         self._send(ack2)
        #         print("send ack2")
        #         self.state = 'TIME-WAIT'
        #
        #         time.sleep(2)
        #         self.state = 'CLOSED'


if __name__ == "__main__":
    # header1 = Header(ACK=True)
    # header1.seq_number = 1000
    # print(header1)
    #
    # bytes = header1.toBytes()
    # print(bytes)
    #
    # header2 = Header.parse(bytes)
    # print(header2)
    segment = Segment(FIN=True)
    segment.data = b'1dasdasd'
    print(segment)

    bytes = segment.toBytes()
    print(bytes)
    segment2 = Segment.parse(bytes)
    print(segment2)
