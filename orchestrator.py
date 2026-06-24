#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AA2 Jail Project - Orchestrator (v1)
====================================
Single entry point for the whole multi-world setup:
  1. Start the patched (multi-client) PPeX server ONCE over the shared data.
  2. Launch each world (auto-launch via env var -> no manual "Launch" click),
     wait until it is in-game, then close its single-instance mutex so the
     next world can start.
  3. Visibility: the active world is shown + running; the others are hidden
     AND their process is SUSPENDED (no sound, no CPU, world frozen).
  4. Simple console switch (ENTER) as a demo of the instant switch.

Nothing about the mods is bypassed: each world loads its own savedconfig.lua
normally. The orchestrator only handles the surroundings (server, mutex, windows).

Foolproof shutdown: however you quit (q, Ctrl+C, closing the terminal, a game
window, or a crash) everything is resumed and terminated - no orphaned frozen
processes are ever left behind.
"""

import atexit
import ctypes
import ctypes.wintypes as wt
import json
import os
_BASE = os.path.dirname(os.path.abspath(__file__))
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import tkinter as tk

import playthrough_db as pdb   # per-playthrough LTM (chars/relationships/world_state)

# Save names are CJK (e.g. "NEW HOPE学園1年1組"); the console is often cp1252, so printing
# them raw would raise UnicodeEncodeError and crash. Make stdout/stderr lenient.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ----------------------------------------------------------------------------
# Configuration  (generic: more worlds = more entries)
# ----------------------------------------------------------------------------
DOTNET        = "dotnet"
PPEX_DLL      = _BASE + r"\_ppex_src\PPeXM64\bin\Release\netcoreapp3.1\PPeXM64.dll"
MUTEXFIND_DLL = _BASE + r"\_mutexfind\bin\Release\net8.0\mutexfind.dll"
# One shared server serves all worlds (identical mod data via copies/junctions):
SHARED_DATA   = _BASE + r"\school\data"
SERVER_LOG    = _BASE + r"\_ppex_server.log"
# Coupled jail saves live one-per-folder under here, keyed by the school save name (no .sav):
#   _playthroughs\<save name>\jail\   <- the single jail twin save for that playthrough
# jail's data\save\class is a junction the orchestrator points at the active twin before loading.
PLAYTHROUGHS  = _BASE + r"\_playthroughs"
SCHOOL_CLASS  = os.path.join(SHARED_DATA, "save", "class")   # school\data\save\class
INDEX_PATH    = os.path.join(PLAYTHROUGHS, "index.json")     # playthrough <-> jail-twin registry

GAME_CLASS = "__AA2Play_Class__"   # window class AND single-instance mutex name

WORLDS = [
    # save        = coupled class-save name (for reference/mapping; school<->jail = trivial mapping)
    # load_seq    = click sequence on the game's own Load menu, as (fx, fy) fractions of the window
    #               (resolution-independent). None = NO auto-load (the world is loaded manually).
    #
    # Design: school = "the game" (always the boot world, played normally by the user -> NO
    # automation, no mouse conflict). jail = "the DLC" (the roster-cap workaround): it boots only
    # to its title menu, gets suspended there, and is LAZY-LOADED into its coupled save the first
    # time the user enters it via the JAIL button (deliberate "enter the DLC" moment, input blocked
    # for the ~3s click sequence). The game's menu-load is the only crash-free load path (RE-proven:
    # function cold-load is impractical, the class container is created by the menu-load lifecycle).
    {"name": "school", "dir": _BASE + r"\school", "visible": True,  "color": "#3a6ea5",
     "load_seq": None},
    {"name": "jail",   "dir": _BASE + r"\jail",   "visible": False, "color": "#a53a3a",
     # jail has exactly ONE coupled save in its class folder -> "top slot" is unambiguous.
     "load_seq": [(0.344, 0.939), (0.422, 0.289), (0.640, 0.750)], "menu_wait": 4},
]

# ----------------------------------------------------------------------------
# Win32 via ctypes (64-bit safe: handles as c_void_p)
# ----------------------------------------------------------------------------
user32   = ctypes.WinDLL("user32",   use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll    = ctypes.WinDLL("ntdll")

user32.EnumWindows.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.EnumWindows.restype  = wt.BOOL
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.GetWindowThreadProcessId.restype  = wt.DWORD
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype  = ctypes.c_int
user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
user32.ShowWindow.restype  = wt.BOOL
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.SetForegroundWindow.restype  = wt.BOOL
user32.BringWindowToTop.argtypes = [wt.HWND]
user32.BringWindowToTop.restype  = wt.BOOL
user32.IsWindowVisible.argtypes = [wt.HWND]
user32.IsWindowVisible.restype  = wt.BOOL


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype  = wt.BOOL
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype  = wt.BOOL
user32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_void_p]
user32.mouse_event.restype  = None
# BlockInput: freeze the user's physical mouse/keyboard while we run the synthetic
# click sequence, so a stray hand movement can't divert the clicks. Our own SetCursorPos/
# mouse_event still work. (May return 0 if the game runs at higher integrity than us ->
# then run the orchestrator as admin; Ctrl+Alt+Del always lifts the block as a safety net.)
user32.BlockInput.argtypes = [wt.BOOL]
user32.BlockInput.restype  = wt.BOOL

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004

ntdll.NtSuspendProcess.argtypes = [ctypes.c_void_p]
ntdll.NtSuspendProcess.restype  = ctypes.c_long
ntdll.NtResumeProcess.argtypes  = [ctypes.c_void_p]
ntdll.NtResumeProcess.restype   = ctypes.c_long
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype  = ctypes.c_void_p
kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype  = wt.BOOL
kernel32.SetConsoleCtrlHandler.argtypes = [ctypes.c_void_p, wt.BOOL]
kernel32.SetConsoleCtrlHandler.restype  = wt.BOOL

SW_HIDE = 0
SW_SHOW = 5
SW_RESTORE = 9
PROCESS_SUSPEND_RESUME = 0x0800

ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def suspend_process(pid):
    h = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if h:
        ntdll.NtSuspendProcess(h)
        kernel32.CloseHandle(h)


def resume_process(pid):
    h = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if h:
        ntdll.NtResumeProcess(h)
        kernel32.CloseHandle(h)


def find_game_hwnd(pid, timeout=90):
    """Wait until the game window (__AA2Play_Class__) of the PID exists, return its HWND."""
    found = {"hwnd": None}

    def _cb(hwnd, lparam):
        wpid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value != pid:
            return True
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        if buf.value == GAME_CLASS:
            found["hwnd"] = hwnd
            return False
        return True

    cb = ENUMPROC(_cb)
    end = time.time() + timeout
    while time.time() < end:
        found["hwnd"] = None
        user32.EnumWindows(cb, 0)
        if found["hwnd"]:
            return found["hwnd"]
        time.sleep(0.5)
    return None


# ----------------------------------------------------------------------------
# Foolproof shutdown
# ----------------------------------------------------------------------------
_server_proc = None
_cleanup_done = False
_cleanup_lock = threading.Lock()


def cleanup(*_args):
    """Idempotent teardown: resume every world (so nothing stays frozen), then
    force-kill all games and the server. Safe to call from any exit path."""
    global _cleanup_done
    with _cleanup_lock:
        if _cleanup_done:
            return
        _cleanup_done = True

    print("\n[*] Shutting down (resuming + closing all games and the server)...")
    # Resume first so no process is ever left suspended/invisible.
    for w in WORLDS:
        if w.get("pid"):
            resume_process(w["pid"])
    # Terminate game processes (force + whole tree; works on suspended too).
    for w in WORLDS:
        pid = w.get("pid")
        if pid:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True)
    if _server_proc and _server_proc.poll() is None:
        try:
            _server_proc.terminate()
        except Exception:
            pass
    print("[+] Done.")


# Keep a reference so the console handler callback is not garbage-collected.
def _console_ctrl_handler(ctrl_type):
    cleanup()
    return 0  # allow default processing (process will exit afterwards)


_CONSOLE_HANDLER = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)(_console_ctrl_handler)


def install_shutdown_hooks():
    atexit.register(cleanup)
    try:
        signal.signal(signal.SIGINT, lambda *a: (cleanup(), os._exit(0)))
        signal.signal(signal.SIGTERM, lambda *a: (cleanup(), os._exit(0)))
    except Exception:
        pass
    kernel32.SetConsoleCtrlHandler(_CONSOLE_HANDLER, True)


def watchdog():
    """If any game or the server dies unexpectedly, tear everything down so no
    frozen/hidden process is orphaned."""
    while not _cleanup_done:
        for w in WORLDS:
            if w.get("restarting"):
                continue   # coupler is intentionally killing+relaunching this world
            proc = w.get("proc")
            if proc is not None and proc.poll() is not None:
                print(f"\n[!] World '{w['name']}' exited - shutting everything down.")
                cleanup()
                os._exit(0)
        if _server_proc is not None and _server_proc.poll() is not None:
            print("\n[!] PPeX server exited - shutting everything down.")
            cleanup()
            os._exit(0)
        time.sleep(2)


# ----------------------------------------------------------------------------
# PPeX server (patched, multi-client)
# ----------------------------------------------------------------------------
def start_server():
    global _server_proc
    print(f"[*] Starting shared PPeX server over: {SHARED_DATA}")
    logf = open(SERVER_LOG, "w", encoding="utf-8", errors="replace")
    # Keep stdin=PIPE open -> the server's ReadLine loop blocks instead of
    # crashing on EOF.
    _server_proc = subprocess.Popen(
        [DOTNET, PPEX_DLL, SHARED_DATA],
        stdout=logf, stderr=logf, stdin=subprocess.PIPE,
        cwd=os.path.dirname(PPEX_DLL),
    )
    return _server_proc


def wait_server_ready(timeout=120):
    print("[*] Waiting for server to finish loading ...")
    end = time.time() + timeout
    while time.time() < end:
        try:
            with open(SERVER_LOG, "r", encoding="utf-8", errors="replace") as f:
                if "Preloading complete" in f.read():
                    print("[+] Server ready.")
                    return True
        except FileNotFoundError:
            pass
        time.sleep(1)
    print("[!] Server did not become ready in time.")
    return False


# ----------------------------------------------------------------------------
# Single-instance mutex (version-independent, no exe patch)
# ----------------------------------------------------------------------------
def close_mutex(pid=None):
    args = [DOTNET, MUTEXFIND_DLL, "close"]
    if pid:
        args.append(str(pid))
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=30).stdout
    except subprocess.TimeoutExpired:
        return False
    return "CLOSED" in out


def wait_and_close_mutex(pid, timeout=120):
    """The mutex only appears once the game is fully started -> retry until
    it exists and gets closed."""
    print(f"    waiting for single-instance mutex (PID {pid}) ...")
    end = time.time() + timeout
    while time.time() < end:
        if close_mutex(pid):
            print(f"    [+] mutex closed (PID {pid}).")
            return True
        time.sleep(1.5)
    print(f"    [!] mutex not found/closed (PID {pid}).")
    return False


# ----------------------------------------------------------------------------
# World launching
# ----------------------------------------------------------------------------
def launch_world(w):
    exe = os.path.join(w["dir"], "AA2Play.exe")
    print(f"[*] Starting world '{w['name']}' ({exe})")
    env = dict(os.environ)
    env["AA2_ORCH_AUTOLAUNCH"] = "1"   # launcher auto-proceeds (no click)
    p = subprocess.Popen([exe], cwd=w["dir"], env=env)
    w["pid"] = p.pid
    w["proc"] = p
    return p


def click_window(world, fx, fy):
    """Left-click at a fraction (fx,fy) of the world's window. Window must be visible+foreground
    because the game's rendered menu polls the real cursor (WM messages are ignored)."""
    if not world.get("hwnd"):
        return
    r = RECT()
    if not user32.GetWindowRect(world["hwnd"], ctypes.byref(r)):
        return
    x = int(r.left + (r.right - r.left) * fx)
    y = int(r.top + (r.bottom - r.top) * fy)
    print(f"      click '{world['name']}' frac=({fx:.3f},{fy:.3f}) -> px=({x},{y})  "
          f"win=({r.left},{r.top})..({r.right},{r.bottom}) {r.right-r.left}x{r.bottom-r.top}")
    user32.ShowWindow(world["hwnd"], SW_SHOW)
    user32.SetForegroundWindow(world["hwnd"])
    time.sleep(0.25)
    user32.SetCursorPos(x, y)
    time.sleep(0.12)
    # The rendered menu POLLS the mouse-button state (DirectInput-style), so the button must
    # stay down across at least one poll tick (~0.2-0.25s) or the click is swallowed. A
    # zero-length down->up (the old code) only registered by luck. RE-proven: see RE_LADEFUNKTION.md.
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)
    time.sleep(world.get("click_hold", 0.25))
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)


