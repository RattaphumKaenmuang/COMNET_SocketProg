import socket
import argparse
import os

parser = argparse.ArgumentParser(description='URFT Server')
parser.add_argument('serverIP', type=str)
parser.add_argument('serverPort', type=int)

args = parser.parse_args()

serverIP = args.serverIP
serverPort = args.serverPort

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((serverIP, serverPort))
sock.settimeout(0.5)

outputPath = "./output/"

print(f"Server listening on {serverIP}:{serverPort}")

try:
    while True:
        try:
            fileName, addr = sock.recvfrom(1024)
            fileName = fileName.decode('utf-8')
            print(f"Receiving file: {fileName} from {addr}")

            filePath = os.path.join(outputPath, fileName)
            with open(filePath, 'wb') as file:
                segmentCount = 0
                while True:
                    chunkContent, addr = sock.recvfrom(1024)
                    if chunkContent == b'':
                        break
                    file.write(chunkContent)
                    segmentCount += 1
                    print(f"Segment: {segmentCount} received")
            print(f"File {fileName} received and saved.")
        except socket.timeout:
            print("Timeout...")
        except KeyboardInterrupt:
            print("Keyboard Interrupted")
            break
except KeyboardInterrupt:
    print("Shutting Down...")
finally:
    sock.close()