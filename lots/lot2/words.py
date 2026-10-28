#!/usr/bin/env python3
# words.py id t0 t1 [offset] : mots minutés (temps source ; offset soustrait pour temps fichier)
import json,sys
id=sys.argv[1]; t0=float(sys.argv[2]); t1=float(sys.argv[3]); off=float(sys.argv[4]) if len(sys.argv)>4 else 0
d=json.load(open(f"/Users/luca.grousset/Movies/highkey-gauchiste/lot2/_claude/tx/{id}.json"))
out=[]
for s in d["segments"]:
    for w in s.get("words",[]):
        if w["end"]>=t0 and w["start"]<=t1: out.append({"w":w["word"].strip(),"start":round(w["start"]-off,2),"end":round(w["end"]-off,2)})
print(json.dumps(out,ensure_ascii=False))
