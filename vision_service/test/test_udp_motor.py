import socket
import time

ESP32_IP = "192.168.1.8"
PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def move(pan, tilt):
    msg = f"{pan},{tilt}\n"
    sock.sendto(msg.encode(), (ESP32_IP, PORT))
    print(f"sent -> pan={pan} tilt={tilt}")

print("Center")
move(90, 120)
time.sleep(2)

print("Pan Left")
move(40, 120)
time.sleep(2)

print("Pan Right")
move(140, 120)
time.sleep(2)

print("Tilt Up")
move(90, 80)
time.sleep(2)

print("Tilt Down")
move(90, 150)
time.sleep(2)

print("Center")
move(90, 120)

sock.close()

print("Done")