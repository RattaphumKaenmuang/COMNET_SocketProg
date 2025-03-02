from socket import *
from const import *

class Segment:
    def __init__(self, content, seqNum, ackNum):
        pass

class RDTEntity:
    def __init__(self):
        self.seqNum = 0
        self.ackNum = 0

class RDTClient(RDTEntity):
    def __init__(self):
        super().__init__()
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.pairedServer = None #(serverIP, serverPort)
        

class RDTServer(RDTEntity):
    def __init__(self, ip, port):
        super().__init__()
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.pairedClient = None #(clientIP, clientPort)