import os
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Dev-only: startet NUR school (+ PPeX) am Hauptmenue, fuer die CE-Debug-Session.
Kein jail, kein Mutex-Close, kein Fenster-Switching. Haelt PPeX-stdin offen (bleibt am Leben)."""
import subprocess, os, time, sys

PPEX_DLL    = _BASE + r"\_ppex_src\PPeXM64\bin\Release\netcoreapp3.1\PPeXM64.dll"
SHARED_DATA = _BASE + r"\school\data"
SCHOOL      = _BASE + r"\school"
SERVER_LOG  = _BASE + r"\_ppex_server.log"

logf = open(SERVER_LOG, "w", encoding="utf-8", errors="replace")
print("[*] PPeX starten ...", flush=True)
srv = subprocess.Popen(["dotnet", PPEX_DLL, SHARED_DATA],
                       stdout=logf, stderr=logf, stdin=subprocess.PIPE,
                       cwd=os.path.dirname(PPEX_DLL))
end = time.time() + 120
ready = False
while time.time() < end:
    try:
        with open(SERVER_LOG, "r", encoding="utf-8", errors="replace") as f:
            if "Preloading complete" in f.read():
                ready = True
                break
    except FileNotFoundError:
        pass
    if srv.poll() is not None:
        print("[!] PPeX-Server beendet sich unerwartet.", flush=True); sys.exit(1)
    time.sleep(1)
print(f"[+] Server ready={ready}", flush=True)

env = dict(os.environ); env["AA2_ORCH_AUTOLAUNCH"] = "1"
game = subprocess.Popen([os.path.join(SCHOOL, "AA2Play.exe")], cwd=SCHOOL, env=env)
print(f"[+] school AA2Play PID = {game.pid}", flush=True)
print("[*] (laeuft; haelt PPeX-stdin offen. Beenden = dieses Skript killen.)", flush=True)
game.wait()
