from classes import *
import argparse
import os

parser = argparse.ArgumentParser(description='URFT Client')
parser.add_argument('filePath', type=str)
parser.add_argument('serverIP', type=str)
parser.add_argument('serverPort', type=int)

args = parser.parse_args()

filePath = args.filePath
serverIP = args.serverIP
serverPort = args.serverPort

client = RDTClient()
connectionSuccess = client.connectTo((serverIP, serverPort))
if connectionSuccess:
    client.sendFile(filePath)