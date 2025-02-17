import socket
import argparse
import os

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

with open(filePath, 'rb') as file:
    fileContent = file.read()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(fileContent, (serverIP, serverPort))