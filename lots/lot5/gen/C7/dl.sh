#!/bin/bash
# dl.sh id start end outname [hauteur=2160]  (secondes source) -> lot5/sources/outname.mp4 (H.264)
id=$1; s=$2; e=$3; out=$4; hh=${5:-2160}
cd ~/Movies/highkey-gauchiste/lot5/sources
yt-dlp -q --no-warnings -f "bv*[height<=$hh]+ba[ext=m4a]/bv*[height<=$hh]+ba" --download-sections "*$s-$e" --force-keyframes-at-cuts -o "$out.%(ext)s" --merge-output-format mp4 "https://www.youtube.com/watch?v=$id" 2>&1 | tail -2
c=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$out.mp4")
if [ "$c" != "h264" ]; then ffmpeg -v error -y -i "$out.mp4" -c:v libx264 -crf 14 -preset fast -pix_fmt yuv420p -c:a aac -b:a 192k "$out.h264.mp4" && mv "$out.h264.mp4" "$out.mp4"; fi
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of csv=p=0 "$out.mp4" | tr '\n' ' '; echo
