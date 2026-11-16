"""Run every paper account in paper/fleet.json for today's close.

The first account (the frozen primary) downloads the day's NSE files; the rest reuse the same data
with --no-download, then updates benchmark indices and paper/fleet_report.md. Stops if the primary says "already processed" (holiday / files not out).
  python3 -W ignore run_fleet.py
"""
import json, subprocess, sys
accts = json.load(open("paper/fleet.json"))["accounts"]
fail = 0
for j, a in enumerate(accts):
    cmd = [sys.executable, "-W", "ignore", "-m", "alpha.paper_trade", "--config", a["config"], "--out", a["out"]]
    if j: cmd.append("--no-download")
    p = subprocess.run(cmd, capture_output=True, text=True)
    last = (p.stdout.strip().splitlines() or [""])[-1]
    if p.returncode:
        fail = 1; print(f"[{a['out']}] ERROR\n{p.stderr[-2000:]}", flush=True)
    else:
        print(f"[{a['out']}] {last}", flush=True)
    if j == 0 and (p.returncode or "already processed" in p.stdout):
        print("primary not processed today: fleet stopped"); sys.exit(p.returncode or 0)
for extra in (["data_download_indices.py"], ["fleet_report.py"]):
    p = subprocess.run([sys.executable, "-W", "ignore"] + extra, capture_output=True, text=True)
    print(p.stdout.strip() if not p.returncode else f"[{extra[0]}] ERROR (fleet results unaffected)\n{p.stderr[-1000:]}", flush=True)
sys.exit(fail)
