import socket
import argparse
import os

parser = argparse.ArgumentParser(description='URFT Client')
parser.add_argument('serverIP', type=str, help='Server IP address')
parser.add_argument('serverPort', type=int, help='Server port number')

args = parser.parse_args()

serverIP = args.serverIP
serverPort = args.serverPort

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((serverIP, serverPort))

outputPath = "./output/"

print(f"Server listening on {serverIP}:{serverPort}")

while True:
    fileName, addr = sock.recvfrom(1024)
    fileName = fileName.decode('utf-8')
    print(f"Receiving file: {fileName} from {addr}")

    fileContent, addr = sock.recvfrom(65535)
    filePath = os.path.join(outputPath, fileName)
    with open(filePath, 'wb') as file:
        file.write(fileContent)
    print(f"File {fileName} received and saved.")