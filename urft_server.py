from classes import *
import argparse
import os

parser = argparse.ArgumentParser(description='URFT Server')
parser.add_argument('serverIP', type=str)
parser.add_argument('serverPort', type=int)

args = parser.parse_args()

serverIP = args.serverIP
serverPort = args.serverPort

server = RDTServer(serverIP, serverPort)
server.waitForConnection()