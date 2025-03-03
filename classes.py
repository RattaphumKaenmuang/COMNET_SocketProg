from socket import *
from const import *
import os
import struct
import threading

def log(txt):
    if DEBUG:
        print(txt)

class Segment:
    headerFormat = "!2I"
    def __init__(self, seqNum, ackNum, payload):
        self.seqNum = seqNum    #uint
        self.ackNum = ackNum    #uint
        self.payload = payload  #bytes

    def pack(self):
        return struct.pack(Segment.headerFormat, self.seqNum, self.ackNum) + self.payload

    @staticmethod
    def unpack(data):
        seqNum, ackNum = struct.unpack(Segment.headerFormat, data[:8])
        payload = data[8:]
        return Segment(seqNum, ackNum, payload)

class RDTEntity:
    def __init__(self):
        self.seqNum = 0
        self.ackNum = 0
        self.unACK = []  # Sent but unACKed segments
        self.toACK = []  # Received but unACKed segments

        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.pairedAddr = None  # (ip, port)

        self.lock = threading.Lock()

        self.recv_thread = threading.Thread(target=self._receive)
        self.recv_thread.daemon = True
        self.recv_thread.start()

        self.ack_thread = threading.Thread(target=self._process_toACK)
        self.ack_thread.daemon = True
        self.ack_thread.start()


    def _send(self, segment):
        segBytes = Segment.pack(segment)
        self.sock.sendto(segBytes, self.pairedAddr)

        if segment.payload:
            with self.lock:
                self.unACK.append(segment)

    def _receive(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                if not self.pairedAddr:
                    self.pairedAddr = addr
                elif addr != self.pairedAddr:
                    continue

                segment = Segment.unpack(data)

                with self.lock:
                    # Remove matched segment from unACK list if it's an ACK
                    self.unACK = [s for s in self.unACK if s.seqNum != segment.ackNum]

                    # Buffer received data
                    if segment.payload:
                        self.toACK.append(segment)

            except timeout:
                continue
            except Exception as e:
                print(f"Receive thread error: {e}")

    def _process_toACK(self):
        while True:
            with self.lock:
                if self.toACK:
                    segment = self.toACK.pop(0)
                    ackSegment = Segment(seqNum=self.seqNum, ackNum=segment.seqNum, payload=b'')
                    self._send(ackSegment)



class RDTClient(RDTEntity):
    def __init__(self):
        super().__init__()

    def connectTo(self, addr):
        self.pairedAddr = addr

        # Send SYN
        synSeg = Segment(seqNum=0, ackNum=0, payload=b'SYN')
        self._send(synSeg)

        # Wait for SYN-ACK
        while True:
            with self.lock:
                for segment in self.toACK:
                    if segment.payload == b'SYN-ACK' and segment.ackNum == self.seqNum + 1:
                        self.toACK.remove(segment)
                        self.seqNum += 1

                        # Send final ACK
                        ackSeg = Segment(seqNum=self.seqNum, ackNum=segment.seqNum + 1, payload=b'ACK')
                        self._send(ackSeg)
                        return

class RDTServer(RDTEntity):
    def __init__(self, ip, port):
        super().__init__()
        self.sock.bind((ip, port))

    def waitForConnection(self):
        while True:
            with self.lock:
                segment = next((s for s in self.toACK if s.payload == b'SYN'), None)

            if segment:
                with self.lock:
                    self.pairedAddr = self.pairedAddr or segment.pairedAddr
                    self.toACK.remove(segment)

                # Send SYN-ACK
                synAckSeg = Segment(seqNum=self.seqNum, ackNum=segment.seqNum + 1, payload=b'SYN-ACK')
                self._send(synAckSeg)

                # Wait for final ACK
                while True:
                    with self.lock:
                        ackSeg = next((s for s in self.toACK if s.payload == b'ACK' and s.ackNum == self.seqNum + 1), None)

                    if ackSeg:
                        with self.lock:
                            self.toACK.remove(ackSeg)
                            self.seqNum += 1
                        return

