import socket
import time

ESP32_IP = "192.168.1.8"
PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

count = 0

start = time.time()

while time.time() - start < 10:

    pan = 90 + (count % 30)

    sock.sendto(
        f"{pan},120\n".encode(),
        (ESP32_IP, PORT)
    )

    count += 1

    time.sleep(0.01)

print()
print("Packets sent:", count)

sock.close()