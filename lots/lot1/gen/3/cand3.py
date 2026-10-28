import subprocess
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"; S = "/Users/luca.grousset/Movies/highkey-gauchiste/sources/3-melenchon-huma-citation.mp4"
T = [72, 76, 82, 88, 92, 97, 101, 104, 107, 112, 116, 198, 203, 209, 219, 233, 240, 252, 258, 264, 272, 286, 291]
for i, t in enumerate(T):
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", S, "-frames:v", "1", "-vf", "scale=240:-2,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%s':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black" % t, "c%02d.png" % i])
subprocess.run([FF, "-v", "error", "-y", "-framerate", "1", "-i", "c%02d.png", "-vf", "tile=6x4", "-frames:v", "1", "cand3.jpg"])