def read_save_name(world):
    """Read the loaded save name the orch_savename mod wrote (e.g. 'NEW HOPE...組.sav').
    Returns the name WITHOUT the .sav extension (the playthrough key), or None."""
    path = os.path.join(world["dir"], "_orch_save.flag")
    try:
        with open(path, encoding="utf-8") as f:
            v = f.read().strip()
    except Exception:
        return None
    if not v:
        return None
    return v[:-4] if v.lower().endswith(".sav") else v


def switch_jail_save(jail_world, key):
    """Point jail's class-save junction at playthrough <key>'s jail twin folder. Removing a
    junction only drops the reparse point - it does NOT delete the target files. Returns True
    if the junction now points at an existing twin."""
    junction = os.path.join(jail_world["dir"], "data", "save", "class")
    target = os.path.join(PLAYTHROUGHS, key, "jail")
    if not os.path.isdir(target):
        print(f"    [!] no jail twin for '{key}' at {target} - keeping current junction.")
        return False
    if os.path.lexists(junction):
        try:
            os.rmdir(junction)   # detaches a junction or removes an empty dir; target untouched
        except OSError as e:
            print(f"    [!] could not detach old junction ({e}).")
            return False
    rc = subprocess.run(["cmd", "/c", "mklink", "/J", junction, target],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if rc.returncode != 0:
        print(f"    [!] mklink failed: {(rc.stdout or '').strip()} {(rc.stderr or '').strip()}")
        return False
    print(f"    [+] jail save coupled -> '{key}'")
    return True


# ----------------------------------------------------------------------------
# Playthrough lifecycle: one jail twin save per school save, tracked in index.json
#   new school save (appears while running) -> auto-copy a jail twin
#   deleted school save                     -> delete its twin + index entry
#   pre-existing school save without a twin -> needs_port (one-time manual setup)
# The intelligent roster transfer (RPG layer) is deliberately NOT here - that needs
# save-format writing ("point 9") and comes later; this is just the folder/DB plumbing.
# ----------------------------------------------------------------------------
def list_school_saves():
    """School playthrough keys = save base names (no .sav) in school\\data\\save\\class."""
    try:
        return [f[:-4] for f in os.listdir(SCHOOL_CLASS) if f.lower().endswith(".sav")]
    except OSError:
        return []


def twin_sav_path(key):
    return os.path.join(PLAYTHROUGHS, key, "jail", key + ".sav")


def load_index():
    try:
        with open(INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_index(idx):
    os.makedirs(PLAYTHROUGHS, exist_ok=True)
    tmp = INDEX_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    os.replace(tmp, INDEX_PATH)


def create_twin(key):
    """Copy school save <key>.sav (+.json) into _playthroughs\\<key>\\jail as the jail twin."""
    twin_dir = os.path.join(PLAYTHROUGHS, key, "jail")
    try:
        os.makedirs(twin_dir, exist_ok=True)
        ok = False
        for ext in (".sav", ".json"):
            src = os.path.join(SCHOOL_CLASS, key + ext)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(twin_dir, key + ext))
                ok = ok or ext == ".sav"
        return ok
    except OSError as e:
        print(f"[!] could not create jail twin for '{key}': {e}")
        return False


def delete_twin(key):
    twin_root = os.path.join(PLAYTHROUGHS, key)
    try:
        if os.path.isdir(twin_root):
            shutil.rmtree(twin_root)
    except OSError as e:
        print(f"[!] could not delete jail twin for '{key}': {e}")


def scan_playthroughs():
    """Refresh the index from current school saves. Pre-existing saves WITHOUT a twin become
    needs_port (manual one-time setup). Returns the set of school keys present right now."""
    idx = load_index()
    school = set(list_school_saves())
    for key in school:
        entry = idx.get(key, {})
        entry.setdefault("origin", "preexisting")
        entry["status"] = "ready" if os.path.exists(twin_sav_path(key)) else "needs_port"
        idx[key] = entry
    for key in list(idx):              # school save gone -> drop twin + entry
        if key not in school:
            delete_twin(key)
            del idx[key]
    save_index(idx)
    need = [k for k, v in idx.items() if v.get("status") == "needs_port"]
    if need:
        print(f"[*] {len(need)} existing save(s) need a manual jail twin (needs_port):")
        for k in need:
            print(f"      - {k}   (put the ported save at _playthroughs\\{k}\\jail\\{k}.sav)")
    return school


def playthrough_watcher(baseline):
    """Background: auto-create twins for NEW saves, drop twins for deleted saves, and pick up
    manually-ported twins. `baseline` = saves present at startup (those are NOT auto-copied)."""
    seen = set(baseline)
    while not _cleanup_done:
        try:
            cur = set(list_school_saves())
            idx = load_index()
            for key in cur - seen:                       # new save -> auto-create twin
                if os.path.exists(twin_sav_path(key)):
                    continue
                if create_twin(key):
                    idx[key] = {"status": "ready", "origin": "auto"}
                    print(f"[+] new playthrough '{key}' -> jail twin auto-created.")
                else:
                    idx[key] = {"status": "needs_port", "origin": "auto_failed"}
            for key in list(idx):                        # deleted save -> remove twin + entry
                if key not in cur:
                    delete_twin(key)
                    del idx[key]
                    print(f"[-] playthrough '{key}' deleted -> jail twin removed.")
            for key in cur:                              # manual twin now present -> ready
                if idx.get(key, {}).get("status") == "needs_port" and os.path.exists(twin_sav_path(key)):
                    idx[key]["status"] = "ready"
                    print(f"[+] '{key}' now has a jail twin -> ready.")
            save_index(idx)
            seen = cur
        except Exception as e:
            print(f"[!] playthrough watcher error: {e}")
        time.sleep(5)


def boot_load(world):
    """Drive the game's OWN menu-load: run the configured click sequence (with physical input
    blocked so the user's hand can't divert it), then wait until in-world. The caller must already
    have made this world the sole visible/foreground window (set_active). Returns True if in-world.
    (Function-call cold-load is impractical per RE; the menu-load is the crash-free path.)"""
    seq = world.get("load_seq")
    if not seq:
        return False  # no auto-load configured -> world is loaded manually
    print(f"    loading coupled save for '{world['name']}' ...")
    user32.ShowWindow(world["hwnd"], SW_SHOW)
    user32.SetForegroundWindow(world["hwnd"])
    time.sleep(world.get("menu_wait", 4))   # let the title menu (re)render after resume
    blocked = bool(user32.BlockInput(True))
    if not blocked:
        print("      [!] BlockInput failed (run orchestrator as admin to freeze input during load).")
    try:
        for (fx, fy) in seq:
            click_window(world, fx, fy)
            time.sleep(world.get("click_delay", 0.9))
    finally:
        if blocked:
            user32.BlockInput(False)
    # wait until in-world (input NOT blocked here): logperiod writes a real period (>=1); 0 = no class
    end = time.time() + 60
    while time.time() < end:
        p = read_period(world)
        if p and p >= 1:
            print(f"    [+] '{world['name']}' is in-world (period {p}).")
            return True
        time.sleep(0.5)
    print(f"    [!] '{world['name']}' did not reach in-world (check load_seq coords/menu_wait).")
    return False


def launch_and_register(w):
    """Phase 1 per world: start it, close its single-instance mutex (so the next
    world can start), and grab its window handle. NO loading yet - loading happens
    later, isolated in main() phase 2 (set_active + boot_load)."""
    launch_world(w)
    # wait until in-game (mutex exists) + close it so the next world can start
    wait_and_close_mutex(w["pid"])
    hwnd = find_game_hwnd(w["pid"])
    w["hwnd"] = hwnd
    if hwnd:
        print(f"    [+] game window found (HWND {hwnd:#x}).")
    else:
        print(f"    [!] no game window found for '{w['name']}'.")


def restart_world(w):
    """Kill and relaunch a world back to a fresh title menu. Needed before loading a DIFFERENT
    save into jail: loading over a live class is the known live-reload crash (0x10E9C8); a fresh
    process cold-loads cleanly. Blocks until the new window is up. The 'restarting' flag tells the
    watchdog this exit is intentional (so it doesn't tear everything down)."""
    print(f"[*] restarting '{w['name']}' to a fresh title menu (save switch) ...")
    w["restarting"] = True
    try:
        pid = w.get("pid")
        if pid:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        w["loaded"] = False
        w["loaded_key"] = None
        w["hwnd"] = None
        w["pid"] = None
        w["proc"] = None
        time.sleep(1.0)
        launch_and_register(w)   # relaunch, close mutex, grab the new window handle
    finally:
        w["restarting"] = False


# ----------------------------------------------------------------------------
# Visibility / switch
# ----------------------------------------------------------------------------
# Shared between run_ui (UI thread) and the background jail coupler. _switch_lock serializes
# every jail load / world switch so they never overlap; _active_world = currently visible world.
_switch_lock = threading.RLock()
_active_world = None


def set_active(active_name):
    global _active_world
    _active_world = active_name
    # Active world: resume, show, bring to front.
    for w in WORLDS:
        if w["name"] != active_name:
            continue
        if w.get("pid"):
            resume_process(w["pid"])
        if w.get("hwnd"):
            user32.ShowWindow(w["hwnd"], SW_RESTORE)
            user32.ShowWindow(w["hwnd"], SW_SHOW)
            user32.BringWindowToTop(w["hwnd"])
            user32.SetForegroundWindow(w["hwnd"])
    # Inactive worlds: hide AND freeze (no sound/CPU, world stands still).
    for w in WORLDS:
        if w["name"] == active_name:
            continue
        if w.get("hwnd"):
            user32.ShowWindow(w["hwnd"], SW_HIDE)
        if w.get("pid"):
            suspend_process(w["pid"])


# ----------------------------------------------------------------------------
# In-game overlay button (shown on the home screen = period 9)
# ----------------------------------------------------------------------------
HOME_PERIOD = 9          # "home again" screen (Quit/Title/Save/Load/sleep)
# Position relative to the window size (resolution-independent). Tweak if needed:
BTN_RIGHT_FRAC  = 0.18   # button left edge, this fraction of width in from the right
BTN_BOTTOM_FRAC = 0.10   # button top edge, this fraction of height up from the bottom


def read_period(world):
    # Only trust a FRESHLY written flag: logperiod's timer writes every 0.5s while in a class;
    # at the menu it goes stale -> treat as "not in-world" so the switch button hides (bug fix).
    path = os.path.join(world["dir"], "_orch_period.flag")
    try:
        if time.time() - os.path.getmtime(path) > 2.0:
            return None
        with open(path) as f:
            v = int(f.read().strip())
            world["_period"] = v
            return v
    except Exception:
        return world.get("_period")


# ----------------------------------------------------------------------------
# SSOT transfer pipeline (model A): commit-on-save -> journal -> derive-on-load.
# School writes a commit log on save; we ingest it into the per-playthrough journal (memory.db),
# then derive jail's inmate list for the day school is currently on and hand it to jail_intake.
# ----------------------------------------------------------------------------
def read_day(world):
    """The game day (nDays) the world is currently on, written by logperiod; None if unknown."""
    try:
        with open(os.path.join(world["dir"], "_orch_day.flag")) as f:
            return int(f.read().strip())
    except Exception:
        return None


_CARD_INDEX = None


def _card_index():
    """Map normalized char name -> card .png filename in jail's card folders (built once)."""
    global _CARD_INDEX
    if _CARD_INDEX is not None:
        return _CARD_INDEX
    idx = {}
    jail = next((w for w in WORLDS if w.get("load_seq")), None)
    if jail:
        base = os.path.join(jail["dir"], "data", "save")
        for sub in ("Female", "Male", "female", "male"):
            d = os.path.join(base, sub)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if fn.lower().endswith(".png"):
                        idx.setdefault(re.sub(r"[^a-z]", "", fn[:-4].lower()), fn)
    _CARD_INDEX = idx
    return idx


def resolve_card_file(name):
    """The card .png filename for a char name (bare name, AddCard picks the folder by gender), or ''."""
    return _card_index().get(re.sub(r"[^a-z]", "", name.lower()), "")


def write_jail_inmates(residents):
    """Write the SSOT-derived inmate list jail_intake reads. One line per inmate:
    '<name>\\t<cardfile>\\t<gender>' so jail_intake can AddCard a missing inmate (cardfile) AND kick
    non-inmates -> full roster reconstruction from the SSOT. Atomic write."""
    jail = next((w for w in WORLDS if w.get("load_seq")), None)
    if not jail:
        return
    path = os.path.join(jail["dir"], "_orch_jail_inmates.flag")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("# jail inmates (SSOT-derived): <name>\\t<cardfile>\\t<gender>\\t<self>. EMPTY = none.\n")
        for r in residents:
            f.write("%s\t%s\t%s\t%s\n" % (r["char_id"], resolve_card_file(r["char_id"]),
                                          r.get("gender", 1), r.get("self_data", "") or ""))
    os.replace(tmp, path)


def write_jail_rels(con, inmate_names):
    """2c: write the relationships originating at the current inmates so jail_intake can restore those
    whose counterpart is also present (another inmate, or the PC). One line per directed pair:
    <from>\\t<to>\\t<love>\\t<like>\\t<dislike>\\t<hate>. Atomic."""
    jail = next((w for w in WORLDS if w.get("load_seq")), None)
    if not jail:
        return
    path = os.path.join(jail["dir"], "_orch_jail_rels.flag")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("# jail relationships (SSOT): <from>\\t<to>\\t<love>\\t<like>\\t<dislike>\\t<hate>\n")
        for nm in inmate_names:
            for r in pdb.char_rels_from(con, nm):
                f.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (nm, r["to_id"], r["love"], r["liking"],
                                                      r["disliking"], r["hate"]))
    os.replace(tmp, path)


