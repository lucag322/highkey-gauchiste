#!/bin/bash
# Après le rendu Resolve d'une HD : son propre, contrôles, ménage, envoi vers le bot TikTok.
# Usage : finir_hd.sh <id> <lot2|lot3…> <slug-figure> "<Légende>" "#tag1 #tag2 …"
# 1. attend hd/HD-<id>.mp4 stable ; 2. remet le mix WAV (AAC 320k, piège du son en cache Resolve) ;
# 3. affiche durée, LUFS / true peak, SSIM moyen contre l'aperçu, têtes coupées ;
# 4. supprime l'aperçu et les copies _30.mov, range la HD dans hd/<style>/ (lettre de l'id) ; 5. dépose une copie (clone APFS) + JSON dans a-publier/,
#    ou remplace la vidéo dans a-publier/proposees/ si elle y attend déjà (HD refaite)
#    avec apres_envoi (HD et fichiers de travail supprimés par le bot quand le brouillon arrive).
set -euo pipefail
ID=$1; LOT=$2; SLUG=$3; LEGENDE=$4; TAGS=$5
R=~/Movies/highkey-gauchiste; G=$R/$LOT/_claude/gen/$ID; HD=$R/hd/HD-$ID.mp4; AP=$R/preview/apercu-$ID.mp4
PY=~/.claude/skills/resolve-studio-editor/.venv/bin/python
for _ in $(seq 1 120); do [ -f "$HD" ] && [ $(( $(date +%s) - $(stat -f %m "$HD") )) -gt 15 ] && break; sleep 5; done
ffmpeg -v error -y -i "$HD" -i "$G/out/$ID-mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart "$HD.tmp.mp4"
rm -f "$HD"; mv "$HD.tmp.mp4" "$HD"   # supprimer avant de remplacer : sinon iCloud garde le rendu brut en « HD-<id> 2.mp4 »
echo "durée $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$HD") s"
ffmpeg -nostats -i "$HD" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tr -s ' '
if [ -f "$AP" ]; then
  ffmpeg -v info -i "$HD" -i "$AP" -lavfi "[0:v]scale=540:960,fps=10[a];[1:v]fps=10[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*" | tail -1 | sed 's/^/SSIM moyen vs aperçu /'
fi
$PY $R/_claude/outils/checkcut.py "$HD" 2>&1 | grep -E "têtes coupées|^[0-9.]+s" || true
rm -f "$AP" "$R/hd/HD-$ID 2.mp4"; find "$G" -name "*_30.mov" -delete
case ${ID:0:1} in
  A|L) STYLE="Aura N&B" ;; C) STYLE="Citation ciné" ;; G) STYLE="Glow couleur" ;; K) STYLE="Karaoké discours" ;;
  P) STYLE="Portrait" ;; V) STYLE="Longue pose N&B" ;; Z) STYLE="Archivage lazy" ;; M) STYLE="Aura couleur multi-contextes" ;;
  R) STYLE="Collage ransom-note" ;; W) STYLE="Aura mots power" ;; I) STYLE="Phonk infographie" ;; S) STYLE="Arc solidarité" ;;
  *) STYLE="Autres" ;;
esac
mkdir -p "$R/hd/$STYLE"; rm -f "$R/hd/$STYLE/HD-$ID.mp4" "$R/hd/$STYLE/HD-$ID 2.mp4"   # HD refaite : supprimer avant, sinon iCloud garde l'ancienne en « HD-<id> 2.mp4 »
mv "$HD" "$R/hd/$STYLE/HD-$ID.mp4"; HD=$R/hd/$STYLE/HD-$ID.mp4
# HD refaite d'une vidéo déjà dans la file TikTok : on remplace la vidéo sur place (même message Discord, même JSON).
FILE=$R/a-publier/proposees/$SLUG-$ID.mp4
if [ -f "$FILE" ]; then cp -c "$HD" "$FILE.tmp" && mv "$FILE.tmp" "$FILE"; echo "remplacé dans la file : proposees/$SLUG-$ID"; exit 0; fi
cp -c "$HD" "$R/a-publier/$SLUG-$ID.mp4"
python3 - "$R/a-publier/$SLUG-$ID.json" "$LEGENDE" "$TAGS" "$ID" "$LOT" "$STYLE" <<'EOF'
import json, sys
f, legende, tags, i, lot, style = sys.argv[1:]
json.dump({"legende": legende, "hashtags": tags.split(), "apres_envoi": [f"hd/{style}/HD-{i}.mp4", f"{lot}/_claude/gen/{i}/out", f"{lot}/_claude/gen/{i}/cache"]},
          open(f, "w"), ensure_ascii=False)
EOF
echo "déposé a-publier/$SLUG-$ID"
