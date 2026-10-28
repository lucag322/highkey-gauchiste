# Mission aperçu lot 6 (un agent par vidéo) — HORS Resolve

INTERDIT : DaVinci Resolve. Seulement un aperçu basse qualité ffmpeg/Python, validé par Luca avant toute finition.
Projet : ~/Movies/highkey-gauchiste (lien vers iCloud Drive). Python : ~/.claude/skills/resolve-studio-editor/.venv/bin/python. Whisper est installé (voir lot2/_claude/tx.sh).

## À lire
- lot6/_claude/brief-lot6.md : ta ligne (style, figure, son).
- lot2/_claude/mission-apercu.md et lot2/_claude/brief-lot2.md : TOUTES les règles de Luca et la méthode valent pour le lot 6 (rythme sur vraies frappes mesuré < 20 ms sur l'export, visages entiers, 9:16 plein écran, pas de guillemets, pas de dézoom, plans ≥ 1 temps, phrases réelles mot à mot, -14 LUFS / TP ≤ -1 dBTP…).
- _claude/outils/LISEZMOI.md : outils (framing, faces, checkcut, cards, words, fx, sheet.sh) et pièges.
- Style validé (aura N&B, glow, citation ciné) : modèle dans lot2/_claude/gen (A1-A5 aura, G1-G3 glow, C1-C3 citation) et ~/Documents/Cerveau/Projets/highkey-gauchiste/da.md.
- Style inspi (archivage lazy, portrait couloir, karaoké discours, longue pose N&B) : la fiche du créateur dans ~/Documents/Cerveau/Projets/highkey-gauchiste/inspis/ (section « Recette avec nos outils », « À ne pas recopier »). Copier la recette, pas inventer.

## Sources : réutiliser l'existant (lot 6)
- Vidéos déjà téléchargées : lot1/sources, lot2/sources, lot3/sources, lot4/sources, lot5/sources (nom = <id>-<figure>-<lieu>). Transcriptions mot à mot avec temps : lot2/_claude/tx/*.json (nom = id YouTube), lot3/_claude/gen/*/tx, lot1/_claude/tx. Plans et phrases déjà utilisés : plan-*.json de chaque lot.
- Prends une AUTRE phrase et d'autres plans que les edits déjà faits avec la même figure (lis leurs plan-*.json) : le compte ne doit pas répéter les mêmes images.
- Ne télécharge un nouvel extrait (lot6/sources/<id>-…) que si les sources existantes n'ont pas ce qu'il faut (ex. archives pour l'archivage, plans d'un autre contexte pour le multi-contextes) ; le son, lui, se télécharge (lot6/sons).
- Styles déjà faits à imiter : archivage → lot3 Z1 et lot4 Z2, karaoké → lot3 K1 et lot4 K2, portrait → lot3 P1 et lot4 P2, longue pose → lot3 V1 et lot4 V2, glow → lot4 G5/G6, citation → lot3 C4/C5 et lot4 C6, aura → lot3 A6/A8 et lot4 A9, aura couleur → lot4 M1/M2. Styles NOUVEAUX (W1 aura mots power, R1 collage ransom-note) : suis la fiche inspi (inspis/2026-10-26 magafx… et inspis/2026-10-26 abdulelsayed…), section « Recette avec nos outils ».

## Règles en plus pour le lot 6
- Glow : toujours en couleur, aucune image en noir et blanc.
- Voix de la figure = plan synchro (même source, même moment) OU plan où elle ne parle pas (écoute, salle, de dos, foule). Jamais un autre plan où elle parle sous sa voix : on dirait que le son ne colle pas (Luca, retour K3, 27/10). En musique seule après le drop, libre.
- Phrase forte et pertinente : une attaque claire ou une punchline qui marche seule, pas une phrase banale (« nous voulons gagner en 2027 » refusée, retour G7).
- Toujours le son de la vidéo en plus de la musique : au moins une vraie phrase de la figure (voix audible, musique baissée dessous), jamais un edit musique seule (Luca, retour sur V1).
- Passage du son : le moment le plus connu du morceau (refrain, hook, phrase culte, celui des edits TikTok), pas l'intro. Montée sous la phrase de la figure, drop sur ce moment (Luca, retours A7 et K1).
- Son et paroles choisis par Luca : les garder tels quels, ne rien censurer ni remplacer de ta propre initiative. Si tu vois un vrai risque, écris-le dans le rapport, c'est tout.
- AUCUNE archive : pas de dossier _anciens / _retires, pas de copie *_v1. Tu écrases tes propres fichiers.
- Durée max : 15 s (aura, glow, portrait couloir, longue pose), 20 s (citation ciné, karaoké, archivage lazy).
- Sources : vidéos réelles de la figure (chaînes officielles LFI, Assemblée nationale, médias), vérifie qu'elle est toujours LFI aujourd'hui. Télécharge seulement les extraits utiles (méthode lot2/_claude/dl.sh, mais dans lot6/sources/<id>-…). Son : audio officiel (chaîne de l'artiste ou du label, lien du brief) dans lot6/sons/<id>-….wav.
- N'écris que dans lot6/_claude/gen/<id>/, lot6/sources/<id>-*, lot6/sons/<id>-* et preview/apercu-<id>.mp4 : 4 autres agents travaillent en parallèle et lisent les mêmes sources : ne modifie ni ne déplace aucun fichier des lots 1 à 5. Pas de fichier commun à modifier : ta fiche son va dans lot6/_claude/gen/<id>/son.json (titre, artiste, url, extrait utilisé début/fin, bpm, drop, frappes).
- Rien sur Discord : Claude vérifie et poste lui-même.

## Rendu
Dans lot6/_claude/gen/<id>/ : script gen<id>.py, plans ProRes 1080×1920 30 i/s dans out/ (pas de ralenti précalculé : speed_pct + optical flow notés dans le plan pour Resolve), mix out/<id>-mix.wav, plan-<id>.json au même format que lot2 (video : clip, s, e, rec, dur, clip_fps, speed_pct ; audio : mix), et l'aperçu preview/apercu-<id>.mp4 (540×960 H.264). Planche à 2 i/s regardée toi-même.

## Rapport (8 lignes max)
Phrase(s) utilisée(s) mot à mot avec source (URL + temps), extrait du son (début/fin) et paroles audibles, durée, écart max coupes/frappes mesuré, LUFS/TP, visages OK, ce que tu as repris de la recette, doutes.

## Textes et interface TikTok (Luca, 26/10)
Tous les textes (cartons, sous-titres, karaoké) hors de l'interface TikTok : bloc centré ≤ 66 % de la largeur (x 0,17-0,83, boutons à droite), entre 12 % et 75 % de la hauteur (onglets en haut, pseudo et légende en bas). Réduire ou couper en lignes plutôt que déborder. Contrôle obligatoire sur l'export : `python3 _claude/outils/zones_tiktok.py preview/apercu-<id>.mp4` doit dire « tous dans la zone sûre TikTok ».

## Style du lot 6 : collage ransom-note (Luca, 27/10)
- Modèle : lot5/_claude/gen/R1 (genR1.py et ses fonctions : découpe de la figure, morceaux de texte penchés serif/sans mélangés, frappes, carton final). Réutilise ce code (copie dans ton dossier gen/<id>/), ne repars pas de zéro.
- Pousser plus loin que R1 : plus de découpes et de couches, textures papier (grain, déchirures, scotch), rythme calé sur les frappes. Aplat blanc plein cadre seulement en flash de transition (2 à 4 images), jamais tenu.
- Chaque edit a sa palette (voir le brief) : les 5 ne doivent pas se ressembler entre eux ni copier les couleurs de R1.
- Phrase : une NOUVELLE phrase forte de la figure (pas celles des edits déjà faits avec elle, lis leurs gen*.py et plan-*.json). Mots en grand = mots de la phrase entendue.
- Durée : 20 s au plus.
- Textes après le drop (Luca, 27/10, retour R3/R4/R6) : chaque carton se lit seul et fait sens. Des groupes de mots complets, dans l'ordre de la phrase (ou sa conclusion évidente), un groupe par plan ou par temps : « SANCTIONNÉ. INTIMIDÉ. MENACÉ. MOQUÉ. » puis « MES VALEURS N'ONT PAS TITUBÉ ». Jamais de mot isolé sans sens (« DE », « UN », « ME »), jamais de mots dans le désordre ou de bouts de mots, jamais deux fois le même groupe.
- Fin des vidéos de Mélenchon (Luca, 27/10) : carton final « JEAN-LUC MÉLENCHON » + « 2027 » (année de l'élection), jamais d'autres dates.