def transfer_sync(school_world):
    """Background: ingest school's commit log into the active playthrough's journal, then derive the
    jail inmate list for the day school is on. Commit-on-save + derive-on-load => jail mirrors the last
    SAVED school state, day-keyed (loading an older save rolls the jail roster back automatically)."""
    commits_path = os.path.join(school_world["dir"], "_orch_slave_commits.flag")
    rel_snapshot_path = os.path.join(school_world["dir"], "_orch_rel_snapshot.flag")
    last = None
    while not _cleanup_done:
        try:
            key = read_save_name(school_world)
            if key and os.path.exists(twin_sav_path(key)):
                ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                con = pdb.connect(os.path.join(PLAYTHROUGHS, key, "memory.db"))
                try:
                    pdb.ingest_transfer_commits(con, commits_path, ts)
                    pdb.ingest_rel_snapshot(con, rel_snapshot_path, ts)   # continuous relationship memory
                    nday = read_day(school_world)
                    if nday is not None:
                        residents = pdb.residents_as_of(con, nday, "jail")
                        residents.sort(key=lambda r: r["char_id"])
                        for r in residents:   # augment each inmate's self with SSOT-derived social_wealth
                            sw, bonds = pdb.social_wealth(con, r["char_id"])
                            base = (r.get("self_data") or "").rstrip(";")
                            r["self_data"] = (base + ";" if base else "") + "social_wealth=%s;bonds=%d" % (sw, bonds)
                        names = [r["char_id"] for r in residents]
                        sig = (key, nday, tuple(names))
                        if sig != last:
                            write_jail_inmates(residents)
                            write_jail_rels(con, names)               # 2c: rels among current inmates
                            print(f"[*] jail roster for '{key}' day {nday}: {names or '(empty)'}")
                            last = sig
                finally:
                    con.close()
        except Exception as e:
            print(f"[!] transfer_sync error: {e}")
        time.sleep(1.5)


