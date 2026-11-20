"""Starts the Streamlit app and opens it in the browser. Used by run.bat / run.sh."""
import os
import socket
import subprocess
import sys
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))


def free_port(start=8501):
    for p in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start


if __name__ == "__main__":
    port = free_port()
    url = "http://localhost:%d" % port
    print("Starting... the app will open at " + url)
    threading.Timer(4.0, lambda: webbrowser.open(url)).start()
    try:
        subprocess.call([sys.executable, "-m", "streamlit", "run", os.path.join(HERE, "app.py"),
                         "--server.port", str(port), "--server.headless", "true",
                         "--browser.gatherUsageStats", "false"], cwd=HERE)
    except KeyboardInterrupt:
        pass
