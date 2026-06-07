import socket
import time

ESP32_IP = "192.168.1.8"
PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)

for i in range(20):

    start = time.time()

    sock.sendto(b"90,120\n", (ESP32_IP, PORT))

    try:
        sock.recvfrom(128)

        latency = (time.time() - start) * 1000

        print(f"{latency:.1f} ms")

    except socket.timeout:
        print("timeout")

    time.sleep(0.5)