import socket

serverIP = "192.168.21.216"
serverPort = 6969

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((serverIP, serverPort))

while True:
    data, addr = sock.recvfrom(1024)
    print(f"{addr} sent: {data.decode("utf-8")}")