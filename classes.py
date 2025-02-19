from socket import *
from const import *
import os

class Segment:
    def __init__(self, content, seqNum, ackNum):
        pass

class RDTClient:
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.pairedServer = None #(serverIP, serverPort)
        self.awaitingACK = {}
        self.seqNum = 0
        self.ackNum = 0

    def __fragment(self, fileContent):
        segments = []
        fileSize = len(fileContent)
        for i in range(0, fileSize, FRAGMENT_SIZE):
            seg = Segment(fileContent[i : i + FRAGMENT_SIZE], self.seqNum, self.ackNum)
            segments.append(seg)
        return segments

    def __send(self, frag):
        self.sock.sendto(frag, (self.pairedServer[0], self.pairedServer[1]))
        self.awaitingACK.append(frag[0])

    def transferFile(self, filePath):
        fileName = os.path.basename(filePath)
        with open(filePath, 'rb') as file:
            fileContent = file.read()
        
        fragments = self.__fragment(fileContent)

class RDTServer:
    def __init__(self, ip, port):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.pairedClient = None #(clientIP, clientPort)
    
    def receive(self):
        fileName, addr = self.sock.recvfrom(1024)
        fileName = fileName.decode('utf-8')

        print(f"Receiving file: {fileName} from {addr}")

        filePath = os.path.join(OUTPUT_PATH, fileName)

        with open(filePath, 'wb') as file:
            segmentCount = 0
            while True:
                fileContent, addr = self.sock.recvfrom(BUFFER_SIZE)
                if not fileContent:
                    break
                file.write(fileContent)
                segmentCount += 1
                print(f"Segment: {segmentCount} received")

        print(f"File {fileName} received and saved to {OUTPUT_PATH}.")