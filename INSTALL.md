# MWA2 — Installation

MWA2 is **self-contained and portable**: copy this whole folder anywhere and run it. **Python is bundled**
(in `system\python`), so there is nothing to install for it. Nothing is hard-coded to a specific machine or
path — everything resolves relative to this folder.

## 1. Copy the package
Create a folder wherever you like and copy this entire directory into it, e.g.:

```
D:\Games\MWA2_V0.1
```

(Same idea as a clean AA2 install — a single self-contained folder you can place anywhere.)

## 2. First run: `Install.bat`
Double-click **`Install.bat`** once. It checks the environment:
- **Python** — bundled in `system\python`, nothing to do. ✔
- **.NET runtime (3.1+)** — the only external requirement, used by the shared **PPeX** asset server
  (`system\ppex\…\PPeXM64.dll`, run via `dotnet`). If `Install.bat` reports it missing, install the
  **.NET Runtime** from <https://dotnet.microsoft.com/download> and run `Install.bat` again.

> A future version will bundle .NET too (self-contained PPeX) so there is zero external requirement.

## 3. Run
- **`Play.bat`** — start the game (two-world jail mode). Self-elevates for admin (needed so the brief input
  lock during jail's auto-click sequence can't be diverted; accept the UAC prompt).
- **`Create Characters.bat`** — open the AA2 character editor (with the PPeX server running).
- **`Memory Tool.bat`** — inspect / tune the per-playthrough SSOT memory without grinding the game.

## Folder layout
```
MWA2_V0.1/
├─ Play.bat   Create Characters.bat   Memory Tool.bat   Install.bat
├─ README.md   INSTALL.md
├─ school/   jail/                 # the two game worlds (AA2 install + our mods)
└─ system/                         # everything "ours", kept out of the way
   ├─ python/                      # bundled Python 3.12 runtime
   ├─ app/                         # our tooling (orchestrator + SSOT/memory + module codec + card tools)
   ├─ ppex/                        # patched multi-client PPeX server
   ├─ mutexfind/                   # multi-instance helper
   ├─ catalogs/                    # module + expression catalogs (reference data)
   └─ docs/  ├─ handovers/   └─ reference/
```

The two worlds (`school/`, `jail/`) are full AA2 installs with our AAUnlimited mods on top. The cross-world
memory + evolution logic lives in the Python layer (`system\app` + `_playthroughs\<save>\memory.db`, created at
runtime). **Cards are never modified** — they are pristine, shareable base data; all our state is external (the SSOT).
