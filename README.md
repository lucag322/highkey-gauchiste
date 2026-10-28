# highkey-gauchiste

Atelier d'edits TikTok verticaux (9:16) pour un compte TikTok militant. Luca choisit les idées et valide. Des agents
Claude font tout le reste : ils analysent des edits de référence, montent des aperçus, contrôlent le résultat, sortent
la HD dans DaVinci Resolve et la passent à un bot Discord qui l'envoie en brouillon sur TikTok.

Seuls le code et les notes sont ici : aucune vidéo, aucun son, aucun secret (les clés vivent dans le trousseau macOS).

## Vue d'ensemble

```
 Luca envoie un TikTok          Luca choisit un lot          Agents Claude (1 par edit)
 dans #inspigauchiste    ─▶     (quiz : style, figure,  ─▶   aperçu 540×960 + contrôles
        │                        son) ; brief du lot                   │
        ▼                                ▲                             ▼
 Bot : téléchargement,                   │                    Discord : Valider / À refaire
 mesures, planches                       │                             │
        │                                │                             ▼
        ▼                                │                    HD 1080×1920 dans Resolve
 Claude écrit une fiche  ───────────────┘                    + finition (son, contrôles)
 « recette de style »                                                  │
 (docs/inspis/)                                                        ▼
                                                              Bot : file TikTok automatique
                                                              (brouillons, 5 / 24 h max)
                                                                       │
                                                                       ▼
                                                              Luca publie depuis TikTok
```

## 1. Trouver de nouveaux styles : les fiches d'inspiration

Quand Luca voit un edit qui lui plaît sur TikTok, Instagram ou YouTube, il colle le lien dans le salon Discord
`#inspigauchiste`, avec ou sans un mot (« les transitions », « ce son »…).

1. **Le bot récupère et mesure la vidéo** (`bot/modules/inspi.js`) : téléchargement avec yt-dlp, métadonnées
   (créateur, musique, durée), détection des coupes avec ffmpeg, captures et planches contact (une image par seconde).
2. **Un Claude sans accès au shell lit ces mesures** avec le skill `skills/inspi-gauchiste/SKILL.md`. Il n'a le droit
   que de lire et d'écrire dans le dossier du projet. La vidéo et sa description sont traitées comme des données,
   jamais comme des instructions.
