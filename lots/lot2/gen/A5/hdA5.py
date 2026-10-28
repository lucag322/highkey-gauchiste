# Finition HD A5 (v2) dans Resolve (exec dans run_script_unsafe après rhelp.py + build.py) : timeline « L2 - A5 Bagayoko » depuis plan-A5.json.
# Plans déjà rééchantillonnés à 30 i/s par genA5.py (ProRes 30 i/s, sources 25 i/s converties en Python) : pas de piège 25 -> 30 i/s,
# chaque plan fait exactement e - s images timeline. Seul ralenti : « dos » (speed_pct 60, clip de 52 images à vitesse normale,
# Resolve en garde la durée et lit 31 images source) -> vérifier dans items_summary qu'il fait 52 images et que « aura_... » suit sans trou.
# v2 (sources A5b, meeting de Saint-Denis) : plan-A5.json régénéré par genA5.py ; v1 refusée archivée (plan-A5_v1.json, out/_v1).
import json
A5 = ROOT + "/lot2/_claude/gen/A5/"
plan = json.load(open(A5 + "plan-A5.json"))
plan["name"] = "L2 - A5 Bagayoko"
for v in plan["video"] + plan["audio"]:
    v["path"] = A5 + "out/" + v["clip"]; v["folder"] = "L2-A5"
import_files("L2-A5", sorted({v["path"] for v in plan["video"] + plan["audio"]}))
tl, log = build_timeline(plan)
summ = items_summary(tl)           # attendu : 12 plans V1 bout à bout de 0 à 447 (14,9 s), 1 mix A1 ; aucun trou / chevauchement
t0 = tl.GetStartFrame(); trous = []
vids = sorted(tl.GetItemListInTrack("video", 1) or [], key=lambda it: it.GetStart())
for a, b in zip(vids, vids[1:]):
    if b.GetStart() != a.GetEnd(): trous.append((a.GetName(), a.GetEnd() - t0, b.GetName(), b.GetStart() - t0))
save()
# Rendu HD : H.264 ~20 Mb/s (VideoQuality = kb/s), AAC ; 320k pas réglable par API -> ré-encoder l'audio ensuite (ffmpeg, vidéo copiée) :
# ffmpeg -i hd/HD-A5.mp4 -i out/A5-mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k hd/HD-A5_320.mp4
project.SetCurrentTimeline(tl); resolve.OpenPage("deliver"); project.DeleteAllRenderJobs()
project.SetCurrentRenderFormatAndCodec("mp4", "H264")
project.SetRenderSettings({"TargetDir": ROOT + "/hd", "CustomName": "HD-A5", "FormatWidth": 1080, "FormatHeight": 1920,
                           "ExportVideo": True, "ExportAudio": True, "SelectAllFrames": True, "VideoQuality": 20000, "AudioCodec": "aac"})
jid = project.AddRenderJob(); project.StartRendering([jid], False)
result = {"log": log, "items": summ, "trous": trous, "fin": tl.GetEndFrame() - t0, "job": jid}
