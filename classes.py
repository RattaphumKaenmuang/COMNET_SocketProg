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
    
    def _getNewAckNum(self, increment):
        return (self.ackNum + increment) % MAX_32BIT_NUM
    
    def _getNewSeqNum(self, increment):
        return (self.seqNum + increment) % MAX_32BIT_NUM

    def _yap_text(self, txt):
        if self.willYap and txt is not None:
            print(txt)

    def _yap_segment(self, segment, sender='Self'):
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

        # self._yap_text("===== UNPACKING RESULT =====")
        # self._yap_text(f"payloadLen: {payloadLen}")
        # self._yap_text(f"sN, aN, f, p: {seqNum}, {ackNum}, {flag}, {payload}")
        # self._yap_text("============================")
        
        return Segment(seqNum, ackNum, flag, payload.decode())
    
class RDTClient(RDTEntity):
    def __init__(self):
        super().__init__(self)
        self.pairedServer = None #(serverIP, serverPort)

    def __transmit(self, segment, serverIP, serverPort, maxRetries=MAX_RETRIES):
        segBytes = self._pack(segment)
        for _ in range(maxRetries):
            try:
                self._yap_text("Sending SYN")
                self._yap_segment(segment)

                self.sock.sendto(segBytes, (serverIP, serverPort))

                ackBytes, addr = self.sock.recvfrom(BUFFER_SIZE)
                ackSeg = self._unpack(ackBytes)
                self._yap_segment(ackSeg, addr)

                ackPayloadLen = len(ackSeg.payload)
                expectedAckNum = self._getNewAckNum(ackPayloadLen)

                if ackSeg.ackNum == expectedAckNum:
                    self._yap_text("CORRECT ACKNUM. TRANSMITTING COMPLETED.")
                    return ackSeg
                else:
                    raise WrongAckNumException(expectedAckNum, ackSeg.ackNum)
            except timeout:
                self._yap_text("RESPONSE TIMEOUT. Retransmitting...")
            except WrongAckNumException as e:
                self._yap_text(f"WRONG ACKNUM ({e.actualAck} should be {e.expectedAck}; Diff = {e.actualAck - e.expectedAck}). Retransmitting...")
            except KeyboardInterrupt:
                self._yap_text("KEYBOARD INTERRUPTED_IN")
                break

        return False

    def shakeHand(self, serverIP, serverPort, fileName):
        # Send SYN and wait for SYN_ACK
        synSeg = Segment(seqNum=self.seqNum, ackNum=self.ackNum, flag=SYN, payload=fileName)
        respSeg = self.__transmit(synSeg, serverIP, serverPort)

        if not respSeg or respSeg.payload != fileName:
            self._yap_text("OOPS. SYN_ACK SEG WENT BAD.")
            return False #Maybe better implementations later.

        # Increment params
        filenameLen = len(fileName)
        self.seqNum = self._getNewSeqNum(filenameLen)
        self.ackNum = self._getNewAckNum(filenameLen)

        # Send ACK
        self.pairedServer = (serverIP, serverPort)
        ackSeg = Segment(self.seqNum, self.ackNum, flag=ACK, payload='')
        self._yap_segment(ackSeg)

        ackSegBytes = self._pack(ackSeg)
        self.sock.sendto(ackSegBytes, self.pairedServer)

        self._yap_text("HOLY SHIT HANDSHAKING COMPLETED")
        self._yap_text(f"Paired Server: {self.pairedServer}")

        return True

class RDTServer(RDTEntity):
    def __init__(self, ip, port):
        super().__init__(self)
        self.sock.bind((ip, port))
        self.pairedClient = None #(clientIP, clientPort)

    def __alignParams(self, newSeqNum, newAckNum):
        self.startSeqNum = newSeqNum
        self.startAckNum = newAckNum
        self.seqNum = self.startSeqNum
        self.ackNum = self.startAckNum
        self._yap_text(f"Realigned Params: startSeq={self.startSeqNum} startAck={self.startAckNum}")

    def extendHand(self):
        # Wait for SYN
        while True:
            try:
                synSegBytes, addr1 = self.sock.recvfrom(BUFFER_SIZE)
                break
            except timeout:
                self._yap_text("Waiting for SYN.")
        
        # Align the params
        synSeg = self._unpack(synSegBytes)
        self._yap_segment(synSeg, addr1)
        self.__alignParams(synSeg.seqNum, synSeg.ackNum)

        # Prepare SYN_ACK
        synSegLen = len(synSeg.payload)
        self.ackNum = self._getNewAckNum(synSegLen) #ackNum first modified here
        synAckSeg = Segment(seqNum=self.seqNum, ackNum=self.ackNum, flag=SYN_ACK, payload=synSeg.payload)
        self._yap_text("Sending SYN_ACK")

        synAckSegBytes = self._pack(synAckSeg)

        # Send SYN_ACK and wait for ACK
        for _ in range(MAX_RETRIES):
            try:
                self.sock.sendto(synAckSegBytes, addr1)
                self._yap_segment(synAckSeg)
                ackSegBytes, addr2 = self.sock.recvfrom(BUFFER_SIZE)
                break
            except timeout:
                self._yap_text("Waiting for ACK.")

        ackSeg = self._unpack(ackSegBytes)

        sameADDR = (addr1 == addr2)
        correctSeqNum = (ackSeg.seqNum == self._getNewSeqNum(synSegLen))
        correctAckNum = (ackSeg.ackNum == self.ackNum)

        # Validate
        if not (sameADDR and correctSeqNum and correctAckNum):
            self._yap_text("ACK VALIDATION FAILED")      
            return False

        # Set SeqNum
        self.seqNum = self._getNewSeqNum(synSegLen) #seqNum first modified here

        self.pairedClient = addr1
        self._yap_text("HOLY SHIT HANDSHAKING COMPLETED")
        self._yap_text(f"Paired Client: {self.pairedClient}")

        return True

class WrongAckNumException(Exception):
    def __init__(self, expectedAck, actualAck):
        self.expectedAck = expectedAck
        self.actualAck = actualAck