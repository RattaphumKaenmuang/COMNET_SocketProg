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
    
    def __str__(self):
        shortPayload = self.payload[:8]
        shortPayload = shortPayload if len(self.payload) <= 8 else shortPayload + "..."
        return f"[seqNum={self.seqNum} ackNum={self.ackNum} payload={shortPayload}]"

class RDTEntity:
    def __init__(self):
        self.seqNum = 0
        self.ackNum = 0
        self.unACK = []  # Sent but unACKed segments
        self.toACK = []  # Received but unACKed segments
        self.handshakeInProgress = True

        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.pairedAddr = None  # (ip, port)

        self.lock = threading.Lock()
        log(f"Thread Lock created: {self.lock}")

        self.recv_thread = threading.Thread(target=self._receive)
        self.recv_thread.daemon = True
        self.recv_thread.start()
        log(f"recv_thread created: {self.recv_thread}")

        self.ack_thread = threading.Thread(target=self._process_toACK)
        self.ack_thread.daemon = True
        self.ack_thread.start()
        log(f"ack_thread created: {self.ack_thread}")


    def _send(self, segment):
        segBytes = Segment.pack(segment)
        self.sock.sendto(segBytes, self.pairedAddr)
        log(f"Sending segment: {str(segment)}")

        if segment.payload and segment.payload not in [b"SYN", b"SYN-ACK", b"ACK"]:
            with self.lock:
                self.unACK.append(segment)
                log(f"Is a payload segment. Added to unACK.")

    def _receive(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                if not self.pairedAddr:
                    self.pairedAddr = addr
                elif addr != self.pairedAddr:
                    continue

                segment = Segment.unpack(data)
                log(f"Receiving segment: {str(segment)}")

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
                if self.toACK and not self.handshakeInProgress:
                    segment = self.toACK.pop(0)
                    ackSegment = Segment(seqNum=self.seqNum, ackNum=segment.seqNum, payload=b'')
                    self._send(ackSegment)



class RDTClient(RDTEntity):
    def __init__(self):
        super().__init__()

    def connectTo(self, addr):
        log(f"Initiating connection with {addr}")
        self.pairedAddr = addr

        # Send SYN
        synSeg = Segment(seqNum=0, ackNum=0, payload=b'SYN')
        self._send(synSeg)

        # Wait for SYN-ACK
        while True:
            with self.lock:
                for segment in self.toACK:
                    if segment.payload == b'SYN-ACK' and segment.ackNum == self.seqNum + 1:
                        log(f"SYN-ACK received.")
                        self.toACK.remove(segment)
                        self.seqNum += 1

                        # Send final ACK
                        log(f"Sending handshake ACK.")
                        ackSeg = Segment(seqNum=self.seqNum, ackNum=segment.seqNum + 1, payload=b'ACK')
                        self._send(ackSeg)
                        self.handshakeInProgress = False
                        log(f"Handshaking Completed.")
                        return True
        
    def sendFile(self, filePath):
        fileName = os.path.basename(filePath)
        fileNameSeg = Segment(seqNum=self.seqNum, ackNum=self.ackNum, payload=fileName.encode())

        log(f"filePath={filePath}")
        log(f"fileName={fileName}")

        self._send(fileNameSeg)

class RDTServer(RDTEntity):
    def __init__(self, ip, port):
        super().__init__()
        self.addr = (ip, port)
        self.sock.bind(self.addr)

    def waitForConnection(self):
        log(f"Waiting for connection at {self.addr}...")
        while True:
            with self.lock:
                segment = next((s for s in self.toACK if s.payload == b'SYN'), None)

            if segment:
                log("SYN sent from client found.")
                with self.lock:
                    self.pairedAddr = self.pairedAddr or segment.pairedAddr
                    self.toACK.remove(segment)
                    log(f"Client addr: {self.pairedAddr}")

                # Send SYN-ACK
                log("Sending SYN-ACK.")
                synAckSeg = Segment(seqNum=self.seqNum, ackNum=segment.seqNum + 1, payload=b'SYN-ACK')
                self._send(synAckSeg)

                # Wait for final ACK
                while True:
                    with self.lock:
                        ackSeg = next((s for s in self.toACK if s.payload == b'ACK' and s.ackNum == self.seqNum + 1), None)

                    if ackSeg:
                        log(f"Handshake ACK received.")
                        with self.lock:
                            self.toACK.remove(ackSeg)
                            self.seqNum += 1
                        self.handshakeInProgress = False
                        return True

