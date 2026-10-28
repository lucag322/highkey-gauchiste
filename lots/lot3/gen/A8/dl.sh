#!/bin/bash
# dl.sh id start end outname  (copie de lot2/_claude/dl.sh, sortie lot3/sources/A8-*)
id=$1; s=$2; e=$3; out=$4
cd ~/Movies/highkey-gauchiste/lot3/sources
args=()
[ "$e" != "0" ] && args=(--download-sections "*$s-$e" --force-keyframes-at-cuts)
yt-dlp -q --no-warnings -f "bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]" "${args[@]}" -o "$out.%(ext)s" --merge-output-format mp4 "https://www.youtube.com/watch?v=$id" 2>&1 | tail -2
c=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$out.mp4")
if [ "$c" != "h264" ]; then ffmpeg -v error -y -i "$out.mp4" -c:v libx264 -crf 14 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k "$out.h264.mp4" && mv "$out.h264.mp4" "$out.mp4"; fi
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of csv=p=0 "$out.mp4" | tr '\n' ' '; echo
