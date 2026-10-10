param([int]$Minutes = 30)
$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot ('capture-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $out -Force | Out-Null
Set-Content -LiteralPath (Join-Path $PSScriptRoot 'latest.txt') -Value $out
function Log($file, $value) {
    $value | ConvertTo-Json -Depth 5 -Compress | Add-Content -LiteralPath (Join-Path $out $file) -Encoding UTF8
}
Add-Type @'
using System;
using System.Text;
using System.Collections.Concurrent;
using System.Runtime.InteropServices;
public class WindowWatch {
  public class Entry { public string Time; public uint Event; public long Handle; public uint Pid; public string Title; public string Class; }
  public static ConcurrentQueue<Entry> Queue = new ConcurrentQueue<Entry>();
  delegate void Callback(IntPtr hook,uint ev,IntPtr hwnd,int obj,int child,uint thread,uint time);
  static Callback callback = OnEvent;
  static IntPtr foreground, show, minimize;
  [DllImport("user32.dll")] static extern IntPtr SetWinEventHook(uint min,uint max,IntPtr module,Callback cb,uint pid,uint thread,uint flags);
  [DllImport("user32.dll")] static extern bool UnhookWinEvent(IntPtr hook);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd,StringBuilder text,int max);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr hwnd,StringBuilder text,int max);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")] static extern IntPtr GetAncestor(IntPtr hwnd,uint flags);
  [StructLayout(LayoutKind.Sequential)] struct Point { public int x,y; }
  [StructLayout(LayoutKind.Sequential)] struct Msg { public IntPtr hwnd; public uint message; public UIntPtr wParam; public IntPtr lParam; public uint time; public Point pt; public uint lPrivate; }
  [DllImport("user32.dll")] static extern bool PeekMessage(out Msg msg,IntPtr hwnd,uint min,uint max,uint remove);
  [DllImport("user32.dll")] static extern bool TranslateMessage(ref Msg msg);
  [DllImport("user32.dll")] static extern IntPtr DispatchMessage(ref Msg msg);
  static void OnEvent(IntPtr hook,uint ev,IntPtr hwnd,int obj,int child,uint thread,uint time) {
    if(hwnd==IntPtr.Zero || obj!=0 || child!=0) return;
    if(ev==0x8002 && (!IsWindowVisible(hwnd) || GetAncestor(hwnd,2)!=hwnd)) return;
    uint pid; GetWindowThreadProcessId(hwnd,out pid);
    var title=new StringBuilder(1024); var cls=new StringBuilder(256);
    GetWindowText(hwnd,title,title.Capacity); GetClassName(hwnd,cls,cls.Capacity);
    Queue.Enqueue(new Entry {Time=DateTimeOffset.Now.ToString("o"),Event=ev,Handle=hwnd.ToInt64(),Pid=pid,Title=title.ToString(),Class=cls.ToString()});
  }
  public static void Start() {
    foreground=SetWinEventHook(3,3,IntPtr.Zero,callback,0,0,0);
    show=SetWinEventHook(0x8002,0x8002,IntPtr.Zero,callback,0,0,0);
    minimize=SetWinEventHook(0x16,0x17,IntPtr.Zero,callback,0,0,0);
    if(foreground==IntPtr.Zero || show==IntPtr.Zero || minimize==IntPtr.Zero) throw new Exception("Window hook installation failed");
  }
  public static void Pump() { Msg msg; while(PeekMessage(out msg,IntPtr.Zero,0,0,1)) { TranslateMessage(ref msg); DispatchMessage(ref msg); } }
  public static void Stop() { UnhookWinEvent(foreground); UnhookWinEvent(show); UnhookWinEvent(minimize); }
}
'@
$cache = @{}
function Details([uint32]$processId) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
    if ($p) {
        $d = [pscustomobject]@{Pid=$p.ProcessId; Parent=$p.ParentProcessId; Name=$p.Name; Path=$p.ExecutablePath; Command=$p.CommandLine; Created=$p.CreationDate}
        $cache[[string]$processId] = $d
        return $d
    }
    return $cache[[string]$processId]
}
try {
    Get-CimInstance Win32_Process | ForEach-Object {
        $d = [pscustomobject]@{Pid=$_.ProcessId; Parent=$_.ParentProcessId; Name=$_.Name; Path=$_.ExecutablePath; Command=$_.CommandLine; Created=$_.CreationDate}
        $cache[[string]$_.ProcessId]=$d
        Log 'baseline-processes.jsonl' $d
    }
    Get-ScheduledTask | ForEach-Object {
        $info = $_ | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue
        Log 'tasks.jsonl' ([pscustomobject]@{Name=$_.TaskName;Path=$_.TaskPath;State=[string]$_.State;LastRun=$info.LastRunTime;NextRun=$info.NextRunTime;Result=$info.LastTaskResult;Actions=@($_.Actions | ForEach-Object { @{Execute=$_.Execute;Arguments=$_.Arguments} });Intervals=@($_.Triggers | ForEach-Object {$_.Repetition.Interval})})
    }
    $known = @{}
    Get-Process | ForEach-Object { $known[$_.Id] = $true }
    $nextScan = Get-Date
    [WindowWatch]::Start()
    Log 'status.jsonl' @{Time=(Get-Date).ToString('o');Status='running';Pid=$PID;Minutes=$Minutes}
    $end = (Get-Date).AddMinutes($Minutes)
    while ((Get-Date) -lt $end -and !(Test-Path -LiteralPath (Join-Path $out 'STOP'))) {
        [WindowWatch]::Pump()
        $entry = $null
        while ([WindowWatch]::Queue.TryDequeue([ref]$entry)) {
            $d=Details $entry.Pid
            $parent=$null
            if ($d) { $parent=Details $d.Parent }
            Log 'windows.jsonl' @{Window=$entry;Process=$d;Parent=$parent}
        }
        if ((Get-Date) -ge $nextScan) {
            $current = @{}
            foreach ($p in @(Get-Process)) {
                $current[$p.Id]=$true
                if (!$known.ContainsKey($p.Id)) {
                    $d=Details $p.Id
                    $parent=$null
                    if ($d) { $parent=Details $d.Parent }
                    Log 'starts.jsonl' @{Time=(Get-Date).ToString('o');Pid=$p.Id;Name=$p.ProcessName;Process=$d;Parent=$parent}
                }
            }
            $known=$current
            $nextScan=(Get-Date).AddMilliseconds(250)
        }
        Start-Sleep -Milliseconds 30
    }
} catch {
    Log 'status.jsonl' @{Time=(Get-Date).ToString('o');Status='error';Error=$_.ToString()}
    throw
} finally {
    [WindowWatch]::Stop()
    Unregister-Event -SourceIdentifier WindowWatchProcess -ErrorAction SilentlyContinue
    Log 'status.jsonl' @{Time=(Get-Date).ToString('o');Status='stopped'}
}