def _transfer_to_jail(key):
    """Snapshot school's char values into the playthrough DB, then inject them into jail's .json
    so jail loads WITH the school development. Phase 'all 1:1' = proof that the JSON bridge reaches
    the game. (Source = school's LAST SAVED .json; live unsaved values would need an in-game hook.)
    Refinements later: which fields transfer, relationship condensation, roster-exact targeting."""
    school_json = os.path.join(SCHOOL_CLASS, key + ".json")
    jail_json = os.path.join(PLAYTHROUGHS, key, "jail", key + ".json")
    db_path = os.path.join(PLAYTHROUGHS, key, "memory.db")
    if not os.path.exists(school_json) or not os.path.exists(jail_json):
        print("    [i] transfer skipped (school or jail .json missing).")
        return
    try:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        con = pdb.connect(db_path)
        n_snap = pdb.snapshot_chars_from_json(con, "school", school_json, ts)
        n_inj = pdb.inject_chars_to_json(con, jail_json, ts)
        con.close()
        print(f"    [+] transfer: snapshot {n_snap} school chars -> injected {n_inj} blocks into jail.")
    except Exception as e:
        print(f"    [!] transfer failed (non-fatal): {e}")


def _couple_jail(jw, key, school_name):
    """(Held under _switch_lock.) Snapshot+inject school's development into jail's save, then bring
    jail forward, point its junction at <key>'s twin, load it, return to school. Sets
    jw['loaded_key'] = key on success (None on failure)."""
    print(f"[*] coupling jail to active save '{key}' ...")
    # _transfer_to_jail(key)  # PROVEN: the json bridge reaches the game (marker test, 2026-06-24).
    #   Parked: "all 1:1" overwrites jail with school AND is roster-seat-naive (writes historical
    #   "<seat> name" blocks). Re-enable once the real transfer (name->current seat, which fields,
    #   relationship condensation) lands. See HANDOVER_jail-coupling.
    if not switch_jail_save(jw, key):
        return
    set_active(jw["name"])
    time.sleep(0.8)
    if boot_load(jw):
        jw["loaded"] = True
        jw["loaded_key"] = key
        print(f"[+] jail coupled to '{key}' - JAIL switch ready.")
    else:
        jw["loaded"] = False
        jw["loaded_key"] = None
        print(f"[!] jail load failed for '{key}' (check load_seq coords / menu_wait).")
    set_active(school_name)   # back to school


