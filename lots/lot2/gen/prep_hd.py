# Prépare la finition HD d'une vidéo du lot 2 : plans à 30 i/s pour une timeline 30 i/s sans trou d'1 image.
# Usage : prep_hd.py <id> [lot2|lot3…]  ->  gen/<id>/plan-<id>-hd.json (lu par hd_lot2.py) + copies gen/<id>/out/<clip>_30.mov
# - plan à vitesse normale, source ≠ 30 i/s : rééchantillonné à 30 i/s (image la plus proche), e = durée timeline ;
# - ralenti (speed_pct) : images source étiquetées 30 i/s, vitesse = speed_pct × fps_source / 30 (même temps réel), e = durée timeline ;
#   Resolve garde la durée et ne lit que durée × vitesse images : la fin du clip est complétée (dernière image) pour
#   atteindre e, ces images ne sont jamais montrées.
import json, subprocess, sys, os

ID = sys.argv[1]; LOT = sys.argv[2] if len(sys.argv) > 2 else "lot2"
G = os.path.expanduser("~/Movies/highkey-gauchiste/%s/_claude/gen/%s/" % (LOT, ID))
plan = json.load(open(G + "plan-%s.json" % ID))
for v in plan["video"]:
    fps = v.get("clip_fps", 30)
    if fps == 30: continue
    src = v.get("path") or G + "out/" + v["clip"]
    v["clip"] = v["clip"].replace(".mov", "_30.mov"); v["path"] = G + "out/" + v["clip"]
    if v.get("speed_pct"):
        v["speed_pct"] = round(v["speed_pct"] * fps / 30, 4); vf = "setpts=N/30/TB,tpad=stop_mode=clone:stop=%d" % v["dur"]
    else:
        vf = "fps=30,tpad=stop_mode=clone:stop=2"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-r", "30", "-c:v", "prores_ks", "-profile:v", "3",
                    "-an", v["path"]], check=True)
    v["s"], v["e"], v["clip_fps"] = 0, v["dur"], 30
for a, b in zip(plan["video"], plan["video"][1:]):
    if "dur" in a: assert a["rec"] + a["dur"] == b["rec"], (a["clip"], b["clip"])
json.dump(plan, open(G + "plan-%s-hd.json" % ID, "w"), ensure_ascii=False, indent=1)
print(ID, "ok", sum(1 for v in plan["video"] if v["clip"].endswith("_30.mov")), "plans convertis")
