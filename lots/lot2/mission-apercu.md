# Mission aperçu lot 2 (un agent par vidéo) — HORS Resolve

INTERDIT : DaVinci Resolve. Seulement un aperçu basse qualité ffmpeg/Python, validé par Luca avant toute finition.

Lire : lot2/_claude/brief-lot2.md (règles de Luca, toutes), lot2/_claude/polices.md, _claude/outils/LISEZMOI.md (outils réutilisables : framing.py, cards.py, words.py, fx.py, faces, segment, sheet.sh, checkcut.py ; Python = ~/.claude/skills/resolve-studio-editor/.venv/bin/python), le modèle validé du style :
- Citation ciné : _claude/gen/3/gen3.py + exports/test-3-citation-cine.mp4 (le préféré de Luca : copier sa structure, sa typo — serif espacée + mots-clés rouges en CaslonGraphique-Opti, sans guillemets — et son étalonnage sépia).
- Aura N&B : _claude/gen/1/gen1.py + exports/test-1-aura-nb.mp4 (Arial Black, mot-clé rouge, pas de police dramatique).
- Glow : _claude/gen/4/gen4.py + exports/test-4-glow.mp4 (Avenir Next Bold Italic, TOUT le texte blanc + halo couleur prise dans la vidéo + contour, jamais de rouge).
Données : lot2/_claude/derush-C.json ou derush-AG.json (ton id), lot2/_claude/sons-lot2.json (ton son, gain conseillé, downbeats).

Règles clés : RYTHME — ne jamais se fier à la grille de sons-lot2.json : détecter les vraies frappes (kick/snare) dans le mix posé, caler coupes, drop et début/fin des zooms dessus, puis mesurer sur l'export (écart < 20 ms) ; DURÉE MAX 20 s pour la citation ciné, 15 s pour l'aura N&B et le glow (Luca : « vidéos trop longues ») ; AUCUN visage coupé au bord du cadre, ni la personne principale ni un visage secondaire visible (vérifier avec l'outil faces sur chaque plan, tous les visages de plus de 5 % de la hauteur doivent être entiers, sinon recadrer ou changer de plan) ; 9:16 plein écran, aucune tête coupée (checkcut = 0 sur la personne principale), aucun logo ni filigrane dans le cadre, plans ≥ 1 temps, coupes sur les downbeats, pas de dézoom (fixe ou poussée lente avant), N&B OK sauf dans le glow (glow toujours en couleur, jamais d'image N&B), jamais de guillemets, phrase réelle mot à mot sans rien couper qui change le sens, pas de fin halo blanc + rayons, musique du début à la fin (voix en intro ou courts extraits), mix ≈ -14 LUFS.
Ralentis : dans l'aperçu, setpts simple ; dans plan-<id>.json noter speed_pct + retime optical_flow pour la finition Resolve.

Rendre dans lot2/_claude/gen/<id>/ : script gen<id>.py, plans, mix, plan-<id>.json, et l'aperçu preview/apercu-<id>.mp4 (dossier ~/Movies/highkey-gauchiste/preview) (540×960, H.264). Vérifier toi-même la planche à 2 i/s.
Rapport 6 lignes : durée, phrase, son, sources des plans, doutes.
