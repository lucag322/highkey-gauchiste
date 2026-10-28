#!/usr/bin/env python3
import json
ROOT="/Users/luca.grousset/Movies/highkey-gauchiste/lot2/_claude/"
def W(id,t0,t1,off=0):
    d=json.load(open(f"{ROOT}tx/{id}.json")); out=[]
    for s in d["segments"]:
        for w in s.get("words",[]):
            if w["end"]>=t0 and w["start"]<=t1: out.append({"w":w["word"].strip(),"start":round(w["start"]-off,2),"end":round(w["end"]-off,2)})
    return out
def P(f,i,o,d): return {"fichier":f"sources/{f}.mp4","in":i,"out":o,"description":d}
D={}
exec(open(ROOT+"derush_data_A.py").read())
try: exec(open(ROOT+"derush_data_G.py").read())
except FileNotFoundError: pass
json.dump({"projet":"highkey-gauchiste lot2","date_derush":"2026-10-26","note":"Temps in/out/mots en secondes DANS le fichier source local (pas dans la vidéo YouTube d'origine) ; offset_yt = décalage à ajouter pour retrouver le temps YouTube. Fichiers 1080p H.264. Voix = piste originale.","figures":D},open(ROOT+"derush-AG.json","w"),ensure_ascii=False,indent=1)
print("ok",list(D))
