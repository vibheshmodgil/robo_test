import socket
import time
import math

ESP32_IP = "192.168.1.8"
PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

r = 30

try:

    while True:

        for deg in range(360):

            rad = math.radians(deg)

            pan = int(90 + r * math.cos(rad))
            tilt = int(120 + r * math.sin(rad))

            sock.sendto(
                f"{pan},{tilt}\n".encode(),
                (ESP32_IP, PORT)
            )

            time.sleep(0.02)

except KeyboardInterrupt:
    pass

sock.close()