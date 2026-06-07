import socket
import time

ESP32_IP = "192.168.1.8"
PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:

        for pan in range(40, 141):
            sock.sendto(
                f"{pan},120\n".encode(),
                (ESP32_IP, PORT)
            )
            time.sleep(0.02)

        for pan in range(140, 39, -1):
            sock.sendto(
                f"{pan},120\n".encode(),
                (ESP32_IP, PORT)
            )
            time.sleep(0.02)

except KeyboardInterrupt:
    pass

sock.close()