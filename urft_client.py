from classes import RDTClient
import argparse
import os

def splitChunks(fileContent, chunkSize):
    chunks = []
    for i in range(0, len(fileContent), chunkSize):
        chunks.append(fileContent[i:i + chunkSize])
    return chunks

parser = argparse.ArgumentParser(description='URFT Client')
parser.add_argument('filePath', type=str)
parser.add_argument('serverIP', type=str)
parser.add_argument('serverPort', type=int)

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

client = RDTClient()
client.shakeHand(serverIP, serverPort, fileName)