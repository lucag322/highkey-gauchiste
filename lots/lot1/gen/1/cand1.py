import subprocess
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"; S = "/Users/luca.grousset/Movies/highkey-gauchiste/sources/1-melenchon-valence-amfis.mp4"
T = [20, 22, 28, 34, 44, 52, 57, 60, 67, 74, 76, 96, 101, 109, 118, 126, 131, 136, 141, 146, 150.5, 152, 157, 163, 166, 170, 173]
for i, t in enumerate(T):
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", S, "-frames:v", "1", "-vf", "scale=240:-2,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%s':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black" % t, "c%02d.png" % i])
subprocess.run([FF, "-v", "error", "-y", "-framerate", "1", "-i", "c%02d.png", "-vf", "tile=7x4", "-frames:v", "1", "cand1.jpg"])
