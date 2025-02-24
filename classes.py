from socket import *
from const import *
from random import *
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
        self.seqNum = randint(0, MAX_32BIT_NUM)
        self.ackNum = randint(0, MAX_32BIT_NUM)

    def yap(self, txt):
        if self.willYap: print(txt)

    def _pack(self, segment):
        # [seqNum (4)][ackNum (4)][flag (1)][payload (varies)]; No payload length, calculate it yourself lmao.
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

    def __transmit(self, segment, serverIP, serverPort, maxRetries=MAX_RETRIES):
        segBytes = self._pack(segment)
        self.yap(f"{addr} : SEQ={self.seqNum - segment.seqNum} ACK={self.ackNum - segment.ackNum} FLAG={segment.flag}")
        for _ in range(maxRetries):
            try:
                self.sock.sendto(segBytes, (serverIP, serverPort))
                resp, addr = self.sock.recvfrom(BUFFER_SIZE)
                respSeg = self._unpack(resp)
                self.yap(f"{addr} : SEQ={self.seqNum - respSeg.seqNum} ACK={self.ackNum - respSeg.ackNum} FLAG={respSeg.flag}")
                respPayloadLen = len(respSeg.payload)

                if resp.ackNum == (self.seqNum + respPayloadLen) % MAX_32BIT_NUM:
                    return respSeg
                else:
                    raise WrongAckNumException
            except timeout:
                self.yap(f"RESPONSE TIMEOUT. Retransmitting...")
            except WrongAckNumException:
                self.yap(f"WRONG ACKNUM. Retransmitting...")
        return False

    def shakeHand(self, serverIP, serverPort, fileName):
        # Send SYN and wait for SYN_ACK
        synSeg = Segment(seqNum=self.seqNum, ackNum=self.ackNum, flag=SYN, payload=fileName)
        respSeg = self.__transmit(self, synSeg, serverIP, serverPort)

        if not respSeg or respSeg.payload != fileName: return False #Maybe better implementations later.

        self.pairedServer = (serverIP, serverPort)

        # Increment params
        filenameLen = len(fileName)
        self.seqNum = (self.seqNum + filenameLen) % MAX_32BIT_NUM
        self.ackNum = (self.ackNum + filenameLen) % MAX_32BIT_NUM

        return True

class RDTServer(RDTEntity):
    def __init__(self, ip, port):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.pairedClient = None #(clientIP, clientPort)

    def extendHand(self):
        # Wait for SYN
        synSegBytes, addr1 = self.sock.recvfrom(BUFFER_SIZE)
        
        # Send SYN_ACK
        synSeg = self._unpack(synSegBytes)
        synACKSeg = Segment(seqNum=synSeg.seqNum, ackNum=(synSeg.seqNum+1) % MAX_32BIT_NUM, flag=SYN_ACK, payload=synSeg.payload)
        self.sock.sendto(synACKSeg, addr1)

        # Wait for ACK
        ackSegBytes, addr2 = self.sock.recvfrom(BUFFER_SIZE)
        ackSeg = self._unpack(ackSegBytes)

        sameADDR = addr1 == addr2
        correctSeqNum = ackSeg.seqNum == ((synSeg.seqNum+1) % MAX_32BIT_NUM)
        correctAckNum = ackSeg.ackNum == ((synSeg.ackNum+1) % MAX_32BIT_NUM)

        # Validate
        if not (sameADDR and correctSeqNum and correctAckNum): return False

        self.seqNum = (synSeg.seqNum+1) % MAX_32BIT_NUM
        self.ackNum = (synSeg.ackNum+1) % MAX_32BIT_NUM
        self.pairedClient = addr1

        return True

class WrongAckNumException(Exception):
    pass