#!/bin/bash
# peek.sh id t [t2 ...] : une image 640px par timecode (source)
id=$1; shift
cd ~/Movies/highkey-gauchiste/lot2/_claude/peek
for t in "$@"; do
  out="${id}_${t}.jpg"
  [ -f "$out" ] && continue
  yt-dlp -q --no-warnings -f "bv*[height<=480]" --download-sections "*$t-$((t+2))" -o "tmp_${id}_$t.%(ext)s" "https://www.youtube.com/watch?v=$id" 2>/dev/null
  f=$(ls tmp_${id}_$t.* 2>/dev/null | head -1)
  [ -n "$f" ] && ffmpeg -v error -y -ss 1 -i "$f" -frames:v 1 -vf scale=640:-1 "$out" && rm -f "$f"
done
