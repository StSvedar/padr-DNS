import socket

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        message = b''
        while True:
            data = conn.recv(1)
            print('Received', repr(data))
            if not data: break
            if data == b'\0':
                break
            message += data
        conn.sendall(message)