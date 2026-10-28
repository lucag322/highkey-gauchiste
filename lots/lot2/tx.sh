#!/bin/bash
# usage: tx.sh id... ; télécharge l'audio + transcrit (turbo fr, mots)
cd ~/Movies/highkey-gauchiste/lot2/_claude/tx
for id in "$@"; do
  [ -f "$id.json" ] && continue
  [ -f "audio/$id.m4a" ] || yt-dlp -q -f "bestaudio[ext=m4a]/bestaudio" -o "audio/$id.%(ext)s" "https://www.youtube.com/watch?v=$id" 
  f=$(ls audio/$id.* | head -1)
  mlx_whisper "$f" --model mlx-community/whisper-large-v3-turbo --language fr --word-timestamps True --output-format json --output-dir . --output-name "$id" --verbose False --condition-on-previous-text False >/dev/null 2>>../tx.err
  echo "done $id" >> ../tx.log
done
