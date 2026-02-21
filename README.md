

---

# 🎙️ Remote Mic Streamer & Dashboard

A powerful **Python-based remote audio streaming system** that allows you to capture microphone input from a client machine and stream it in real-time to a central Dashboard. This project includes a GUI for the server and a payload builder to create standalone executables for clients.

## ✨ Key Features

* **Real-time Audio Streaming:** High-quality 44100Hz mono audio streaming.
* **Centralized Dashboard:** Manage multiple incoming connections from a single PyQt6 interface.
* **Payload Builder:** Built-in tool to compile the `audio_sender.py` into a hidden Windows executable (.exe) using PyInstaller.
* **Auto-Reconnect:** The client (payload) automatically tries to reconnect if the connection to the server is lost.
* **Recording Support:** Easily record incoming audio streams for later review.
* **Modern UI:** Clean and responsive dashboard built with PyQt6.

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **GUI Framework:** PyQt6
* **Audio Library:** `sounddevice`, `numpy`
* **Networking:** Socket programming (TCP)
* **Packaging:** PyInstaller

---

## 🚀 Getting Started

### 1. Prerequisites

Make sure you have Python installed on your system. You will also need to install the required libraries:

```bash
pip install -r requirements.txt

```

### 2. Running the Dashboard (Server)

Launch the main dashboard to start listening for connections:

```bash
python mic_streamer.py

```

### 3. Creating the Client Payload

1. Open the **Builder** tab in the Dashboard.
2. Enter your **Server IP** (e.g., `127.0.0.1` for local or your Public IP for remote).
3. Enter the **Port** (default is `50005`).
4. Click **"Build Payload (.exe)"**.
5. The compiled executable will be located in the `dist/` folder.

---

## 📂 File Structure

| File | Description |
| --- | --- |
| `mic_streamer.py` | The main Server Dashboard application (GUI). |
| `audio_sender.py` | The client-side script that captures and sends audio. |
| `settings.json` | Stores your dashboard configuration (IP, Port, etc.). |
| `requirements.txt` | List of necessary Python packages. |
| `audio_sender_payload.spec` | PyInstaller configuration for building the executable. |

---

## ⚠️ Disclaimer

This project is created for **educational purposes** and **authorized monitoring** only. Unauthorized access to a computer system or recording audio without consent is illegal. The developer is not responsible for any misuse of this software.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://www.google.com/search?q=https://github.com/your-username/your-repo-name/issues).

---

*Developed with ❤️ by [https://github.com/lochana2005]*

---

