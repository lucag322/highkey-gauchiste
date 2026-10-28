#!/bin/bash
# Contrôle rapide d'un aperçu avant envoi Discord : durée, LUFS / true peak, têtes coupées, textes et visages sous l'interface TikTok, planche à 2 i/s.
# Usage : verif_apercu.sh <id> <planche.jpg>
R=~/Movies/highkey-gauchiste; F=$R/preview/apercu-$1.mp4
echo "$1 $(ffprobe -v error -show_entries format=duration -of csv=p=0 $F)s $(ffmpeg -nostats -i $F -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' ') $(~/.claude/skills/resolve-studio-editor/.venv/bin/python $R/_claude/outils/checkcut.py $F 2>&1 | grep -E 'têtes|^[0-9.]+s' | tr '\n' ' ')"
bash $R/_claude/outils/sheet.sh $F "$2" 2 8 120 >/dev/null 2>&1
python3 $R/_claude/outils/zones_tiktok.py $F | head -10
