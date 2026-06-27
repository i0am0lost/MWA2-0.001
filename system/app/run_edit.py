#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_edit.py - launch the AA2 character editor (AA2Edit.exe) with the PPeX environment.
======================================================================================
AA2Edit (the char creator: bodies, faces, custom NPCs) needs a RUNNING PPeX server for its assets
(bodies/faces live in .ppx / base.pp). In MWA2 the PPeX server is orchestrator-managed (patched,
multi-client) instead of AAU auto-starting its own per game -> launched standalone, AA2Edit has no
PPeX server and dies before its log window. This starts the SAME shared PPeX server the orchestrator
uses, launches AA2Edit, and tears the server down again when the editor closes.

No custom exe: it reuses the existing AA2Edit.exe + the orchestrator's PPeX building blocks. This is
the "edit" half of the bat-based distribution model (run_orchestrator.bat = play, run_edit.bat = create).
Run via run_edit.bat (self-elevating). Writes only under this project; never touches AA2MiniPPX.
"""

import os
import subprocess
import sys

import orchestrator as orch


def main():
    school = next((w for w in orch.WORLDS if w["name"] == "school"), None)
    if not school:
        print("[!] no 'school' world configured.")
        return 1
    exe = os.path.join(school["dir"], "AA2Edit.exe")
    if not os.path.isfile(exe):
        print("[!] AA2Edit.exe not found at", exe)
        return 1

    try:
        orch.start_server()
        if not orch.wait_server_ready():
            print("[!] PPeX server did not become ready -> aborting "
                  "(AA2Edit would crash without it).")
            return 1

        print(f"[*] Launching AA2Edit ({exe}) ...")
        env = dict(os.environ)
        env["AA2_ORCH_AUTOLAUNCH"] = "1"   # AAU launcher auto-proceeds (no click), same as the game
        p = subprocess.Popen([exe], cwd=school["dir"], env=env)
        print(f"[+] AA2Edit running (PID {p.pid}). Close the editor to shut the PPeX server down.")
        p.wait()
        print("[*] AA2Edit closed.")
    except KeyboardInterrupt:
        print("\n[*] Interrupted.")
    finally:
        orch.cleanup()   # in edit mode no worlds are launched -> this just stops the PPeX server
    return 0


if __name__ == "__main__":
    sys.exit(main())
