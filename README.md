# highkey-gauchiste

Atelier d'edits TikTok verticaux (9:16) pour un compte TikTok militant : des agents Claude montent des aperçus,
Luca valide sur Discord, la HD sort de DaVinci Resolve, puis un bot Discord envoie les vidéos en brouillon sur TikTok.

Seuls le code et les notes sont ici : aucune vidéo, aucun son, aucun secret (les clés vivent dans le trousseau macOS).

## Le circuit

1. **Brief** (`lots/lotN/brief-lotN.md`) : un tableau style / figure / son par edit, choisi par Luca.
2. **Aperçu** : un agent par edit lit `lots/lotN/mission-lotN.md` et écrit `lots/lotN/gen/<id>/gen<id>.py`.
   Le script génère les plans ProRes 1080×1920 (textes cuits), le mix et un aperçu 540×960.
3. **Contrôles** (`outils/verif_apercu.sh`) : durée, volume (-14 LUFS), têtes coupées,
   textes et visages hors de l'interface TikTok (`outils/zones_tiktok.py`).
4. **Validation** : le bot poste l'aperçu sur Discord avec deux boutons, Valider ou À refaire (`bot/modules/apercu.js`).
5. **HD** : `lots/lot2/gen/prep_hd.py` puis `hd_lot2.py` montent la timeline et lancent le rendu dans Resolve ;
   `outils/finir_hd.sh` remet le son propre, contrôle et dépose la vidéo dans la file.
6. **TikTok** (`bot/modules/tiktok.js`) : file automatique vers les brouillons TikTok (API Content Posting),
   5 au plus par 24 h, en évitant d'envoyer plusieurs fois le même style à la suite.

## Dossiers

- `outils/` : outils partagés. `decoupe.py` découpe une personne (Apple Vision : instance croisée avec la
  segmentation), `zones_tiktok.py` repère textes et visages sous l'interface, `checkcut.py` les têtes coupées,
  `build.py` / `rhelp.py` pilotent Resolve. Mode d'emploi : `outils/LISEZMOI.md`.
- `lots/` : un dossier par lot, avec le brief, la mission des agents et le script de chaque edit.
- `bot/` : les modules du bot Discord liés au compte (aperçus, file TikTok, inspirations), extraits du bot complet.
- `docs/` : la direction artistique (`da.md`), le process et l'historique de tous les edits.

## Styles

Aura N&B, glow couleur, citation ciné, karaoké discours, portrait, longue pose N&B, archivage lazy,
aura couleur multi-contextes, aura mots power, phonk infographie, arc solidarité et collage ransom-note.
Les règles de Luca qui s'appliquent à tous sont dans `docs/da.md`.
