#!/bin/bash
SRC=~/Movies/highkey-gauchiste/lot1/sources/5-melenchon-saintdenis-smic.mp4
while read a b; do
  /opt/homebrew/bin/ffmpeg -v error -y -ss $a -t $b -i $SRC -ac 1 -ar 16000 p.wav
  mlx_whisper p.wav --model mlx-community/whisper-large-v3-turbo --language fr --output-format txt --output-dir . --output-name p --verbose False >/dev/null 2>&1
  echo "$a+$b: $(cat p.txt)"
done