def jail_coupler(school_world):
    """Background: keep jail coupled to school's ACTIVE save. While the user is in school and
    in-world with a save that HAS a twin, and jail isn't already loaded for it, bring jail forward
    once and load it - so the JAIL switch is instant and always the right world. A save without a
    twin (unsaved, or needs_port) simply leaves jail unavailable (no stale world is shown)."""
    school_name = school_world["name"]
    jw = next((w for w in WORLDS if w.get("load_seq")), None)
    if not jw:
        return
    while not _cleanup_done:
        try:
            key = read_save_name(school_world)
            in_world = (read_period(school_world) or 0) >= 1
            # Couple when jail isn't already loaded for the active save. If jail is in a DIFFERENT
            # class, restart it to a fresh title first (loading over a live class is the known
            # live-reload crash 0x10E9C8). couple_attempted guards against retrying a failed key
            # forever (jail blinking / restarting every 2s).
            if (_active_world == school_name and in_world and key
                    and jw.get("loaded_key") != key
                    and jw.get("couple_attempted") != key
                    and os.path.exists(twin_sav_path(key))):
                if _switch_lock.acquire(blocking=False):
                    try:
                        if (_active_world == school_name
                                and read_save_name(school_world) == key
                                and jw.get("loaded_key") != key):
                            jw["couple_attempted"] = key
                            if jw.get("loaded_key") is not None:
                                restart_world(jw)   # jail in a different class -> fresh title first
                            _couple_jail(jw, key, school_name)
                    finally:
                        _switch_lock.release()
        except Exception as e:
            print(f"[!] jail coupler error: {e}")
        time.sleep(2)


