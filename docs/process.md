# Process des lots highkey-gauchiste
↑ [[Projets/highkey-gauchiste/highkey-gauchiste|highkey-gauchiste]] · [[Projets/highkey-gauchiste/historique|historique]] · [[Projets/highkey-gauchiste/da|DA]] · [[Projets/highkey-gauchiste/inspis|inspis]]

Dossier de travail : `~/Movies/highkey-gauchiste` (lien vers iCloud Drive). Un dossier par lot : `lot1/` à `lot4/` (sources, sons, `_claude/brief-lotN.md`, `_claude/mission-lotN.md`, `_claude/gen/<id>/`). Outils communs : `_claude/outils/` (LISEZMOI.md).

## 1. Choisir le lot (quiz)
- Avant le quiz, Claude lit [[Projets/highkey-gauchiste/historique|historique]] et propose d'abord les styles, figures et sons les moins faits (pas de spam du même style). Après le lot, il y ajoute les nouveaux edits.
- Moitié du lot = Mélenchon (ex. 5 sur 10), dans des styles et des moments variés ; l'autre moitié = autres figures LFI.
- Claude pose un quiz par edit : figure, style (DA validée ou fiche [[Projets/highkey-gauchiste/inspis|inspis]]), son avec lien YouTube officiel calé sur le passage. Une dizaine d'edits, puis récap.
- Il écrit le brief `lotN/_claude/brief-lotN.md` (tableau id / style / figure / son) et la mission des agents `mission-lotN.md`.
- Lot 4 : réutilise les sources des lots 1 à 3 et les transcriptions (`lot2/_claude/tx/*.json`), autres phrases et autres plans.

## 2. Aperçus (un agent par edit, hors Resolve)
- Règles : toutes celles de la DA et de `Montage/Looks & titres/préférences.md` ; voix de la figure toujours audible ; passage le plus connu du son, jamais l'intro ; glow en couleur ; 15 s (20 s citation, karaoké, archivage) ; aucune archive de version.
- Textes jamais sous l'interface TikTok (bloc centré ≤ 66 % de large, entre 12 % et 75 % de haut) : contrôle `_claude/outils/zones_tiktok.py`, lancé par `verif_apercu.sh`.
- Claude vérifie chaque aperçu (durée, -14 LUFS, têtes coupées, textes, planche) puis le poste : `npm run apercu -- <id> <video> "<texte>"` dans discord-bot. Boutons Valider / À refaire, choix noté dans `preview/validations.json`.
- Barre d'avancement du lot : message Discord mis à jour toutes les 2 min, ou `/avancement`.

## 3. HD (Resolve, seulement après validation)
- Une seule HD par edit, toujours de la dernière version (v2 écrase v1 dans gen/<id>/out) ; jamais de HD d'une v1 quand une v2 existe (Luca, 27/10).
- Luca valide sur Discord puis dit « lance les HD » (Claude ne voit les validations que quand Luca lui écrit).
- `lot2/_claude/gen/prep_hd.py <id> <lotN>` (plans ramenés à 30 i/s), `hd_lot2.py` : `build_hd(id, "lotN")` puis `render_hd([...])` dans Resolve, ralentis en Optical Flow.
- `_claude/outils/finir_hd.sh <id> <lotN> <figure> "<légende>" "<#tags>"` : remet le son propre, contrôles, supprime l'aperçu, range la HD dans `hd/<style>/` (dossier par style, d'après la lettre de l'id ; Resolve rend toujours dans `hd/`), dépose la HD + JSON (légende, hashtags, `apres_envoi`) dans `a-publier/`. Si la vidéo attend déjà dans `a-publier/proposees/`, elle y est remplacée sur place (même message Discord, même légende).

## 4. Envoi TikTok (bot Discord, module tiktok)
- Le bot poste chaque HD de `a-publier/` avec Valider / Refuser. Valider = brouillon TikTok (API upload, app sandbox « highkey bot »).
- TikTok met 15 à 45 min : le message passe de ⏳ à ✅ à l'arrivée ; le bot supprime alors la vidéo, la HD et les fichiers de travail (`apres_envoi`).
- Limite TikTok : 5 brouillons en attente par 24 h. Au-delà, la vidéo passe « en file d'attente » (`proposees/<nom>.attente.json`) et le bot réessaie seul toutes les 30 min, une par passage.
- La légende part dans un message Discord à part. Page de copie : artifact « Légendes highkey.gauchiste » (https://claude.ai/artifact/4mtbcQ3ET7Prx3W3CoHNMP).
- Dans TikTok : effacer `#highkeybot` (ajouté par TikTok), coller la légende, publier. Une vidéo publiée à la main : le dire à Claude, qui la retire de la file.
- Mettre la file en pause : renommer `proposees/<nom>.attente.json` en `.pause.json` (et l'inverse pour relancer).
- `/tiktok` donne l'état (connecté, à valider, envoyées, silence électoral).

## État au 26/10/2026 (nuit)
- Publiée à la main : C3 Mélenchon.
- Dans les brouillons TikTok : G2 Aubry, A2 Bompard, G1 Boyard, A3 Chikirou, C2 Coquerel, G3 Léaument (x2 tests).
- File d'attente : 24 HD = 14 des lots 1 à 3 (textes replacés hors interface TikTok le 26/10) + les 10 HD du lot 4 (M1, M2, G5, G6, Z2, K2, C6, P2, A9, V2).
- K1 Boyard : rallongé à 22 s (demande de Luca), aperçu v2 sur Discord ; HD à refaire après validation, sa place dans la file est en pause (`boyard-K1.pause.json`).
