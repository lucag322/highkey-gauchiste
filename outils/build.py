# Construction de timeline générique depuis un plan JSON (exec côté Resolve après rhelp.py)
import json
def import_files(folder_name, paths, refresh=False):
    """refresh=True : réimporte les clips déjà présents (Resolve garde en cache la durée d'un fichier régénéré au même chemin)."""
    fol = folder(folder_name); mp.SetCurrentFolder(fol)
    have = {c.GetName(): c for c in fol.GetClipList()}
    if refresh:
        old = [c for n, c in have.items() if n in {os.path.basename(p) for p in paths}]
        if old: mp.DeleteClips(old)
        have = {c.GetName(): c for c in fol.GetClipList()}
    new = [p for p in paths if os.path.basename(p) not in have]
    if new: mp.ImportMedia(new)
    mp.SetCurrentFolder(rf)
    return {c.GetName(): c for c in fol.GetClipList()}
def build_timeline(plan):
    """plan = {name, fps, video:[{clip, folder, s, e, rec, track}], audio:[{clip, folder, rec, track, s?, e?}]}"""
    tl = tl_new(plan["name"], str(plan.get("fps", 30)))
    nv = max([v.get("track", 1) for v in plan["video"]] + [1]); na = max([a.get("track", 1) for a in plan["audio"]] + [1])
    while tl.GetTrackCount("video") < nv: tl.AddTrack("video")
    while tl.GetTrackCount("audio") < na: tl.AddTrack("audio", "stereo")
    t0 = tl.GetStartFrame(); log = []
    for v in plan["video"]:
        c = clip(v["clip"], v.get("folder"))
        info = {"mediaPoolItem": c, "startFrame": v["s"], "endFrame": v["e"], "mediaType": 1,
                "trackIndex": v.get("track", 1), "recordFrame": t0 + v["rec"]}
        its = mp.AppendToTimeline([info])
        if its and v.get("speed_pct"):   # ralenti Resolve : durée gardée, source raccourcie ; Optical Flow + Speed Warp
            its[0].SetSpeed({"Percentage": float(v["speed_pct"]), "RippleTimeline": False})
            its[0].SetProperty("RetimeProcess", resolve.RETIME_OPTICAL_FLOW)
            its[0].SetProperty("MotionEstimation", resolve.MOTION_EST_SPEED_WARP_BETTER)
        if its and v.get("composite"): its[0].SetProperty("CompositeMode", getattr(resolve, v["composite"]))
        if its and v.get("props"): its[0].SetProperties(v["props"])
        log.append((v.get("id"), bool(its)))
    for a in plan["audio"]:
        c = clip(a["clip"], a.get("folder"))
        info = {"mediaPoolItem": c, "mediaType": 2, "trackIndex": a.get("track", 1), "recordFrame": t0 + a["rec"]}
        if "s" in a: info.update({"startFrame": a["s"], "endFrame": a["e"]})
        its = mp.AppendToTimeline([info])
        log.append((a.get("id"), bool(its)))
    return tl, log
def items_summary(tl):
    t0 = tl.GetStartFrame(); out = []
    for kind in ("video", "audio"):
        for tr in range(1, tl.GetTrackCount(kind) + 1):
            for it in tl.GetItemListInTrack(kind, tr) or []:
                out.append("%s%d %s %d-%d" % (kind[0].upper(), tr, it.GetName()[:22], it.GetStart() - t0, it.GetEnd() - t0))
    return out
def export_defaults(tl, style, prefix_names):
    d = ROOT + "/_claude/comps/%s" % style; os.makedirs(d, exist_ok=True)
    resolve.OpenPage("media"); t0 = tl.GetStartFrame(); recs = []
    for tr in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", tr) or []:
            if any(it.GetName().startswith(p) for p in prefix_names):
                rec = it.GetStart() - t0; tag = "%d" % rec if tr == 1 else "%d_v%d" % (rec, tr)
                export_default(it, d + "/def_%s.comp" % tag); recs.append(tag)
    return recs
def apply_comps(tl, style):
    d = ROOT + "/_claude/comps/%s" % style; resolve.OpenPage("media"); t0 = tl.GetStartFrame(); done = []
    for tr in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", tr) or []:
            rec = it.GetStart() - t0; tag = "%d" % rec if tr == 1 else "%d_v%d" % (rec, tr)
            p = d + "/F_%s.comp" % tag
            if os.path.exists(p):
                import_clip_comp(it, p); done.append(tag)
    return done
def run_local(cmd):
    env = dict(os.environ, PATH="/opt/homebrew/bin:/usr/bin:/bin")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    return (r.stdout + r.stderr)[-1500:]
