# Echo client program
import socket

HOST = 'localhost'    # The remote host
PORT = 50008              # The same port as used by the server
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.sendto(b'Hello, world', (HOST, PORT))
    data = s.recv(1024)
print('Received', repr(data))
