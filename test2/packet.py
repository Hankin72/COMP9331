# a class for the stp packet

from socket import inet_aton
from struct import pack, unpack


"""
PACKET STRUCTURE
===================
Sequence number
Acknowledgment
Flags:syn ack fin 0 
0000
-------------------
Data
===================
"""
class Header:
    def __init__(self):
        self.syn = 0
        self.ack = 0
        self.fin = 0
        self.ack_num = 0
        self._gen_isn()

    def _gen_isn(self):
        self.isn = 0
        self.seq_num = 0

    def __str__(self):
        return "SYN: {}\nACK: {}\nFIN: {}\nseq_num: {}\nack_num {}"\
                .format(self.syn, self.ack, self.fin, self.seq_num, self.ack_num)
STRUCT_CODE = '!2i4hi'
HEADER_LEN = 20

class Packet:
    def __init__(self):
        self.corrupted = None
    def wrap(self, header, data=None):
        self.msg = pack(STRUCT_CODE, header.seq_num, header.ack_num, header.syn, header.ack, header.fin, 0, 0)
        if data is not None:
            self.msg += data
        return

    def parse(self, msg, header):
        header.seq_num, header.ack_num, header.syn, header.ack, header.fin, _a, _b =\
            unpack(STRUCT_CODE, msg[:HEADER_LEN])
        data = msg[HEADER_LEN:]
        return data


