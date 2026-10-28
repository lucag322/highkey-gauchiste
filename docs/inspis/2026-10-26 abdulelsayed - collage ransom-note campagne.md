---
date: 2026-10-26
source: https://vm.tiktok.com/ZN8DgDK2k/
createur: "@abdulelsayed"
style: nouveau
son: original sound — Abdul El-Sayed
---
# abdulelsayed - collage ransom-note campagne
↑ [[Projets/highkey-gauchiste/inspis|inspis]]
- Note de Luca : « aucune, hypothèse »
- Ce que ça montre : candidat sénateur US, ton glorifiant, campagne progressiste — accumulation visuelle de slogans
## À recopier
- Texte ransom-note : chaque mot dans son propre rectangle légèrement penché, mix serif/sans-serif, tout en capitales
- Slogans qui s'accumulent carton par carton sur le fond (pas tout d'un coup, mot après mot)
- Photos N&B meetings/pancartes collées sur fond coloré uni comme un scrapbook
- Silhouette détourée en aplat blanc du candidat sur fond sombre
- Carton final propre (fond crème, typo bold bleu + rouge) qui contraste avec le chaos visuel du reste
## Recette avec nos outils
- Fond coloré uni + photos N&B posées avec rotation légère → compkit.py Merge, fx.py vignette + grain
- Accumulation mot/carton → b.anim() dans compkit.py, un node texte par mot qui apparaît à son timecode
- Texte ransom-note → cards.py avec polices différentes par mot, ou Fusion Text+ taille/font par token
- Silhouette détourée → segment binaire puis fill aplat blanc dans Fusion (Merge mode Normal)
- Recadrage 9:16 obligatoire (source 16:9) → framing.py sur chaque plan
## Mesures
- 16:9 source (1920×1080), 31,6 s, 8,6 coupes / 10 s global — pic 14,3 coupes / 10 s entre 7-14 s
- Coupes sur montée de voix, pas sur beat musical
- Couleurs : #C5D0E8 #4A2070 #1B3472 #FFFFFF #CC2030 #F2EDE0 #1B2B5C
## À ne pas recopier
- ⚠️ Flashs sub-frame : coupes à 40 ms (9.05 → 9.09, 10.89 → 10.93) = environ 1 image à 25 fps — Luca refuse les flashs 1-2 images
- Source 16:9 : ne jamais poster tel quel, toujours recadrer en 9:16 avec framing.py
- "NOT ENOUGH" très gros sans contour sur fond variable : tester lisibilité avant de copier
- Carton "VOTE NOV. 3" = logique campagne US, adapter en CTA FR si repris

![[Projets/highkey-gauchiste/inspis/images/2026-10-26-abdulelsayed/t2.6.jpg|240]] ![[Projets/highkey-gauchiste/inspis/images/2026-10-26-abdulelsayed/t13.2.jpg|240]]
