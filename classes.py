from socket import *
from const import *

class Segment:
    def __init__(self, content, seqNum, ackNum):
        pass

class RDTClient:
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.pairedServer = None #(serverIP, serverPort)
        

class RDTServer:
    def __init__(self, ip, port):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.pairedClient = None #(clientIP, clientPort)