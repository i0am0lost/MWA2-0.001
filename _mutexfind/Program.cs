using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;

// Liest die benannten Mutant(Mutex)-Handles des laufenden AA2Play-Prozesses aus,
// um den Single-Instance-Mutex-Namen zu finden (fuer den Welt-spezifischen exe-Patch).
class MutexFinder
{
    const int SystemExtendedHandleInformation = 64;
    const int ObjectTypeInformation = 2;
    const int ObjectNameInformation = 1;
    const uint PROCESS_DUP_HANDLE = 0x0040;
    const uint DUPLICATE_SAME_ACCESS = 0x2;
    const uint STATUS_INFO_LENGTH_MISMATCH = 0xC0000004;

    [DllImport("ntdll.dll")]
    static extern uint NtQuerySystemInformation(int cls, IntPtr info, int len, out int retLen);
    [DllImport("ntdll.dll")]
    static extern uint NtQueryObject(IntPtr h, int cls, IntPtr info, int len, out int retLen);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool DuplicateHandle(IntPtr srcProc, IntPtr srcH, IntPtr tgtProc, out IntPtr tgtH, uint access, bool inherit, uint options);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll")]
    static extern IntPtr GetCurrentProcess();

    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc cb, IntPtr p);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out int pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, System.Text.StringBuilder s, int max);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, System.Text.StringBuilder s, int max);

    static void Main(string[] args)
    {
        bool closeMode = Array.IndexOf(args, "close") >= 0;
        var pids = new HashSet<int>();
        foreach (var p in Process.GetProcessesByName("AA2Play")) pids.Add(p.Id);
        foreach (var a in args) if (int.TryParse(a, out int f)) pids.Add(f);
        if (closeMode) Console.WriteLine("[close-Modus: schliesse __AA2Play_Class__ Mutex der laufenden Instanz(en)]");
        if (pids.Count == 0) { Console.WriteLine("Kein AA2Play-Prozess gefunden. Laeuft school?"); return; }
        Console.WriteLine("Ziel-PIDs: " + string.Join(",", pids));

        int len = 0x100000;
        IntPtr buf = Marshal.AllocHGlobal(len);
        uint status;
        while ((status = NtQuerySystemInformation(SystemExtendedHandleInformation, buf, len, out int rl)) == STATUS_INFO_LENGTH_MISMATCH)
        {
            Marshal.FreeHGlobal(buf);
            len = Math.Max(len * 2, rl + 0x20000);
            buf = Marshal.AllocHGlobal(len);
        }
        if (status != 0) { Console.WriteLine($"NtQuerySystemInformation failed 0x{status:X8}"); return; }

        long count = Marshal.ReadIntPtr(buf).ToInt64();
        int entrySize = IntPtr.Size * 3 + 4 + 2 + 2 + 4 + 4; // 40 (x64)
        IntPtr arrayStart = buf + IntPtr.Size * 2;
        IntPtr cur = GetCurrentProcess();
        var procHandles = new Dictionary<int, IntPtr>();
        int found = 0;

        for (long i = 0; i < count; i++)
        {
            IntPtr ep = arrayStart + checked((int)(i * entrySize));
            int pid = Marshal.ReadIntPtr(ep + IntPtr.Size).ToInt32();      // UniqueProcessId @ +8
            if (!pids.Contains(pid)) continue;
            IntPtr hval = Marshal.ReadIntPtr(ep + IntPtr.Size * 2);         // HandleValue @ +16

            if (!procHandles.TryGetValue(pid, out IntPtr ph))
            {
                ph = OpenProcess(PROCESS_DUP_HANDLE, false, pid);
                procHandles[pid] = ph;
                if (ph == IntPtr.Zero)
                    Console.WriteLine($"  WARN: OpenProcess(PID {pid}) fehlgeschlagen (evtl. Adminrechte noetig).");
            }
            if (ph == IntPtr.Zero) continue;

            if (!DuplicateHandle(ph, hval, cur, out IntPtr dup, 0, false, DUPLICATE_SAME_ACCESS)) continue;
            try
            {
                string type = QueryObject(dup, ObjectTypeInformation);
                // Nur Typen, deren Namensabfrage NICHT haengt (kein File/Pipe!):
                if (type == "Event" || type == "Mutant" || type == "Semaphore" || type == "Section")
                {
                    string name = QueryObject(dup, ObjectNameInformation);
                    if (!string.IsNullOrEmpty(name)
                        && !name.Contains("WilStaging") && !name.Contains("WilError")
                        && !name.Contains("SM0:") && !name.Contains("ImmersiveShell")
                        && !name.Contains("RPC Control"))
                    {
                        found++;
                        Console.WriteLine($"PID {pid}  {type,-9} ->  {name}");

                        // Single-Instance-Mutex der laufenden Instanz schliessen,
                        // damit die naechste Instanz starten kann.
                        if (closeMode && type == "Mutant" && name.EndsWith("__AA2Play_Class__"))
                        {
                            const uint DUPLICATE_CLOSE_SOURCE = 0x1;
                            if (DuplicateHandle(ph, hval, cur, out IntPtr dd, 0, false, DUPLICATE_CLOSE_SOURCE))
                            { CloseHandle(dd); Console.WriteLine($"   >>> single-instance mutex CLOSED (PID {pid})."); }
                            else
                                Console.WriteLine($"   >>> Schliessen fehlgeschlagen (Err {Marshal.GetLastWin32Error()}).");
                        }
                    }
                }
            }
            finally { CloseHandle(dup); }
        }
        Marshal.FreeHGlobal(buf);
        Console.WriteLine($"Fertig (Handles). {found} interessante benannte Objekte.");

        Console.WriteLine("=== Top-Level-Fenster der Ziel-PIDs (fuer FindWindow-basierte Single-Instance) ===");
        EnumWindows((h, l) =>
        {
            GetWindowThreadProcessId(h, out int wpid);
            if (!pids.Contains(wpid)) return true;
            var cls = new System.Text.StringBuilder(256); GetClassName(h, cls, 256);
            var tit = new System.Text.StringBuilder(256); GetWindowText(h, tit, 256);
            Console.WriteLine($"PID {wpid}  HWND {h.ToInt64():X}  class='{cls}'  title='{tit}'");
            return true;
        }, IntPtr.Zero);
        Console.WriteLine("Fertig (Fenster).");
    }

    // Beide Strukturen (TYPE/NAME) beginnen mit UNICODE_STRING { USHORT Length; USHORT Max; PWSTR Buffer(@+8) }
    static string QueryObject(IntPtr handle, int cls)
    {
        int len = 0x800;
        IntPtr buf = Marshal.AllocHGlobal(len);
        try
        {
            uint st = NtQueryObject(handle, cls, buf, len, out int ret);
            if (st == STATUS_INFO_LENGTH_MISMATCH && ret > 0)
            {
                Marshal.FreeHGlobal(buf); len = ret; buf = Marshal.AllocHGlobal(len);
                st = NtQueryObject(handle, cls, buf, len, out ret);
            }
            if (st != 0) return null;
            ushort sLen = (ushort)Marshal.ReadInt16(buf);
            IntPtr sBuf = Marshal.ReadIntPtr(buf + IntPtr.Size);
            if (sBuf == IntPtr.Zero || sLen == 0) return "";
            return Marshal.PtrToStringUni(sBuf, sLen / 2);
        }
        finally { Marshal.FreeHGlobal(buf); }
    }
}
