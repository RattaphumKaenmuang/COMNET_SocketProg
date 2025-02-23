import socket
import argparse
import os

def splitChunks(fileContent, chunkSize):
    chunks = []
    for i in range(0, len(fileContent), chunkSize):
        chunks.append(fileContent[i:i + chunkSize])
    return chunks

parser = argparse.ArgumentParser(description='URFT Client')
parser.add_argument('filePath', type=str, nargs='?', default="The client didn't input shit lmao", help='Message to send')
parser.add_argument('serverIP', type=str, help='Server IP address')
parser.add_argument('serverPort', type=int, help='Server port number')

args = parser.parse_args()

filePath = args.filePath
serverIP = args.serverIP
serverPort = args.serverPort

if not os.path.isfile(filePath):
    print(f"File {filePath} doesn't exist")
    exit(1)

fileName = os.path.basename(filePath)

with open(filePath, 'rb') as file:
    fileContent = file.read()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(fileName.encode("utf-8"), (serverIP, serverPort))
chunks = splitChunks(fileContent, 1024)
i = 0
for c in chunks:
    i += 1
    print(f"Sending chunk {i}")
    sock.sendto(c, (serverIP, serverPort))

sock.sendto(b'', (serverIP, serverPort))
print(f"Finished sending {fileName}")