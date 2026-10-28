import subprocess, os
S = "/Users/luca.grousset/Movies/highkey-gauchiste/sources/"
FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
specs = [("a",3),("a",8),("a",22),("a",26),("a",36),("a",55),("a",61),("a",64),("a",68),("a",74),("a",86),("a",96),("a",104),("a",112),("b",2),("b",8),("b",12),("b",46),("b",62),("c",17),("c",19),("c",30),("c",42),("c",52)]
os.makedirs("cand", exist_ok=True)
for i,(k,t) in enumerate(specs):
    f = {"a":"4-boyard-franceinfo-duel-a.mp4","b":"4-boyard-franceinfo-duel-b.mp4","c":"4-boyard-cnews-debat.mp4"}[k]
    cr = {"a":"crop=720:720:1160:130","b":"crop=720:720:1160:130","c":"crop=900:900:960:0"}[k]
    if k=="b" and t<13: cr="crop=640:640:0:150"
    subprocess.run([FF,"-v","error","-y","-ss",str(t),"-i",S+f,"-frames:v","1","-vf",cr+",scale=200:200,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%s %s':x=4:y=4:fontsize=20:fontcolor=yellow:box=1:boxcolor=black"%(k,t),"cand/c%02d.png"%i])
subprocess.run([FF,"-v","error","-y","-framerate","1","-i","cand/c%02d.png","-vf","tile=8x3","-frames:v","1","cand.jpg"])
