import socket
import struct
import sys
import time

BM7_PORT = 7077
MAGIC_BYTE = 0xB7

def run_daemon():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', BM7_PORT))
    
    while True:
        data, addr = server_sock.recvfrom(2048)
        if len(data) >= 16:
            magic, version, command, reserved, seq, flags, length = struct.unpack("!BBBBIII", data[:16])
            if magic == MAGIC_BYTE:
                print(f"PACKET OK: {addr[0]} | SEQ: {seq} | CMD: {command:02X} | FLAGS: {flags:08X}")
            else:
                print(f"DROP: Invalid Magic 0x{magic:02X}")

if __name__ == "__main__":
    run_daemon()
