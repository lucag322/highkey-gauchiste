# Helpers côté Resolve (exec dans run_script_unsafe ; resolve/project injectés)
import os, time, subprocess
ROOT = os.path.expanduser("~/Movies/highkey-gauchiste")
exec(open(ROOT + "/_claude/outils/compkit.py").read())
mp = project.GetMediaPool(); rf = mp.GetRootFolder()
def folder(name):
    f = next((f for f in rf.GetSubFolderList() if f.GetName() == name), None)
    return f or mp.AddSubFolder(rf, name)
def clip(name, fol=None):
    fols = [folder(fol)] if fol else rf.GetSubFolderList() + [rf]
    for f in fols:
        for c in f.GetClipList():
            if c.GetName() == name: return c
def tl_get(name):
    for i in range(1, project.GetTimelineCount() + 1):
        t = project.GetTimelineByIndex(i)
        if t.GetName() == name: return t
def tl_new(name, fps="30"):
    old = tl_get(name)
    if old:
        project.DeleteAllRenderJobs()
        other = next((project.GetTimelineByIndex(i) for i in range(1, project.GetTimelineCount() + 1)
                      if project.GetTimelineByIndex(i).GetName() != name), None)
        if other: project.SetCurrentTimeline(other)
        mp.DeleteTimelines([old])
    mp.SetCurrentFolder(folder("timelines"))
    t = mp.CreateEmptyTimeline(name)
    t.SetSetting("useCustomSettings", "1")
    t.SetSetting("timelineResolutionWidth", "1080"); t.SetSetting("timelineResolutionHeight", "1920")
    t.SetSetting("timelineFrameRate", fps)
    mp.SetCurrentFolder(rf)
    project.SetCurrentTimeline(t)
    return t
def export_default(item, path):
    if not item.GetFusionCompNameList(): item.AddFusionComp()
    item.ExportFusionComp(path, 1)
    return open(path).read()
def import_clip_comp(item, path):
    old = item.GetFusionCompNameList() or []
    item.ImportFusionComp(path)
    for n in old:
        if len(item.GetFusionCompNameList()) > 1: item.DeleteFusionCompByName(n)
    names = item.GetFusionCompNameList()
    if len(names) > 1:
        item.LoadFusionCompByName(names[-1])
    return names
def render(tl, path, w=540, h=960, mark=None, wait=180):
    project.SetCurrentTimeline(tl)
    resolve.OpenPage("deliver")
    project.DeleteAllRenderJobs()
    d, f = os.path.split(path)
    s = {"TargetDir": d, "CustomName": os.path.splitext(f)[0], "FormatWidth": w, "FormatHeight": h,
         "ExportVideo": True, "ExportAudio": True, "SelectAllFrames": mark is None}
    if mark: s.update({"MarkIn": mark[0], "MarkOut": mark[1]})
    project.SetRenderSettings(s)
    project.SetCurrentRenderFormatAndCodec("mp4", "H264")
    jid = project.AddRenderJob()
    project.StartRendering([jid], False)
    t0 = time.time()
    while project.IsRenderingInProgress() and time.time() - t0 < wait: time.sleep(0.5)
    st = project.GetRenderJobStatus(jid)
    if not project.IsRenderingInProgress():
        project.DeleteAllRenderJobs(); resolve.OpenPage("edit")
    return st, round(time.time() - t0, 1)
def save(): return resolve.GetProjectManager().SaveProject()
