#!/usr/bin/env python3
"""Copy the Runna calendar feed into docs/runna.json so the app can read it.

The feed URL is private, so it comes from the RUNNA_ICS_URL environment variable
(a repository secret) and is never written to the output. Standard library only.

Usage: RUNNA_ICS_URL=... python3 tools/runna_sync.py [--file feed.ics]
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "runna.json"
PAST_DAYS, AHEAD_DAYS = 28, 120


def fetch(url):
    url = url.strip().replace("webcal://", "https://", 1)
    req = urllib.request.Request(url, headers={"User-Agent": "gym-log-runna-sync"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def unfold(text):
    lines = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def unescape(v):
    out, i = [], 0
    while i < len(v):
        c = v[i]
        if c == "\\" and i + 1 < len(v):
            n = v[i + 1]
            out.append("\n" if n in "nN" else n)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out).strip()


def event_date(params, value, tz):
    """Calendar date of DTSTART. UTC times are shifted into RUNNA_TZ; other times keep their own date."""
    value = value.strip()
    d = dt.date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
    if len(value) == 8 or params.upper().endswith("VALUE=DATE"):
        return d
    if value.endswith("Z") and tz:
        t = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
        return t.astimezone(tz).date()
    return d


def minutes(clock):
    """'27:40' or '1:02:15' -> minutes as a short string."""
    parts = [int(x) for x in clock.split(":")]
    secs = sum(v * 60 ** i for i, v in enumerate(reversed(parts)))
    return f"{secs / 60:.1f}".rstrip("0").rstrip(".")


def tidy(ev):
    """Runna's events: UPCOMING_* hold the workout, COMPLETED_* add a summary with distance and time.
    Location, laps and PBs are left out on purpose: the output is public."""
    title = re.sub(r"^[^\w(]+", "", ev["title"]).strip() or ev["title"]
    desc = ev.get("desc", "")
    m = re.search(r"View in the Runna app:\s*(https://club\.runna\.com/\S+)", desc)
    run = {"date": ev["date"], "title": title, "desc": "", "id": ev.get("uid", ""), "link": m.group(1) if m else ""}
    if ev.get("uid", "").startswith("COMPLETED"):
        run["done"] = True
        d = re.search(r"Distance:\s*([\d.]+)\s*km", desc)
        t = re.search(r"Time:\s*([\d:]+)", desc)
        if d:
            run["dist"] = d.group(1)
        if t:
            run["time"] = minutes(t.group(1))
        body = re.search(r"Description:\n(.*?)(?=\n\S{1,3}\s*(?:Laps|PBs):|\n\S{1,3}\s*View in the Runna app|\Z)", desc, re.S)
        desc = body.group(1) if body else ""
    else:
        lines = desc.split("\n")
        if lines and lines[0].startswith(title.split(" • ")[0]):
            lines = lines[1:]
        desc = "\n".join(lines)
    desc = re.sub(r".*View in the Runna app.*", "", desc)
    desc = re.sub(r"(?m)^-{3,}$\n?", "", desc)
    run["desc"] = re.sub(r"\n{3,}", "\n\n", desc).strip()
    return {k: v for k, v in run.items() if v != ""}


def parse(text, tz):
    runs, ev = [], None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            ev = {}
            continue
        if line == "END:VEVENT":
            if ev and ev.get("date") and ev.get("title") and ev.get("status") != "CANCELLED":
                runs.append(tidy(ev))
            ev = None
            continue
        if ev is None or ":" not in line:
            continue
        head, value = line.split(":", 1)
        name, _, params = head.partition(";")
        name = name.upper()
        if name == "DTSTART":
            ev["date"] = event_date(params, value, tz).isoformat()
        elif name == "SUMMARY":
            ev["title"] = unescape(value)
        elif name == "DESCRIPTION":
            ev["desc"] = unescape(value)
        elif name == "UID":
            ev["uid"] = value.strip()
        elif name == "STATUS":
            ev["status"] = value.strip().upper()
    return runs


def main():
    tz = None
    if os.environ.get("RUNNA_TZ"):
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(os.environ["RUNNA_TZ"])
    if "--file" in sys.argv:
        text = pathlib.Path(sys.argv[sys.argv.index("--file") + 1]).read_text()
    else:
        url = os.environ.get("RUNNA_ICS_URL", "")
        if not url.strip():
            print("::notice::RUNNA_ICS_URL secret is not set, skipping the Runna sync.")
            return
        text = fetch(url)
    if "BEGIN:VCALENDAR" not in text:
        sys.exit("The Runna link didn't return a calendar. Check the RUNNA_ICS_URL secret.")

    today = dt.datetime.now(tz).date()
    lo, hi = (today - dt.timedelta(days=PAST_DAYS)).isoformat(), (today + dt.timedelta(days=AHEAD_DAYS)).isoformat()
    runs = sorted((r for r in parse(text, tz) if lo <= r["date"] <= hi), key=lambda r: (r["date"], r["title"]))

    old = None
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text()).get("runs")
        except ValueError:
            pass
    if old == runs:
        print(f"No change ({len(runs)} Runna sessions).")
        return
    stamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    OUT.write_text(json.dumps({"changed": stamp, "runs": runs}, ensure_ascii=False, indent=1) + "\n")
    print(f"Wrote {len(runs)} Runna sessions to {OUT.name}.")


if __name__ == "__main__":
    main()
