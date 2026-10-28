#!/bin/zsh
# sheet.sh in.mp4 out.jpg [fps=1] [cols=6] [w=180]
FF=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
in=$1; out=$2; fps=${3:-1}; cols=${4:-6}; w=${5:-180}
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in" | head -1)
n=$(python3 -c "import math;print(math.ceil($d*$fps))")
rows=$(( (n + cols - 1) / cols ))
$FF -v error -y -i "$in" -vf "fps=$fps,scale=$w:-2,drawtext=text='%{pts\:flt}':x=3:y=3:fontsize=13:fontcolor=yellow:box=1:boxcolor=black@0.7,tile=${cols}x${rows}:padding=2" -frames:v 1 -update 1 "$out"
echo "$out $n frames ${cols}x${rows}"
