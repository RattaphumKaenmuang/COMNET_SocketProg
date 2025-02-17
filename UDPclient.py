import socket

serverIP = "192.168.21.216"
serverPort = 6969
message = input("Enter your message: ")
message = message if message else "The client didn't input shit lmao"
message = message.encode("utf-8")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(message, (serverIP, serverPort))