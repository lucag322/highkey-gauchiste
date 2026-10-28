#!/usr/bin/env python3
# seg.py id [t0 t1] : phrases avec timecode (segments Whisper)
import json,sys
id=sys.argv[1]; t0=float(sys.argv[2]) if len(sys.argv)>2 else 0; t1=float(sys.argv[3]) if len(sys.argv)>3 else 1e9
d=json.load(open(f"/Users/luca.grousset/Movies/highkey-gauchiste/lot2/_claude/tx/{id}.json"))
for s in d["segments"]:
    if s["end"]>=t0 and s["start"]<=t1:
        print(f'{s["start"]:7.1f}-{s["end"]:7.1f} {s["text"].strip()}')
