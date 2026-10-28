# Finition HD G3 dans Resolve (exec dans run_script_unsafe après rhelp.py + build.py) : timeline « L2 - G3 Léaument » depuis plan-G3.json.
# Version recalée sur les kicks 808 réels (rythme/frappes.json). Tous les clips sont en 30 i/s, e = durée timeline exacte :
# - vitesse normale : images source 25 i/s converties en 30 i/s (image la plus proche) ;
# - ralentis (B1, B4, B7) : images source 25 i/s étiquetées 30 i/s, SetSpeed 41,6667 % (= 50 % du temps réel) + Optical Flow + Speed Warp.
# Plus aucun arrondi 25 -> 30 : pas de trou ni de chevauchement. Fondu au noir cuit dans G3k_B7.mov. Clips renommés G3k_* : aucun clip périmé du Media Pool (ancienne version 25 i/s) réutilisé.
import json
G3 = ROOT + "/lot2/_claude/gen/G3/"
plan = json.load(open(G3 + "plan-G3.json"))
plan["name"] = "L2 - G3 Léaument"
for v, w in zip(plan["video"], plan["video"][1:]): assert v["rec"] + v["dur"] == w["rec"], (v["id"], w["id"])
import_files("L2-G3", [v["path"] for v in plan["video"]] + [a["path"] for a in plan["audio"]])
for v in plan["video"] + plan["audio"]: v["folder"] = "L2-G3"
tl, log = build_timeline(plan)
summ = items_summary(tl)           # attendu : V1 0-162, 162-202, 202-241, 241-268, 268-307, 307-360, 360-392, 392-412, 412-447 ; A1 0-447
save()
# Rendu HD : H.264 ~20 Mb/s, AAC 320k (VideoQuality = kb/s ; pas de clé de débit audio dans RenderSettings)
project.SetCurrentTimeline(tl); resolve.OpenPage("deliver"); project.DeleteAllRenderJobs()
project.SetCurrentRenderFormatAndCodec("mp4", "H264")
project.SetRenderSettings({"TargetDir": ROOT + "/hd", "CustomName": "HD-G3", "FormatWidth": 1080, "FormatHeight": 1920,
                           "ExportVideo": True, "ExportAudio": True, "SelectAllFrames": True, "VideoQuality": 20000, "AudioCodec": "aac"})   # AAC 320k pas réglable par API : audio ré-encodé ensuite (ffmpeg, vidéo copiée)
jid = project.AddRenderJob(); project.StartRendering([jid], False)
result = {"log": log, "items": summ, "job": jid}
