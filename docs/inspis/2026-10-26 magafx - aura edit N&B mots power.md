---
date: 2026-10-26
source: https://vm.tiktok.com/ZN8DVGEgL/
createur: "@.magafx"
style: aura N&B
son: original sound — MAGA FX (son original du créateur, pas de lien YouTube disponible)
---
# .magafx — aura edit N&B, overlays mots power

↑ [[Projets/highkey-gauchiste/inspis|inspis]]

- Note de Luca : « aucune, hypothèse »
- Ce que ça montre : edit aura ultra-rapide, figure politique glorifiée par mots power en N&B — structure "texte murmure → flash montage → fondu noir"

## À recopier

- Hook carte texte : fond quasi-blanc (#F5F5F5), 1 mot lowercase italique serif très fin (~16px équivalent), couleur #C8C8C8 — "murmure" volontaire, presque invisible
- Overlay mot power : 1 mot max 4 lettres, caps, fonte distressed bold #FFFFFF, centré à mi-hauteur — "BOSS", "GOAT"
- N&B intégral contraste élevé + grain filmique léger sur toute la vidéo
- Motion blur directionnel sur les coupes rapides (flou de mouvement entre plans)
- Fin en fondu noir total

## Recette avec nos outils

- Carte texte intro : `cards.text_cards` — fond #F5F5F5, texte #C8C8C8, lowercase, italic, taille minimale, 2 cartes × ~0,5 s
- Overlay mot power : `cards.text_cards` ou titre Fusion — fonte texturée/distressed, caps, 1 mot, blanc, durée 1-2 s sur le plan fort
- N&B + contraste : node étalonnage Resolve — désaturation totale + Lift/Gain pour booster le contraste
- Grain filmique : node Resolve `Film Grain` ou `fx.grain` si dispo
- Motion blur entre plans rapides : `fx.zoom_blur` ou Resolve Optical Flow en mode Speed Warp

## Mesures

- Format : 1:1 (1080×1080) — pas 9:16
- 18 s, 35,4 coupes / 10 s, clusters de flashs au début (0,05 → 0,13 s = 3 plans × ~30 ms), plan long vers 2,4-5,3 s (~3 s)
- Couleurs : #080808 #F0F0F0 (N&B pur, aucune couleur)
- Drop structurel vers 2,4 s (fin des cartes texte, début flash montage)

## À ne pas recopier

- Format 1:1 : nos formats sont 9:16
- Flashes < 2 images nombreux (plans de 30-50 ms) : Luca refuse
- Sujet de la vidéo (propagande MAGA) : données ignorées, style seul retenu

![[Projets/highkey-gauchiste/inspis/images/2026-10-26-magafx/t1.5.jpg|240]] ![[Projets/highkey-gauchiste/inspis/images/2026-10-26-magafx/t4.5.jpg|240]]
