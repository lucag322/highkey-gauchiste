# Montage des 6 tests — notes du motion-designer (26/10/2026)

Projet Resolve « highkey-gauchiste tests », une timeline par style (1080×1920). Méthode commune :
- Chaque plan de source a sa compo Fusion générée en fichier (`_claude/comps/<n>/F_<image>.comp`, construite sur le MediaIn exporté du clip) : cadre letterbox, LUT du style (`_claude/luts/`), mouvements, flous, textes.
- Les graphismes impossibles à faire proprement en Fusion par script (texture journal, détourage, glitch, halo…) sont calculés en Python (`_claude/gen/<n>/`) et posés comme clips ProRes.
- Sons préparés dans `_claude/audio/` (voix extraite aux timecodes exacts du dérush, musique avec enveloppe de ducking) ; mix final ≈ -14/-15 LUFS, crête < -1 dBFS.
- Exports proxy 540×960 dans `exports/`, planches contact dans `_claude/sheets/`.

## 6 — Edit moqueur (`exports/test-6-edit-moqueur.mp4`, 13,0 s) — EN PAUSE (retour Luca : pas moqueur, le journal dit que Macron a de l'aura ; halo/rayons de fin refusés)
Cadre 3:4 (1080×1440) centré dans le 9:16 noir, comme la réf (720×960).
Voix : Macron 24,0-31,0 s du dérush, phrase entière, posée à 3,0-10,0 s ; musique de la réf 0-13 s, baissée de 9 dB sous la voix.
| t (s) | plan |
|---|---|
| 0-3,2 | page de journal floue (texte générique sur l'« Aura », attribué à personne), « Aura » surligné jaune, vues qui glissent puis rafale de 3 images |
| 3,2-3,9 | glitch (RGB + tranches) et Macron détouré (Vision Apple) qui surgit du bas, balayage |
| 3,9-5,5 | extrait plein cadre puis encadré 85 % sur noir |
| 5,5-6,6 | journal + Macron qui surgit sur « pognon de dingue » |
| 6,6-8,0 | plein cadre, encadré qui pivote (carte 3D), encadré 70 % |
| 8,0-8,6 | rafale journal + surgissement |
| 8,6-10,5 | plein cadre secoué (flous de mouvement, punch zoom) sur « On n'en sort pas » |
| 10,5-11,4 | gros plan main au menton (source 40,5 s, hors voix), journal |
| 11,4-13 | halo blanc, rayons, noir |
Diffère encore de la réf : une seule source vidéo (la réf mélange photos, archives, vue aérienne) ; pas de cadre « photo datée » ; pas de sous-titres (la réf n'en a pas, à décider si on veut la phrase écrite) ; glitch fait en Python, pas en Fusion.

## 2 — Speech edit — ABANDONNÉ (retour Luca : ennuyeux, sans musique). Ne plus réexporter. Dernier fichier : `exports/test-2-speech-edit.mp4`.

## Règles Luca (26/10, priment sur la DA)
Plein écran 9:16 sans bandes, sujet entier (tête jamais coupée, vérifié par `outils/checkcut.py`), edit porté par une musique tendance, voix en intro ou courts extraits, plans variés (plusieurs sources/moments), texte gros et lisible (halo derrière, contour, lettres nettes), couleur du halo tirée de la palette de la source, ralentis en Optical Flow Resolve, pas de halo blanc/rayons.

## 4 — Glow (`exports/test-4-glow.mp4`, 14,5 s) — timeline « 4 - Glow »
- Voix : Boyard, franceinfo Le Duel (duel-a) 51,72-57,12 s, phrase entière « Que vous soyez de gauche ou de droite, je pense que vous devriez aller pour défendre ces adolescents qui risquent leur vie. » ; musique de la réf (`sons/4-lbn7182_sans-voix.wav`) de 5,4 s à 14,4 s, coupes aux temps de la réf.
- Cartons de 1-3 mots, Avenir Next Bold Italic majuscules, blanc + mots-clés rouges (ADOLESCENTS, RISQUENT, LEUR VIE), halo violet #A58BE8 (décor violet du plateau), contour sombre.
- v4 (retour Luca : flashs bizarres) : plus de flashs, de noir ni de N&B ; coupes sur les temps (97 BPM), aucun plan < 1 temps (min 0,6 s, vérifié par détection de coupes) ; punch-in adoucis.
- v5 (retour Luca : dézooms bizarres) : plus aucun saut ni retour de zoom ; cadrage stable sur le visage avec poussée lente, uniquement vers l'avant (framing.py monotonic=True, vérifié sur les clés des comps) ; plan N&B remis en vrai plan de 0,63 s sur le 1er temps fort de la musique (5,4 s).
- Plans (source, s) : duel-a 51,72 (sync) · duel-a 96 N&B · duel-b 36 ralenti · duel-a 112 ralenti · duel-b 2 · duel-a 26 ralenti · duel-a 22 · duel-b 8 ralenti · duel-b 56 · duel-a 64 ralenti, fondu noir. Ralentis : SetSpeed 50 % + Optical Flow / Speed Warp.
- Recadrage 9:16 suivi du visage (Vision), bornes sans bandeau ni logo ; checkcut : 0 tête coupée sur 144 images.
- Diffère de la réf : réf 12 s avec 2,4 s de voix (ici 5,4 s pour garder la phrase entière) ; une seule émission (pas d'autres débats TV de Boyard dans sources/ hors CNews, écarté : bandeau hostile et visage trop large pour le 9:16 sous le bandeau) ; image plus nette mais upscale ×2,8 depuis le demi-écran 954×720 (un peu doux) ; pas de flous de mouvement en balayage (retirés : ils sortaient la tête du cadre).

## 1 — Aura N&B (`exports/test-1-aura-nb.mp4`, 18,1 s) — timeline « 1 - Aura N&B » (assemblage)
- Assemblée depuis plan1.json (17 plans ProRes 9:16 préparés hors Resolve dans gen/1/out, mix gen/1/out/1-mix.wav). Ralentis Resolve 60 % Optical Flow + Speed Warp sur passerelle, foule_dos, pupitre.
- Vérifié : coupes identiques à l'aperçu (2 / 5,5 / 6,17 … 16,53 s), plan le plus court 0,67 s ; 0 tête coupée (180 images) ; -13,9 LUFS, crête -1,5 dBFS.

## 3 — Citation ciné (`exports/test-3-citation-cine.mp4`, 33,7 s) — timeline « 3 - Citation ciné » (assemblage)
- Assemblée depuis plan3.json (24 plans ProRes 9:16 de gen/3/out, mix 3-mix.wav). 14 ralentis 50 % Optical Flow + Speed Warp ; fondu au noir de 21 images sur le dernier plan (SetFades) ; B03 pris sur 64 images à 50 i/s au lieu de 63 pour éviter un trou d'une image.
- Vérifié : coupes identiques à l'aperçu ; synchro labiale Q2 / Q4 / V1 à +1 / +14 / -1 ms (corrélation audio source ↔ export) ; -14,0 LUFS, crête -1,9 dBFS ; checkcut : 3 images signalées, ce sont des visages de la foule au bord du cadre dans les plans larges (15,7 s et 17,9 s), aucun plan de Mélenchon coupé.

## 5 — Phonk (`exports/test-5-phonk.mp4`, 15,9 s) — timeline « 5 - Phonk » (assemblage)
- Assemblée depuis plan5.json (17 plans ProRes 9:16 en V1, 5_TXT.mov ProRes 4444 alpha en V2 mode Normal, mix 5-mix.wav en A1, stems voix/musique en A2/A3 pistes coupées). C7 à 50 % Optical Flow + Speed Warp.
- Vérifié : coupes et planche identiques à l'aperçu ; plans les plus courts 0,40 s = 1 temps à 145 BPM ; 0 tête coupée (159 images) ; -14,0 LUFS, crête -7,3 dBFS (comme l'aperçu).

### Style 4 v6 (mots rouges en Thunder)
- ADOLESCENTS, RISQUENT, LEUR VIE en Thunder Black LC Italic, même halo et contour. Taille Text+ = em × asz(police)/1,37 ; ligne de base recalée de −0,273 em (mesuré, Text+ ne suit pas les métriques PIL) : écart mesuré 1 px avec les mots blancs.
- Export exports/test-4-glow.mp4 : 14,5 s, −13,9 LUFS, 0 tête coupée, accents OK (DÉFENDRE).

### Style 1 : 1_long.mov rechargé (ReplaceClip), export refait — 18,07 s, −13,9 LUFS, 0 tête coupée, image du rendu = nouveau fichier (PSNR 31 dB).

### Style 3 : Q1, Q3, Q4, V1 rechargés (ReplaceClip), export refait — 33,66 s, −14,0 LUFS ; plus de guillemets, mots rouges en Caslon, accents OK ; checkcut : 3 têtes de foule en bord à 15,7-17,9 s (plans inchangés, déjà acceptés).

### Style 4 v7 (retour Luca) : Thunder et rouge retirés, tout en blanc Avenir Next Bold Italic, halo violet + contour sombre. Export 14,5 s, −13,9 LUFS, 0 tête coupée.
### Style 1 : 1_long.mov (Arial Black) rechargé, export 18,07 s, −13,9 LUFS, 0 tête coupée, rendu = nouveau fichier (PSNR 34 dB).
