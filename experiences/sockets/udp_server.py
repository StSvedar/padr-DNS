import socket

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50008              # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    while True:
        data, addr = s.recvfrom(1024)
        print('Connected by', addr)
        print('Received', repr(data))
        if not data:
            print('No data received, closing connection.')
            s.sendto(b'No data received', addr)
            break
        s.sendto(data, addr)