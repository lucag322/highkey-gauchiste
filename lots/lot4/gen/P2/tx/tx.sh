#!/bin/bash
# transcrit les sources Delogu du lot 3 (mot à mot) dans lot4/_claude/gen/P2/tx
cd ~/Movies/highkey-gauchiste/lot4/_claude/gen/P2/tx
for f in "$@"; do
  n=$(basename "$f" .mp4); [ -f "$n.json" ] && continue
  mlx_whisper "$f" --model mlx-community/whisper-large-v3-turbo --language fr --word-timestamps True --output-format json --output-dir . --output-name "$n" --verbose False --condition-on-previous-text False >/dev/null 2>>tx.err
  echo "done $n" >> tx.log
done
