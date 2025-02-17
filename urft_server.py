import socket
import argparse

parser = argparse.ArgumentParser(description='URFT Client')
parser.add_argument('serverIP', type=str, help='Server IP address')
parser.add_argument('serverPort', type=int, help='Server port number')

args = parser.parse_args()

serverIP = args.serverIP
serverPort = args.serverPort

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((serverIP, serverPort))

print(f"Server listening on {serverIP}:{serverPort}")

while True:
    data, addr = sock.recvfrom(1024)
    print(f"{addr} sent: {data.decode("utf-8")}\n")