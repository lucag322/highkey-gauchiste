# Mission aperçu lot 3 (un agent par vidéo) — HORS Resolve

INTERDIT : DaVinci Resolve. Seulement un aperçu basse qualité ffmpeg/Python, validé par Luca avant toute finition.
Projet : ~/Movies/highkey-gauchiste (lien vers iCloud Drive). Python : ~/.claude/skills/resolve-studio-editor/.venv/bin/python. Whisper est installé (voir lot2/_claude/tx.sh).

## À lire
- lot3/_claude/brief-lot3.md : ta ligne (style, figure, son).
- lot2/_claude/mission-apercu.md et lot2/_claude/brief-lot2.md : TOUTES les règles de Luca et la méthode valent pour le lot 3 (rythme sur vraies frappes mesuré < 20 ms sur l'export, visages entiers, 9:16 plein écran, pas de guillemets, pas de dézoom, plans ≥ 1 temps, phrases réelles mot à mot, -14 LUFS / TP ≤ -1 dBTP…).
- _claude/outils/LISEZMOI.md : outils (framing, faces, checkcut, cards, words, fx, sheet.sh) et pièges.
- Style validé (aura N&B, glow, citation ciné) : modèle dans lot2/_claude/gen (A1-A5 aura, G1-G3 glow, C1-C3 citation) et ~/Documents/Cerveau/Projets/highkey-gauchiste/da.md.
- Style inspi (archivage lazy, portrait couloir, karaoké discours, longue pose N&B) : la fiche du créateur dans ~/Documents/Cerveau/Projets/highkey-gauchiste/inspis/ (section « Recette avec nos outils », « À ne pas recopier »). Copier la recette, pas inventer.

## Règles en plus pour le lot 3
- Glow : toujours en couleur, aucune image en noir et blanc.
- Toujours le son de la vidéo en plus de la musique : au moins une vraie phrase de la figure (voix audible, musique baissée dessous), jamais un edit musique seule (Luca, retour sur V1).
- Passage du son : le moment le plus connu du morceau (refrain, hook, phrase culte, celui des edits TikTok), pas l'intro. Montée sous la phrase de la figure, drop sur ce moment (Luca, retours A7 et K1).
- Son et paroles choisis par Luca : les garder tels quels, ne rien censurer ni remplacer de ta propre initiative. Si tu vois un vrai risque, écris-le dans le rapport, c'est tout.
- AUCUNE archive : pas de dossier _anciens / _retires, pas de copie *_v1. Tu écrases tes propres fichiers.
- Durée max : 15 s (aura, glow, portrait couloir, longue pose), 20 s (citation ciné, karaoké, archivage lazy).
- Sources : vidéos réelles de la figure (chaînes officielles LFI, Assemblée nationale, médias), vérifie qu'elle est toujours LFI aujourd'hui. Télécharge seulement les extraits utiles (méthode lot2/_claude/dl.sh, mais dans lot3/sources/<id>-…). Son : audio officiel (chaîne de l'artiste ou du label, lien du brief) dans lot3/sons/<id>-….wav.
- N'écris que dans lot3/_claude/gen/<id>/, lot3/sources/<id>-*, lot3/sons/<id>-* et preview/apercu-<id>.mp4 : 9 autres agents travaillent en parallèle. Pas de fichier commun à modifier : ta fiche son va dans lot3/_claude/gen/<id>/son.json (titre, artiste, url, extrait utilisé début/fin, bpm, drop, frappes).
- Rien sur Discord : Claude vérifie et poste lui-même.

## Rendu
Dans lot3/_claude/gen/<id>/ : script gen<id>.py, plans ProRes 1080×1920 30 i/s dans out/ (pas de ralenti précalculé : speed_pct + optical flow notés dans le plan pour Resolve), mix out/<id>-mix.wav, plan-<id>.json au même format que lot2 (video : clip, s, e, rec, dur, clip_fps, speed_pct ; audio : mix), et l'aperçu preview/apercu-<id>.mp4 (540×960 H.264). Planche à 2 i/s regardée toi-même.

## Rapport (8 lignes max)
Phrase(s) utilisée(s) mot à mot avec source (URL + temps), extrait du son (début/fin) et paroles audibles, durée, écart max coupes/frappes mesuré, LUFS/TP, visages OK, ce que tu as repris de la recette, doutes.