def run_ui(school_world):
    """Two topmost overlays over the active game window:
       - a persistent world-name label (top-center) so you always know which world you are in,
       - a switch button (next to 'sleep') shown only on the home screen (period 9) AND only when
         the target is ready (jail must be coupled+loaded for the CURRENT school save).
    The background jail coupler keeps jail loaded, so switching is instant."""
    root = tk.Tk()
    root.withdraw()

    # persistent world-name label (always visible while the active window is shown)
    label = tk.Toplevel(root)
    label.overrideredirect(True)
    label.attributes("-topmost", True)
    lbl = tk.Label(label, font=("Segoe UI", 11, "bold"), fg="white", padx=12, pady=4)
    lbl.pack()
    label.withdraw()

    # switch button (home screen only)
    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)
    overlay.configure(bg="#caa54a")

    def jail_ready_for_current():
        """True if jail is loaded for the save school currently has (safe/meaningful to switch)."""
        jw = next((w for w in WORLDS if w.get("load_seq")), None)
        if not jw:
            return True
        cur = read_save_name(school_world)
        return bool(cur) and jw.get("loaded_key") == cur

    def do_switch():
        # Non-blocking: if the coupler is loading jail right now, ignore the click.
        if not _switch_lock.acquire(blocking=False):
            return
        try:
            names = [w["name"] for w in WORLDS]
            i = names.index(_active_world)
            target = names[(i + 1) % len(names)]
            tw = next(w for w in WORLDS if w["name"] == target)
            if tw.get("load_seq") and not jail_ready_for_current():
                print("[!] jail not ready for the current save (save the class first / wait).")
                return
            set_active(target)   # instant: jail is already loaded by the coupler
        finally:
            _switch_lock.release()

    btn = tk.Button(overlay, command=do_switch, bg="#caa54a", fg="black",
                    activebackground="#e0bb58", font=("Segoe UI", 13, "bold"),
                    relief="raised", bd=3, width=7, height=1)
    btn.pack(padx=2, pady=2)
    overlay.withdraw()

    def poll():
        aw = next((w for w in WORLDS if w["name"] == _active_world), None)
        visible = bool(aw and aw.get("hwnd") and user32.IsWindowVisible(aw["hwnd"]))
        r = RECT()
        have_rect = visible and bool(user32.GetWindowRect(aw["hwnd"], ctypes.byref(r)))
        w_px = (r.right - r.left) if have_rect else 0
        h_px = (r.bottom - r.top) if have_rect else 0

        # persistent world label (top-center, clear of the Sun/book corners)
        if have_rect:
            lbl.configure(text=aw["name"].upper(), bg=aw.get("color", "#333333"))
            label.update_idletasks()
            lw = label.winfo_width()
            label.geometry("+%d+%d" % (r.left + (w_px - lw) // 2, r.top + int(h_px * 0.012)))
            label.deiconify(); label.attributes("-topmost", True); label.lift()
        else:
            label.withdraw()

        # switch button: on the home screen (period 9) AND only if the target world is ready
        # (jail must be coupled+loaded for the current save; school is always ready).
        other = next((w for w in WORLDS if w["name"] != _active_world), None)
        target_ready = not (other and other.get("load_seq")) or jail_ready_for_current()
        show_btn = bool(have_rect and other and read_period(aw) == HOME_PERIOD and target_ready)
        if show_btn:
            x = int(r.right - w_px * BTN_RIGHT_FRAC)
            y = int(r.bottom - h_px * BTN_BOTTOM_FRAC)
            overlay.geometry("+%d+%d" % (x, y))
            btn.configure(text=other["name"].upper())
            overlay.deiconify(); overlay.attributes("-topmost", True); overlay.lift()
        else:
            overlay.withdraw()

        root.after(300, poll)

    root.after(300, poll)
    root.mainloop()


def mirror_config_school_to_jail():
    """Copy school's savedconfig.lua over jail's at startup so jail launches with the SAME mod
    list the user maintains in school. Never disables anything. Guarded: if school's config is
    empty/missing (corruption), we skip rather than wipe jail's."""
    school = next((w for w in WORLDS if w.get("visible")), None)
    jail = next((w for w in WORLDS if w.get("load_seq")), None)
    if not (school and jail):
        return
    src = os.path.join(school["dir"], "AAUnlimited", "savedconfig.lua")
    dst = os.path.join(jail["dir"], "AAUnlimited", "savedconfig.lua")
    try:
        if os.path.exists(src) and os.path.getsize(src) > 50:   # >50B = real config, not a stub
            shutil.copy2(src, dst)
            print("[*] mirrored school's mod list -> jail (savedconfig).")
        else:
            print("[!] school savedconfig looks empty/corrupt - NOT mirroring (kept jail's).")
    except OSError as e:
        print(f"[!] could not mirror config to jail: {e}")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    install_shutdown_hooks()

    start_server()
    if not wait_server_ready():
        cleanup()
        return

    # jail launches with SCHOOL's mod list: mirror school's savedconfig over jail's, so the user
    # maintains one list (school) and jail stays in sync. We never disable anything - jail just
    # gets whatever school has (win10fix etc.). Helper mods exist in both mod folders.
    mirror_config_school_to_jail()

    # Launch every world, close its mutex, grab its window handle. NO auto-load here:
    # school is played manually (the user loads their save); jail just reaches its title
    # menu and waits there, suspended, until the user enters it via the JAIL button.
    for w in WORLDS:
        launch_and_register(w)

    threading.Thread(target=watchdog, daemon=True).start()

    # Playthrough registry: mark pre-existing saves without a twin as needs_port, then watch
    # for new/deleted saves in the background (new -> auto-twin, deleted -> remove twin).
    baseline = scan_playthroughs()
    threading.Thread(target=playthrough_watcher, args=(baseline,), daemon=True).start()

    # Active = school first: the user loads their save normally. jail stays hidden + suspended.
    active = next((w["name"] for w in WORLDS if w["visible"]), WORLDS[0]["name"])
    school_world = next(w for w in WORLDS if w["name"] == active)
    set_active(active)
    print(f"\n[+] Worlds up. Active: '{active}'. Load your save normally now.")
    print("    jail follows your active save automatically: once you're in-world with a SAVED")
    print("    class, jail comes forward once (~3s, input frozen) to load its coupled twin, then")
    print("    goes back - the JAIL button then appears on the home screen. A brand-new, unsaved")
    print("    class has no twin yet: save it first, then jail couples on its own.\n")

    # Background coupler: keep jail loaded for whatever save school currently has (handles the
    # first load, saving a new class, and switching between saves).
    threading.Thread(target=jail_coupler, args=(school_world,), daemon=True).start()

    # SSOT transfer pipeline: ingest school's save-time commits into the journal and derive jail's
    # inmate list for the day school is on (model A: commit-on-save, derive-on-load, day-keyed).
    threading.Thread(target=transfer_sync, args=(school_world,), daemon=True).start()

    try:
        run_ui(school_world)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
