---
date: 2026-10-26
source: https://vm.tiktok.com/ZN8DVvV4v/
createur: "@jaxnotpl3"
style: nouveau
son: Gigi D'Agostino - L'Amour Toujours
---
# jaxnotpl3 - Macron aura couleur multi-contextes
↑ [[Projets/highkey-gauchiste/inspis|inspis]]
- Note de Luca : aucune, hypothèse
- Ce que ça montre : compilation de moments protocolaires de Macron (Davos, Élysée, Maison Blanche, Paris 2017), lunettes noires, rythme posé — aura couleur sans effet graphique

## À recopier
- Multi-contextes dans un même edit : Macron jeune + actuel + Davos + Maison Blanche = arc temporel qui donne du poids à la figure
- Plans lunettes placés sur le drop — marqueur visuel de "cool" sans texte
- Rythme posé (4,4 coupes / 10 s) pour un effet monumental, pas un montage frénétique
- Archives brutes variées (JT, événement officiel, conf de presse) sans caption artificielle ajoutée

## Recette avec nos outils
- Collecter 4-6 contextes différents du sujet (timeline large, jeune → actuel) — framing.py pour recadrer chaque plan en 9:16 sur le visage
- Couper toutes les 1,5-2 s sur les temps de la musique — détection beat manuelle dans Resolve ou words.py
- Placer le plan lunettes sur le drop de la musique (ici L'Amour Toujours drop vers 4-5 s)
- Couleur naturelle, pas de filtre lourd : correction expo légère dans Resolve sans LUT

## Mesures
- 1:1 carré (≠ notre 9:16), 20,3 s, 9 coupes, 4,4 coupes / 10 s, coupes régulières sur les temps
- Couleurs dominantes : #0D1117 #1B3A6B #F5F5F5 #C8102E

## À ne pas recopier
- Format carré 1:1 — nous faisons 9:16 exclusivement
- Durée 20,3 s dépasse légèrement la limite de 20 s
- Watermark "jxc" présent sur chaque plan

![[Projets/highkey-gauchiste/inspis/images/2026-10-26-jaxnotpl3/t1.7.jpg|240]] ![[Projets/highkey-gauchiste/inspis/images/2026-10-26-jaxnotpl3/t8.5.jpg|240]]
