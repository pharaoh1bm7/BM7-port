import socket
import struct

def send_test():
    packet = struct.pack("!BBBBIII", 0xB7, 0x01, 0x01, 0x00, 1, 0x00000001, 0)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(packet, ('127.0.0.1', 7077))
    sock.close()

if __name__ == "__main__":
    send_test()
