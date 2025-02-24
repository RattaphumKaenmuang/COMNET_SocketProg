from socket import *
from const import *
from random import *
import struct

class Segment:
    headerSize = 4 + 4 + 1
    def __init__(self, seqNum, ackNum, flag, payload=''):
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.flag = flag
        self.payload = payload  #str

class RDTEntity:
    def __init__(self, willYap=YAP):
        self.willYap = willYap #Boolean
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.settimeout(SOCKET_TIMEOUT)

        self.startSeqNum = randint(0, MAX_32BIT_NUM)
        self.startAckNum = randint(0, MAX_32BIT_NUM)

        self.seqNum = self.startSeqNum
        self.ackNum = self.startAckNum

    def yap_text(self, txt):
        if self.willYap and txt is not None:
            print(txt)

    def yap_segment(self, segment, sender='Self'):
        if self.willYap and segment is not None:
            print(f"{str(sender)}: SEQ={segment.seqNum - self.startSeqNum} ACK={segment.ackNum - self.startAckNum} FLAG={segment.flag}")


    def _pack(self, segment):
        # [seqNum (4)][ackNum (4)][flag (1)][payload (varies)]; No payload length, calculate it yourself lmao.
        format = f"!2I B {len(segment.payload)}s" #uint, uint, uchar, n * uchar
        return struct.pack(format, segment.seqNum, segment.ackNum, segment.flag, segment.payload.encode())
    
    def _unpack(self, segBytes):
        payloadLen = len(segBytes) - Segment.headerSize
        format = f"!2I B {payloadLen}s"
        seqNum, ackNum, flag, payload = struct.unpack(format, segBytes)

        # self.yap_text("===== UNPACKING RESULT =====")
        # self.yap_text(f"payloadLen: {payloadLen}")
        # self.yap_text(f"sN, aN, f, p: {seqNum}, {ackNum}, {flag}, {payload}")
        # self.yap_text("============================")
        
        return Segment(seqNum, ackNum, flag, payload.decode())
    
class RDTClient(RDTEntity):
    def __init__(self):
        super().__init__(self)
        self.pairedServer = None #(serverIP, serverPort)

    def __transmit(self, segment, serverIP, serverPort, maxRetries=MAX_RETRIES):
        segBytes = self._pack(segment)
        try:
            for _ in range(maxRetries):
                try:
                    self.yap_text("Sending SYN")
                    self.yap_segment(segment)

                    self.sock.sendto(segBytes, (serverIP, serverPort))

                    resp, addr = self.sock.recvfrom(BUFFER_SIZE)
                    respSeg = self._unpack(resp)

                    self.yap_segment(respSeg, addr)

                    respPayloadLen = len(respSeg.payload)

                    if respSeg.ackNum == (self.ackNum + respPayloadLen) % MAX_32BIT_NUM:
                        self.yap_text("CORRECT ACKNUM. TRANSMITTING COMPLETED.")
                        return respSeg
                    else:
                        raise WrongAckNumException((self.ackNum + respPayloadLen) % MAX_32BIT_NUM, respSeg.ackNum)
                except timeout:
                    self.yap_text("RESPONSE TIMEOUT. Retransmitting...")
                except WrongAckNumException as e:
                    self.yap_text(f"WRONG ACKNUM ({e.actualAck} should be {e.expectedAck}; Diff = {e.actualAck - e.expectedAck}). Retransmitting...")
                except KeyboardInterrupt:
                    self.yap_text("KEYBOARD INTERRUPTED_IN")
                    break

        except KeyboardInterrupt:
            self.yap_text(f"KEYBOARD INTERRUPTED")
            return False

        return False

    def shakeHand(self, serverIP, serverPort, fileName):
        # Send SYN and wait for SYN_ACK
        synSeg = Segment(seqNum=self.seqNum, ackNum=self.ackNum, flag=SYN, payload=fileName)
        respSeg = self.__transmit(synSeg, serverIP, serverPort)

        if not respSeg or respSeg.payload != fileName:
            self.yap_text("OOPS. SYN_ACK SEG WENT BAD.")
            return False #Maybe better implementations later.

        # Increment params
        filenameLen = len(fileName)
        self.seqNum = (self.seqNum + filenameLen) % MAX_32BIT_NUM
        self.ackNum = (self.ackNum + filenameLen) % MAX_32BIT_NUM

        # Send ACK
        self.pairedServer = (serverIP, serverPort)
        ackSeg = Segment(self.seqNum, self.ackNum, flag=ACK, payload='')
        self.yap_segment(ackSeg)

        ackSegBytes = self._pack(ackSeg)
        self.sock.sendto(ackSegBytes, self.pairedServer)

        self.yap_text("HOLY SHIT HANDSHAKING COMPLETED")
        self.yap_text(f"Paired Server: {self.pairedServer}")
        
        return True

class RDTServer(RDTEntity):
    def __init__(self, ip, port):
        super().__init__(self)
        self.sock.bind((ip, port))
        self.pairedClient = None #(clientIP, clientPort)

    def extendHand(self):
        # Wait for SYN
        while True:
            try:
                synSegBytes, addr1 = self.sock.recvfrom(BUFFER_SIZE)
                break
            except timeout:
                self.yap_text("Waiting for SYN.")
        
        # Align the params
        synSeg = self._unpack(synSegBytes)
        self.startSeqNum = synSeg.seqNum
        self.startAckNum = synSeg.ackNum
        self.seqNum = self.startSeqNum
        self.ackNum = self.startAckNum
        self.yap_segment(synSeg, addr1)
        self.yap_text(f"Realigned Params: startSeq={self.startSeqNum} startAck={self.startAckNum}")

        # Prepare SYN_ACK
        synSegPayloadLen = len(synSeg.payload)
        self.ackNum = self.ackNum + synSegPayloadLen
        synAckSeg = Segment(seqNum=self.seqNum, ackNum=self.ackNum, flag=SYN_ACK, payload=synSeg.payload)
        self.yap_text("Sending SYN_ACK")

        synAckSegBytes = self._pack(synAckSeg)
        

        # Send SYN_ACK and wait for ACK
        for _ in range(MAX_RETRIES):
            try:
                self.sock.sendto(synAckSegBytes, addr1)
                self.yap_segment(synAckSeg)
                ackSegBytes, addr2 = self.sock.recvfrom(BUFFER_SIZE)
                break
            except timeout:
                self.yap_text("Waiting for ACK.")

        ackSeg = self._unpack(ackSegBytes)

        sameADDR = addr1 == addr2
        correctSeqNum = ackSeg.seqNum == ((self.startSeqNum + synSegPayloadLen) % MAX_32BIT_NUM)
        correctAckNum = ackSeg.ackNum == ((self.startAckNum + synSegPayloadLen) % MAX_32BIT_NUM)

        # Validate
        if not (sameADDR and correctSeqNum and correctAckNum): return False

        self.startAckNum = (self.startAckNum + synSegPayloadLen) % MAX_32BIT_NUM
        self.pairedClient = addr1
        self.yap_text("HOLY SHIT HANDSHAKING COMPLETED")
        self.yap_text(f"Paired Client: {self.pairedClient}")

        return True

class WrongAckNumException(Exception):
    def __init__(self, expectedAck, actualAck):
        self.expectedAck = expectedAck
        self.actualAck = actualAck