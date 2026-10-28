# Finition HD des lots (lot2 par défaut, build_hd(id, "lot3") pour les autres) (exec dans run_script_unsafe après rhelp.py + build.py).
# build_hd(id) : timeline « L2 - <id> HD » depuis gen/<id>/plan-<id>.json (plans ProRes 9:16 déjà prêts, ralentis
# speed_pct -> Optical Flow + Speed Warp dans build_timeline). Construire toutes les timelines AVANT d'ajouter les
# rendus : tl_new efface les render jobs quand la timeline existe déjà.
# render_hd(ids) : un job H.264 ~20 Mb/s 1080×1920 par timeline -> hd/HD-<id>.mp4. Audio ré-encodé ensuite avec ffmpeg
# depuis gen/<id>/out/<id>-mix.wav (piège : Resolve peut garder un ancien son en cache).
import json

def build_hd(ID, lot="lot2"):
    G = ROOT + "/%s/_claude/gen/%s/" % (lot, ID)
    hd = G + "plan-%s-hd.json" % ID   # plans ramenés à 30 i/s par prep_hd.py (sources ≠ 30 i/s)
    plan = json.load(open(hd if os.path.exists(hd) else G + "plan-%s.json" % ID))
    plan["name"] = "L2 - %s HD" % ID
    for v in plan["video"] + plan["audio"]:
        v["path"] = v.get("path") or G + "out/" + v["clip"]
        v["folder"] = "L2-" + ID
    import_files("L2-" + ID, sorted({v["path"] for v in plan["video"] + plan["audio"]}), refresh=True)
    tl, log = build_timeline(plan)
    t0 = tl.GetStartFrame(); trous = []
    vids = sorted(tl.GetItemListInTrack("video", 1) or [], key=lambda it: it.GetStart())
    for a, b in zip(vids, vids[1:]):
        if b.GetStart() != a.GetEnd(): trous.append((a.GetName(), a.GetEnd() - t0, b.GetName(), b.GetStart() - t0))
    manquants = [i for i, ok in log if not ok]
    return {"id": ID, "plans": len(vids), "fin": tl.GetEndFrame() - t0, "attendu": round(plan["duree_s"] * 30),
            "trous": trous, "manquants": manquants}

def render_hd(ids):
    resolve.OpenPage("deliver"); project.DeleteAllRenderJobs(); jobs = []
    for ID in ids:
        project.SetCurrentTimeline(tl_get("L2 - %s HD" % ID))
        project.SetCurrentRenderFormatAndCodec("mp4", "H264")
        project.SetRenderSettings({"TargetDir": ROOT + "/hd", "CustomName": "HD-" + ID, "FormatWidth": 1080, "FormatHeight": 1920,
                                   "ExportVideo": True, "ExportAudio": True, "SelectAllFrames": True, "VideoQuality": 20000, "AudioCodec": "aac"})
        jobs.append(project.AddRenderJob())
    save(); project.StartRendering(jobs, False)
    return jobs
