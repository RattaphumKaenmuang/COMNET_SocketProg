from socket import *
from const import *
import struct

class Segment:
    headerSize = 4 + 4 + 1
    def __init__(self, seqNum, ackNum, flag, payload):
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.flag = flag
        self.payload = payload  #str

class RDTEntity:
    def __init__(self, willYap=YAP):
        self.willYap = willYap #Boolean

    def yap(self, txt):
        if self.willYap: print(txt)

    def _pack(self, segment):
        # [seqNum (8)][ackNum (8)][flag (1)][payload (varies)]; No payload length, calculate it yourself lmao.
        format = f"!2I B {len(segment.payload)}s" #uint, uint, uchar, n * uchar
        return struct.pack(format, segment)
    
    def _unpack(self, segBytes):
        payloadLen = len(segBytes) - Segment.headerSize*8
        format = f"!2I B {payloadLen}s"
        seqNum, ackNum, flag, payload = struct.unpack(format, segBytes)
        return Segment(seqNum, ackNum, flag, payload)
    
class RDTClient(RDTEntity):
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.pairedServer = None #(serverIP, serverPort)

    def shakeHand(self, serverIP, serverPort, fileName):
        pass

class RDTServer(RDTEntity):
    def __init__(self, ip, port):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.pairedClient = None #(clientIP, clientPort)

    def extendHand(self):
        pass