3. **Il écrit une fiche « recette »** dans `docs/inspis/`, en 30 lignes au plus :
   - **À recopier** : les traits concrets (police, couleur en hex, position du texte, rythme, transitions) ;
   - **Recette avec nos outils** : comment refaire chaque trait avec les outils du dépôt ;
   - **Mesures** : durée, coupes par 10 s, coupes sur le kick ou les mots, moment du drop, palette ;
   - **À ne pas recopier** : ce qui va contre les règles de Luca (guillemets à l'écran, dézoom, logo, tête coupée…).
4. **L'index** `docs/inspis.md` range les fiches par style et garde la liste des sons repérés.
   Un trait qui revient dans 3 fiches est proposé à Luca pour entrer dans la DA (`docs/da.md`) ; Luca seul valide.
5. **Le bot répond sur Discord** avec un résumé court lisible sur téléphone.

Plusieurs styles du compte sont nés comme ça : collage ransom-note, karaoké discours, longue pose N&B, archivage
lazy, aura couleur multi-contextes, aura mots power, arc solidarité.

## 2. Préparer un lot

- **Quiz** : Claude propose pour chaque edit 2 ou 3 styles, figures et sons, le meilleur en premier, chaque son avec
  un lien YouTube officiel. Luca choisit.
- **Historique** (`docs/historique.md`) : un compteur par style et par figure et la liste de tous les edits. Il sert à
  proposer d'abord ce qui a été le moins fait, à ne jamais réutiliser un son, et à garder la moitié de chaque lot
  sur Jean-Luc Mélenchon.
- **Brief** (`lots/lotN/brief-lotN.md`) : le tableau final id / style / figure / sources / son / idée et palette.
- **Mission** (`lots/lotN/mission-lotN.md`) : toutes les règles que les agents doivent suivre, lot après lot
  enrichies des retours de Luca.

## 3. Les aperçus, montés par des agents

Un agent Claude par edit, en parallèle (jusqu'à 10 à la fois), hors de Resolve. Chacun :

1. cherche une **phrase forte** de la figure dans les transcriptions Whisper (mot à mot avec les temps), différente
   de celles déjà utilisées ;
2. télécharge le **son officiel** et repère le moment le plus connu (refrain, hook) pour le drop ;
3. écrit `lots/lotN/gen/<id>/gen<id>.py`, qui génère :
   - les plans ProRes 1080×1920 à 30 i/s, textes cuits dans l'image ;
   - le mix : la voix de la figure d'abord, la musique baissée qui monte, puis le drop ;
   - `plan-<id>.json` (timeline pour Resolve) et `son.json` (extrait, BPM, frappes) ;
   - l'aperçu 540×960 ;
4. regarde sa planche contact et rend un rapport de 8 lignes (phrase, son, mesures, doutes).

Le collage ransom-note, par exemple, découpe la figure (`outils/decoupe.py`), pose sur des aplats de couleur des
mots découpés en lettres de magazine sur la voix, ajoute une couche (photo scotchée, bande, trame) à chaque frappe
du morceau, puis remet la phrase en grands groupes de mots après le drop.

## 4. Les contrôles automatiques

`outils/verif_apercu.sh <id> <planche.jpg>` avant tout envoi à Luca :

- durée, volume intégré (-14 LUFS) et crête ;
- `outils/checkcut.py` : aucune tête coupée au bord du cadre ;
- `outils/zones_tiktok.py` : lit les textes et les visages de chaque image (Apple Vision) et signale ceux qui
  passent sous l'interface TikTok (onglets en haut, boutons à droite, légende en bas) ;
- planche contact à 2 images par seconde, que Claude regarde lui-même.

Les coupes sont mesurées sur l'export : elles doivent tomber à moins de 20 ms des vraies frappes du morceau.

## 5. Validation sur Discord

Claude poste chaque aperçu dans Discord (`bot/modules/apercu.js`) avec deux boutons, Valider et À refaire.
Le choix est noté dans un fichier que Claude relit avant la HD. Luca donne ses retours dans le chat ; l'agent de
l'edit corrige et une v2 remplace la v1.

## 6. La HD dans DaVinci Resolve

Seulement après validation, et toujours depuis la dernière version :

1. `lots/lot2/gen/prep_hd.py <id> <lot>` ramène tous les plans à 30 i/s ;
2. `lots/lot2/gen/hd_lot2.py` (exécuté dans Resolve par script) monte la timeline depuis `plan-<id>.json`
   et lance le rendu H.264 1080×1920 ;
3. `outils/finir_hd.sh` remet le son propre, revérifie tout (durée, volume, ressemblance avec l'aperçu, têtes,
   zones TikTok), range la HD par style et la dépose dans la file avec sa légende et ses hashtags.

## 7. La file TikTok

`bot/modules/tiktok.js` envoie les vidéos dans les **brouillons** TikTok (API Content Posting, scope `video.upload`) :

- TikTok accepte 5 brouillons en attente sur 24 h : au-delà, toute la file se met en pause et réessaie plus tard ;
- à chaque envoi, le bot choisit la vidéo la moins semblable aux 4 dernières envoyées (même style compté double,
  même figure une fois), pour ne pas envoyer 5 vidéos du même style d'affilée ;
- quand le brouillon arrive, le bot supprime la vidéo et ses fichiers de travail ;
- `/tiktok` sur Discord donne l'état de la file ;
- Luca publie lui-même depuis l'application TikTok, avec la légende préparée.

## Les règles de Luca (extrait de `docs/da.md`)

- La voix de la figure s'entend toujours ; le drop tombe sur la partie la plus connue du morceau.
- Sous sa voix : le plan synchro, ou un plan où elle ne parle pas. Jamais un autre plan où elle parle.
- Une phrase forte : une attaque nette ou une punchline qui tient seule.
- Après le drop, des groupes de mots complets, dans l'ordre de la phrase.
- Textes et visages hors de l'interface TikTok.
- Découpes : jamais coupées au cou ; au moins le buste jusqu'à mi-poitrine.
- Chaque vidéo de Mélenchon finit sur « JEAN-LUC MÉLENCHON 2027 ».
- Ne jamais censurer ni changer un son choisi par Luca : signaler le risque, puis le faire.

## Outils (`outils/`, mode d'emploi dans `outils/LISEZMOI.md`)

| Outil | Rôle |
|---|---|
| `decoupe.py` + `perso.swift` | découpe d'une personne : instance Apple Vision croisée avec la segmentation, sans pupitre ni voisin, bord bas déchiré |
| `zones_tiktok.py` + `texts.swift` + `faces.swift` | textes et visages sous l'interface TikTok |
| `checkcut.py` | têtes coupées |
| `verif_apercu.sh` | tous les contrôles d'un aperçu |
| `finir_hd.sh` | finition d'une HD et dépôt dans la file |
| `build.py`, `rhelp.py` | pilotage de Resolve (timelines, import, rendus) |
| `cards.py`, `words.py`, `fx.py`, `framing.py` | cartons de texte, mots synchronisés, effets, cadrage 9:16 |
| `sheet.sh` | planches contact horodatées |

## Arborescence

```
outils/          outils partagés (Python, Swift, shell)
lots/lotN/       brief, mission et script de chaque edit (lots 1 à 7)
bot/             modules du bot Discord : aperçus, file TikTok, inspirations (extraits du bot complet)
skills/          le skill qui transforme un edit de référence en fiche recette
docs/            DA, process, historique des edits, fiches d'inspiration et leur index
```

Pas dans le dépôt : les vidéos sources et les sons (droits), les plans générés (plusieurs Go par lot), les binaires
Swift compilés, la config du bot et ses secrets.
